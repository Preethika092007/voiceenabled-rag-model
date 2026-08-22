import os
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import ValidationError
from .models import HealthResponse, TextQueryRequest, TextQueryResponse, VoiceQueryResponse, DatasetStatusResponse
from services.sarvam_stt import transcribe_audio
from services.vector_retrieval import vector_retriever
from services.bm25_retrieval import bm25_retriever
from services.reranker import reranker
from services.orchestration import run_query_pipeline

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    # Load indices asynchronously or in background thread, but for simplicity, load directly
    vector_retriever.load()
    bm25_retriever.load()
    reranker.load()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running and available."""
    return HealthResponse(
        status="healthy",
        service="EchoRAG API",
        version="1.0.0"
    )

@router.get("/dataset-status", response_model=DatasetStatusResponse)
async def dataset_status():
    """Check if the offline MSMARCO preprocessing has completed."""
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "manifest.json")
    if os.path.exists(manifest_path):
        if vector_retriever.is_ready and bm25_retriever.is_ready:
            return DatasetStatusResponse(status="ready", message="Knowledge Base & Indices Ready")
        else:
            # Try to load them if not loaded
            vector_retriever.load()
            bm25_retriever.load()
            if vector_retriever.is_ready and bm25_retriever.is_ready:
                return DatasetStatusResponse(status="ready", message="Knowledge Base & Indices Ready")
            return DatasetStatusResponse(status="not_prepared", message="Knowledge Base Prepared, but Indices missing.")
    return DatasetStatusResponse(status="not_prepared", message="Knowledge Base Not Prepared")

@router.get("/benchmark-results")
async def get_benchmark_results():
    """Retrieve the latest latency benchmark results."""
    results_path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "not_found", "message": "No benchmark results available yet."}

@router.post("/query", response_model=TextQueryResponse)
async def submit_query(request: TextQueryRequest):
    """Submit a text query and perform the complete RAG pipeline."""
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty or just whitespace."
        )
        
    if not vector_retriever.is_ready or not bm25_retriever.is_ready:
        return TextQueryResponse(
            status="error",
            query=request.query,
            message="Knowledge base index is not ready. Run the embedding/index build process first.",
            results=[]
        )
        
    # Perform full pipeline
    try:
        pipeline_result = await run_query_pipeline(request.query)
        
        return TextQueryResponse(
            **pipeline_result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@router.post("/voice-query", response_model=VoiceQueryResponse)
async def submit_voice_query(audio: UploadFile = File(...)):
    """Upload an audio file for Speech-to-Text processing."""
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file provided."
        )
        
    # Read a chunk to verify it's not empty and get size
    content = await audio.read()
    file_size = len(content)
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is empty."
        )
        
    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format: {audio.content_type}. Please upload an audio file."
        )
        
    # Send to Sarvam STT
    success, result = await transcribe_audio(content, audio.filename or "recording.webm", audio.content_type or "audio/webm")
    
    if not success:
        # Returning a 200 with an error message so frontend can display it cleanly without throwing an unhandled rejection,
        # but the spec asks for structured response. Let's return 400 with detail.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    return VoiceQueryResponse(
        status="success",
        message="Audio transcribed successfully",
        transcript=result,
        content_type=audio.content_type,
        file_size=file_size,
        filename=audio.filename
    )
