#!/usr/bin/env python3
"""
Kokoro-82M FastAPI server with OpenAI TTS compatibility.
Supports both English and Mandarin Chinese voices.
"""

import io
import logging
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from kokoro import KPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kokoro TTS Server", version="1.0.0")

# Global pipeline cache
_pipelines = {}

def get_pipeline(lang_code: str) -> KPipeline:
    """Get or create a KPipeline for the specified language."""
    if lang_code not in _pipelines:
        try:
            logger.info(f"Loading Kokoro pipeline for language: {lang_code}")
            _pipelines[lang_code] = KPipeline(lang_code=lang_code)
        except Exception as e:
            logger.error(f"Failed to load pipeline for {lang_code}: {e}")
            raise
    return _pipelines[lang_code]

def detect_language_from_voice(voice: str) -> str:
    """Detect language from voice name.
    
    Voice naming convention:
    - af_*, am_*, bf_*, bm_* => English (a=US, b=UK)
    - zf_*, zm_* => Mandarin Chinese
    - jf_*, jm_* => Japanese
    - ef_*, em_* => Spanish
    - ff_* => French
    - hf_*, hm_* => Hindi
    - if_*, im_* => Italian
    - pf_*, pm_* => Portuguese
    """
    prefix = voice[:2]
    
    language_map = {
        'af': 'a',  # US English female
        'am': 'a',  # US English male
        'bf': 'b',  # UK English female
        'bm': 'b',  # UK English male
        'zf': 'z',  # Mandarin female
        'zm': 'z',  # Mandarin male
        'jf': 'j',  # Japanese female
        'jm': 'j',  # Japanese male
        'ef': 'e',  # Spanish female
        'em': 'e',  # Spanish male
        'ff': 'f',  # French female
        'hf': 'h',  # Hindi female
        'hm': 'h',  # Hindi male
        'if': 'i',  # Italian female
        'im': 'i',  # Italian male
        'pf': 'p',  # Portuguese female
        'pm': 'p',  # Portuguese male
    }
    
    return language_map.get(prefix, 'a')  # Default to English

class TTSRequest(BaseModel):
    """OpenAI-compatible TTS request."""
    input: str
    model: str = "kokoro"
    voice: str = "af_heart"
    response_format: str = "mp3"
    speed: float = 1.0

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "kokoro",
                "object": "model",
                "owned_by": "hexgrad"
            }
        ]
    }

@app.post("/v1/audio/speech")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Kokoro-82M.
    OpenAI-compatible endpoint.
    """
    try:
        if not request.input or not request.input.strip():
            raise HTTPException(status_code=400, detail="Input text cannot be empty")
        
        # Detect language from voice
        lang_code = detect_language_from_voice(request.voice)
        logger.info(f"TTS: voice={request.voice}, lang={lang_code}, input_len={len(request.input)}")
        
        # Get pipeline for detected language
        pipeline = get_pipeline(lang_code)
        
        # Generate speech - concatenate all chunks
        audio_chunks = []
        for i, (graphemes, phonemes, audio) in enumerate(
            pipeline(request.input, voice=request.voice, speed=request.speed)
        ):
            logger.debug(f"Generated chunk {i}: graphemes={graphemes}, phonemes={phonemes}")
            audio_chunks.append(audio)
        
        if not audio_chunks:
            return StreamingResponse(
                io.BytesIO(b""),
                media_type="audio/wav"
            )
        
        # Concatenate all audio chunks
        import numpy as np
        full_audio = np.concatenate(audio_chunks)
        
        # Convert to WAV format first, then to MP3
        import soundfile as sf
        from pydub import AudioSegment
        import io
        
        # Write to WAV buffer
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, full_audio, 24000, format='WAV')
        wav_buffer.seek(0)
        
        # Convert WAV to MP3 using pydub
        audio_segment = AudioSegment.from_wav(wav_buffer)
        mp3_buffer = io.BytesIO()
        audio_segment.export(mp3_buffer, format='mp3')
        mp3_buffer.seek(0)
        
        return StreamingResponse(
            mp3_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """Placeholder for potential future chat integration."""
    raise HTTPException(status_code=501, detail="Not implemented")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8880, log_level="info")
