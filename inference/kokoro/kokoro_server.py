#!/usr/bin/env python3
"""
Kokoro-82M FastAPI server with OpenAI TTS compatibility.
Supports both English and Mandarin Chinese voices.
"""

import os
import io
import logging
from typing import Optional
import sys

# Set HuggingFace cache environment variables before importing kokoro
os.environ.setdefault('HF_HOME', '/root/.cache/huggingface')
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

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
            # Use default repo_id but rely on offline mode and local cache
            _pipelines[lang_code] = KPipeline(lang_code=lang_code)
        except Exception as e:
            logger.error(f"Failed to load pipeline for {lang_code}: {e}")
            raise
    return _pipelines[lang_code]

def detect_language_from_text(text: str) -> str:
    """Detect language from text content using simple heuristics."""
    # Chinese character ranges
    chinese_chars = 0
    total_chars = 0
    
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            chinese_chars += 1
        if char.isalnum():  # Count alphanumeric characters
            total_chars += 1
    
    # If more than 30% of alphanumeric characters are Chinese, consider it Chinese
    if total_chars > 0 and (chinese_chars / total_chars) > 0.3:
        return 'z'
    return 'a'

def get_voice_for_language(language: str, current_voice: str = None) -> str:
    """Get appropriate voice for the detected language."""
    if language == 'z':
        # Use Chinese voice if current voice is not already Chinese
        if current_voice and current_voice.startswith('z'):
            return current_voice
        return 'zf_xiaobei'  # Default Chinese voice
    else:
        # Use English voice if current voice is not already English
        if current_voice and (current_voice.startswith('a') or current_voice.startswith('b')):
            return current_voice
        return 'af_heart'  # Default English voice

class TTSRequest(BaseModel):
    """OpenAI-compatible TTS request."""
    input: str
    model: str = "kokoro"
    voice: str = "zf_xiaobei"  # Default voice, can be overridden by language detection
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
        
        # Detect language from text content
        detected_language = detect_language_from_text(request.input)
        
        # Choose appropriate voice based on detected language
        voice_to_use = get_voice_for_language(detected_language, request.voice)
        
        # Detect language from voice (for pipeline selection)
        #lang_code = detect_language_from_text(voice_to_use)
        lang_code = 'z' if voice_to_use.startswith('z') else 'a'
        logger.info(f"TTS: input_lang={detected_language}, voice={voice_to_use}, pipeline_lang={lang_code}, input_len={len(request.input)}")
        
        # Get pipeline for detected language
        pipeline = get_pipeline(lang_code)
        
        # Generate speech - concatenate all chunks
        audio_chunks = []
        for i, (graphemes, phonemes, audio) in enumerate(
            pipeline(request.input, voice=voice_to_use, speed=request.speed)
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
