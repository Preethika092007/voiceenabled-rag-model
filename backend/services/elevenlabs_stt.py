import os
import httpx
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

ELEVENLABS_API_URL = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1/speech-to-text")
ELEVENLABS_STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2")

async def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> Tuple[bool, str]:
    """
    Sends audio to ElevenLabs STT (Scribe) and returns (success, transcript_or_error_message).
    Implements a simple retry mechanism for transient errors.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return False, "Speech-to-Text is not configured. Please add the required ElevenLabs API credentials (ELEVENLABS_API_KEY) in your .env file."
    
    headers = {
        "xi-api-key": api_key,
    }
    
    # We use httpx async client for non-blocking I/O
    async with httpx.AsyncClient(timeout=45.0) as client:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                files = {
                    "file": (filename, audio_bytes, content_type)
                }
                
                data = {
                    "model_id": ELEVENLABS_STT_MODEL
                }

                response = await client.post(
                    ELEVENLABS_API_URL,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get("text")
                    if not transcript:
                        return False, "Transcription failed: API returned an empty response."
                    return True, transcript
                
                elif response.status_code in [400, 401, 403, 422]:
                    # Do not retry on client errors
                    return False, f"ElevenLabs API error: {response.status_code} - {response.text}"
                
                elif response.status_code >= 500:
                    # Retry on server errors
                    if attempt < max_retries - 1:
                        continue
                    return False, "ElevenLabs Speech-to-Text provider is currently unavailable."
                    
            except httpx.RequestError as e:
                logger.error(f"Request error connecting to ElevenLabs: {e}")
                if attempt < max_retries - 1:
                    continue
                return False, "Network error occurred while connecting to the transcription provider."
                
        return False, "Transcription failed after multiple attempts."
