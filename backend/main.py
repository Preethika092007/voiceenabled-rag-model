import os
import torch
# AGGRESSIVE MEMORY OPTIMIZATION FOR 512MB RAM:
# Limit PyTorch to 1 thread to prevent massive thread-pool memory allocation
torch.set_num_threads(1)
# Globally disable gradients since we only do inference
torch.set_grad_enabled(False)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="EchoRAG API",
    description="Backend API for EchoRAG Voice-enabled RAG System",
    version="1.0.0"
)

# Configure CORS
# For development, allow the Vite default port and potentially others based on env
origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Make port configurable
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
