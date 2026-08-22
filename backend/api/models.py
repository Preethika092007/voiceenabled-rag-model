from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class DatasetStatusResponse(BaseModel):
    status: str
    message: str

class TextQueryRequest(BaseModel):
    query: str = Field(..., description="The user's text question", min_length=1, max_length=1000)

class RetrievalResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = {}
    retrieval_sources: List[str] = []
    reranker_score: Optional[float] = None
    final_rank: Optional[int] = None

class SourceInfo(BaseModel):
    chunk_id: str
    rank: int

class TextQueryResponse(BaseModel):
    status: str
    query: str
    message: Optional[str] = None
    answer: Optional[str] = None
    results: List[RetrievalResult] = []
    sources: List[SourceInfo] = []
    pipeline: Dict[str, str] = {}
    timings: Dict[str, float] = {}
    reason: Optional[str] = None

class VoiceQueryResponse(BaseModel):
    status: str
    message: str
    transcript: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    filename: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
