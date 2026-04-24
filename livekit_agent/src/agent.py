import logging
import os
from typing import Any

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
)
from livekit.plugins import silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from datetime import datetime

logger = logging.getLogger("agent")

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self) -> None:
        self.language: str = "zh"  # Default language is Chinese
        self.voice: str = "zf_xiaobei"  # Default voice for Chinese
        super().__init__(
            instructions="""You are a helpful voice AI Chinese tutor. The user is interacting with you via voice, even if you perceive the conversation as text.
            You are teaching a beginner Chinese language student (who speaks English natively) to speak and understand Chinese.  
            Always respond in Chinese, even if the user speaks to you in English, unless the user explicitly asks you to switch to English.
            Only use simple Chinese phrases and don't say more than 3 sentences in a row before pausing and asking whether the user is ready to continue.
            Provide a short definition, short English translation, and write the pinyin whenever the user repeats a word or phrase that you already used.
            You are friendly and have a sense of humor.""",
        )

    @function_tool()
    async def get_current_date_and_time(self, context: RunContext) -> str:
        """Get the current date and time."""
        return f"The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."    
    
    @function_tool()
    async def multiply_numbers(
        self,
        context: RunContext,
        number1: int,
        number2: int,
    ) -> dict[str, Any]:
        """Multiply two numbers.
        
        Args:
            number1: The first number to multiply.
            number2: The second number to multiply.
        """

        return f"The product of {number1} and {number2} is {number1 * number2}."

    @function_tool()
    async def set_language(
        self,
        context: RunContext,
        language: str,
    ) -> str:
        """Set the language for speech recognition (STT).
        
        Note: Text-to-speech (TTS) automatically detects language from text content and uses appropriate voices.
        
        Args:
            language: The language code to set for STT. Use "en" for English or "zh" for Chinese.
        """
        # Update the agent's language
        self.language = language
        
        # Update the STT language dynamically
        session = context.agent.session
        if session and hasattr(session, '_stt') and session._stt:
            stt = session._stt
            if hasattr(stt, 'update_options'):
                stt.update_options(language=language)
        
        language_name = "English" if language == "en" else "Chinese"
        return f"Speech recognition language set to {language_name} ({language}). TTS automatically detects language from text."

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
    )

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
