import os
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import ValidationError
from .models import HealthResponse, TextQueryRequest, TextQueryResponse, VoiceQueryResponse, DatasetStatusResponse
from services.elevenlabs_stt import transcribe_audio
from services.vector_retrieval import vector_retriever
from services.bm25_retrieval import bm25_retriever
from services.reranker import reranker
from services.orchestration import run_query_pipeline

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    # Index files are now committed to git to prevent OOM spikes on Render
    # Removed eager loading: models will now load lazily on first request
    # to prevent OOM on Render 512MB free tier during deployment binding.
    pass

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

@router.get("/memory-audit")
async def memory_audit():
    """Diagnostic endpoint to measure incremental RAM usage."""
    import psutil
    process = psutil.Process(os.getpid())
    
    def get_mem():
        return f"{process.memory_info().rss / 1024 / 1024:.2f} MB"
        
    audit_results = {
        "1_startup_baseline": get_mem()
    }
    
    try:
        bm25_retriever.load()
        audit_results["2_after_bm25_load"] = get_mem()
        
        vector_retriever.load()
        audit_results["3_after_faiss_and_embedder_load"] = get_mem()
        
        reranker.load()
        audit_results["4_after_cross_encoder_load"] = get_mem()
        
        audit_results["5_final_idle_memory"] = get_mem()
        audit_results["status"] = "success"
    except Exception as e:
        audit_results["error"] = str(e)
        audit_results["status"] = "failed"
        
    return audit_results

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
            detail={"error": "INVALID_AUDIO", "message": "No audio file provided."}
        )
        
    # Read a chunk to verify it's not empty and get size
    content = await audio.read()
    file_size = len(content)
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_AUDIO", "message": "The uploaded audio file is empty."}
        )
        
    # Browser recordings produce formats like audio/webm, audio/ogg, audio/mp4
    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={"error": "UNSUPPORTED_MEDIA_TYPE", "message": f"Unsupported file format: {audio.content_type}. Please upload an audio file."}
        )
        
    # Send to ElevenLabs STT
    result = await transcribe_audio(content, audio.filename or "recording.webm", audio.content_type or "audio/webm")
    
    if not result.get("success"):
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # Log SAFE structured error as requested
        safe_log = {
            "provider": result.get("provider"),
            "stage": result.get("stage"),
            "upstream_status": result.get("status_code"),
            "message": result.get("message"),
            "request_id": result.get("request_id")
        }
        logger.error(json.dumps(safe_log))
        
        # Raise HTTP exception with mapped status code
        status_code = result.get("status_code", 502)
        
        # For quota exceeded, explicitly use 429 to be accurate, but 502 is also okay for upstream proxy.
        # We will use exactly what ElevenLabs returned, or 500/502.
        
        error_code = "STT_PROVIDER_ERROR"
        if status_code == 429:
            error_code = "STT_QUOTA_EXCEEDED"
            
        raise HTTPException(
            status_code=status_code,
            detail={"error": error_code, "message": result.get("message")}
        )

    return VoiceQueryResponse(
        status="success",
        message="Audio transcribed successfully",
        transcript=result.get("transcript"),
        content_type=audio.content_type,
        file_size=file_size,
        filename=audio.filename
    )
