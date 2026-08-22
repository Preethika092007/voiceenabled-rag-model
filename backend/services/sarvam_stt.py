import os
import httpx
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

SARVAM_API_URL = os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/speech-to-text-translate")
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v1")
SARVAM_STT_LANGUAGE = os.getenv("SARVAM_STT_LANGUAGE", "en") # Might not be strictly needed for translate, but good to have

async def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> Tuple[bool, str]:
    """
    Sends audio to Sarvam STT and returns (success, transcript_or_error_message).
    Implements a simple retry mechanism for transient errors.
    """
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        return False, "Speech-to-Text is not configured. Please add the required Sarvam API credentials."
    
    headers = {
        "api-subscription-key": api_key,
    }
    
    # We use httpx async client for non-blocking I/O
    async with httpx.AsyncClient(timeout=30.0) as client:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # The API typically accepts multipart/form-data with the 'file' field.
                files = {
                    "file": (filename, audio_bytes, content_type)
                }
                
                # Optional parameters depending on API version, like prompt or model
                data = {
                    "model": SARVAM_STT_MODEL
                }

                response = await client.post(
                    SARVAM_API_URL,
                    headers=headers,
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get("transcript") or result.get("text")
                    if not transcript:
                        return False, "Transcription failed: API returned an empty response."
                    return True, transcript
                
                elif response.status_code in [400, 401, 403]:
                    # Do not retry on client errors
                    return False, f"Sarvam API configuration or validation error: {response.status_code}"
                
                elif response.status_code >= 500:
                    # Retry on server errors
                    if attempt < max_retries - 1:
                        continue
                    return False, "Sarvam Speech-to-Text provider is currently unavailable."
                    
            except httpx.RequestError as e:
                logger.error(f"Request error connecting to Sarvam: {e}")
                if attempt < max_retries - 1:
                    continue
                return False, "Network error occurred while connecting to the transcription provider."
                
        return False, "Transcription failed after multiple attempts."
