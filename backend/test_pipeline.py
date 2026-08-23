import httpx
import asyncio
from gtts import gTTS
import json

async def run_test():
    print("Generating speech audio...")
    tts = gTTS("What are the advantages of Reciprocal Rank Fusion?", lang='en')
    tts.save("test_query.mp3")
    
    print("Sending POST request to /voice-query...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open("test_query.mp3", "rb") as f:
            audio_bytes = f.read()
            
        files = {
            "audio": ("test_query.mp3", audio_bytes, "audio/mpeg")
        }
        
        response = await client.post("http://localhost:8000/voice-query", files=files)
        
        print(f"Status: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response (raw): {response.text}")

if __name__ == "__main__":
    asyncio.run(run_test())
