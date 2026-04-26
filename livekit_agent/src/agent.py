import logging
import os
import asyncio
from typing import Any
from livekit import rtc
from livekit.agents import Agent, get_job_context, ChatContext, ChatMessage
from livekit.agents.llm import ImageContent
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    function_tool,
    RunContext,
    room_io,
)
from livekit.plugins import silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from datetime import datetime


logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self) -> None:
        #self.language: str = "zh"  # Default language is Chinese
        #self.voice: str = "zf_xiaobei"  # Default voice for Chinese
        self._latest_frame = None
        self._video_stream = None
        self._tasks = []
        super().__init__(
            instructions="""You are a helpful Chinese reading and app navigation tutor for a beginner Chinese language student. 
            The user is interacting with you via voice, even if you perceive the conversation as text, and via images of books, apps, and other visual content.
            When you receive an image, read the text in the image word-for-word out loud and provide a simple definition in Simplified Chinese for any advanced words.
            Whenever the user repeats a word or phrase that you already used, provide a short definition, short English translation in parentheses, and write the pinyin.
            If you don't understand what the user just said, then simply read the text from the next image out loud and provide a definition for any advanced words in Simplified Chinese.
            Do not include any dashes, asterisks, or HTML tags in your responses.""",
        )

    # @function_tool()
    # async def get_current_date_and_time(self, context: RunContext) -> str:
    #     """Get the current date and time."""
    #     return f"The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."    
    
    # @function_tool()
    # async def multiply_numbers(
    #     self,
    #     context: RunContext,
    #     number1: int,
    #     number2: int,
    # ) -> dict[str, Any]:
    #     """Multiply two numbers.
        
    #     Args:
    #         number1: The first number to multiply.
    #         number2: The second number to multiply.
    #     """

    #     return f"The product of {number1} and {number2} is {number1 * number2}."

    # @function_tool()
    # async def set_language(
    #     self,
    #     context: RunContext,
    #     language: str,
    # ) -> str:
    #     """Set the language for speech recognition (STT).
        
    #     Note: Text-to-speech (TTS) automatically detects language from text content and uses appropriate voices.
        
    #     Args:
    #         language: The language code to set for STT. Use "en" for English or "zh" for Chinese.
    #     """
    #     # Update the agent's language
    #     self.language = language
        
    #     # Update the STT language dynamically
    #     session = context.agent.session
    #     if session and hasattr(session, '_stt') and session._stt:
    #         stt = session._stt
    #         if hasattr(stt, 'update_options'):
    #             stt.update_options(language=language)
        
    #     language_name = "English" if language == "en" else "Chinese"
    #     return f"Speech recognition language set to {language_name} ({language}). TTS automatically detects language from text."

    async def on_enter(self):
            room = get_job_context().room

            # Find the first video track (if any) from the remote participant
            remote_participants = list(room.remote_participants.values())
            if remote_participants:
                remote_participant = remote_participants[0]
                video_tracks = [publication.track for publication in list(remote_participant.track_publications.values()) if publication.track.kind == rtc.TrackKind.KIND_VIDEO]
                if video_tracks:
                    self._create_video_stream(video_tracks[0])

            # Watch for new video tracks not yet published
            @room.on("track_subscribed")
            def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
                if track.kind == rtc.TrackKind.KIND_VIDEO:
                    self._create_video_stream(track)

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        # Add the latest video frame, if any, to the new message
        # Note: Only send images if your LLM model supports multimodal input
        # Qwen3-4B is text-only, so images are disabled for now
        if self._latest_frame and True:  # Set to True when using a vision-capable model
            new_message.content.append(ImageContent(image=self._latest_frame))
            self._latest_frame = None

    # Helper method to buffer the latest video frame from the user's track
    def _create_video_stream(self, track: rtc.Track):
        # Close any existing stream (we only want one at a time)
        if self._video_stream is not None:
            self._video_stream.close()

        # Create a new stream to receive frames
        self._video_stream = rtc.VideoStream(track)
        async def read_stream():
            async for event in self._video_stream:
                # Store the latest frame for use later
                self._latest_frame = event.frame

        # Store the async task
        task = asyncio.create_task(read_stream())
        task.add_done_callback(lambda t: self._tasks.remove(t))
        self._tasks.append(task)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    llama_model = os.getenv("LLAMA_MODEL", "qwen3-4b")
    llama_base_url = os.getenv("LLAMA_BASE_URL", "http://llama_cpp:11434/v1")

    stt_provider = os.getenv("STT_PROVIDER", "whisper").lower()
    default_stt_base_url = "http://whisper:80/v1"
    default_stt_model = "Systran/faster-whisper-large-v3"

    stt_base_url = os.getenv("STT_BASE_URL", default_stt_base_url)
    stt_model = os.getenv("STT_MODEL", default_stt_model)
    stt_api_key = os.getenv("STT_API_KEY", "no-key-needed")

    logger.info(
        "Starting agent with STT provider=%s model=%s base_url=%s",
        stt_provider,
        stt_model,
        stt_base_url,
    )

    session = AgentSession(
        stt=openai.STT(
            base_url=stt_base_url,
            # base_url="http://localhost:11435/v1", # uncomment for local testing
            model=stt_model,
            language="zh",  # Default language
            detect_language=False,  # Disable automatic detection, use the language variable
            api_key=stt_api_key
        ),
        llm=openai.LLM(
            base_url=llama_base_url,
            # base_url="http://localhost:11436/v1", # uncomment for local testing
            model=llama_model,
            api_key="no-key-needed"
        ),
        tts=openai.TTS(
            base_url="http://kokoro:8880/v1",
            # base_url="http://localhost:8880/v1", # uncomment for local testing
            model="kokoro",
            voice="zf_xiaobei",
            api_key="no-key-needed"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            video_input=True,
        ),
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
