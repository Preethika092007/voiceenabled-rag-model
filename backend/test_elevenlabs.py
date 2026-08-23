import os
import asyncio
import httpx

def load_env():
    try:
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v
    except Exception:
        pass

load_env()

async def test_elevenlabs():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    print(f"ELEVENLABS_API_KEY configured: {bool(api_key)}")
    
    # Create a tiny valid dummy WAV file in memory (44-byte RIFF header + minimal data)
    import struct
    # 1 channel, 8000 Hz, 8 bit, 1 sample
    dummy_wav = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36, b'WAVE', b'fmt ', 16, 1, 1, 8000, 8000, 1, 8, b'data', 0)
    
    headers = {
        "xi-api-key": api_key,
    }
    
    files = {
        "file": ("test.wav", dummy_wav, "audio/wav")
    }
    data = {
        "model_id": "scribe_v2"
    }
    
    print("Sending request to ElevenLabs...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers=headers,
            files=files,
            data=data
        )
        print(f"Upstream Status: {response.status_code}")
        print(f"Upstream Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_elevenlabs())
