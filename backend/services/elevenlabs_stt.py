import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

ELEVENLABS_API_URL = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1/speech-to-text")
ELEVENLABS_STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2")

async def transcribe_audio(audio_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
    """
    Sends audio to ElevenLabs STT (Scribe) and returns a structured dictionary.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    
    # Safe debug log without exposing the key
    logger.info(f"ELEVENLABS_API_KEY configured: {bool(api_key)}")
    
    if not api_key:
        return {
            "success": False,
            "status_code": 500,
            "message": "Speech-to-Text is not configured. Please add the required ElevenLabs API credentials.",
            "provider": "elevenlabs",
            "stage": "speech_to_text"
        }
    
    headers = {
        "xi-api-key": api_key,
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
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
            
            request_id = response.headers.get("request-id", "unknown")
            
            if response.status_code == 200:
                result = response.json()
                transcript = result.get("text")
                if not transcript:
                    return {
                        "success": False,
                        "status_code": 502,
                        "message": "Transcription failed: API returned an empty response.",
                        "provider": "elevenlabs",
                        "stage": "speech_to_text",
                        "request_id": request_id
                    }
                return {
                    "success": True,
                    "transcript": transcript,
                    "provider": "elevenlabs"
                }
            
            # Map upstream errors appropriately
            error_message = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict) and "detail" in error_json:
                    error_detail = error_json["detail"]
                    if isinstance(error_detail, dict) and "message" in error_detail:
                        error_message = error_detail["message"]
            except Exception:
                pass

            # Map quotas or auth issues
            if response.status_code == 401:
                human_message = "Invalid ElevenLabs API key or unauthorized."
            elif response.status_code == 403:
                human_message = "Permission denied or access restriction."
            elif response.status_code == 429:
                human_message = "ElevenLabs Speech-to-Text quota is unavailable or rate limit exceeded."
            elif response.status_code == 400 or response.status_code == 422:
                human_message = f"Invalid STT request: {error_message}"
            else:
                human_message = f"ElevenLabs provider error: {error_message}"

            return {
                "success": False,
                "status_code": response.status_code,
                "message": human_message,
                "provider": "elevenlabs",
                "stage": "speech_to_text",
                "request_id": request_id,
                "raw_response": response.text
            }
                
        except httpx.RequestError as e:
            return {
                "success": False,
                "status_code": 502,
                "message": "Network error occurred while connecting to the transcription provider.",
                "provider": "elevenlabs",
                "stage": "speech_to_text",
                "raw_response": str(e)
            }
