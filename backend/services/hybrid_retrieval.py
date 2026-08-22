import os
import asyncio
import logging
import time
from typing import List, Dict, Any
from .vector_retrieval import vector_retriever
from .bm25_retrieval import bm25_retriever

logger = logging.getLogger(__name__)

RRF_K = int(os.getenv("RRF_K", "60"))
VECTOR_TOP_K = int(os.getenv("VECTOR_TOP_K", "20"))
BM25_TOP_K = int(os.getenv("BM25_TOP_K", "20"))
HYBRID_TOP_K = int(os.getenv("HYBRID_TOP_K", "5"))

async def hybrid_search(query: str, timings: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """
    Performs parallel search across Vector and BM25, then fuses results using RRF.
    Records sub-stage timings if a timings dictionary is provided.
    """
    if timings is None:
        timings = {}
        
    start_time = time.perf_counter()
    
    # Run in parallel using asyncio to simulate IO concurrency
    async def run_vector():
        s = time.perf_counter()
        res = await asyncio.to_thread(vector_retriever.search, query, VECTOR_TOP_K)
        timings["faiss_ms"] = (time.perf_counter() - s) * 1000
        return res
        
    async def run_bm25():
        s = time.perf_counter()
        res = await asyncio.to_thread(bm25_retriever.search, query, BM25_TOP_K)
        timings["bm25_ms"] = (time.perf_counter() - s) * 1000
        return res
    
    vector_results, bm25_results = await asyncio.gather(run_vector(), run_bm25())
    
    # Fusion
    rrf_s = time.perf_counter()
    fused_scores = {}
    chunk_data = {}
    
    # Process vector results
    for rank, res in enumerate(vector_results):
        cid = res["chunk_id"]
        chunk_data[cid] = res
        fused_scores[cid] = 1.0 / (RRF_K + rank + 1)
        
    # Process bm25 results
    for rank, res in enumerate(bm25_results):
        cid = res["chunk_id"]
        if cid in chunk_data:
            fused_scores[cid] += 1.0 / (RRF_K + rank + 1)
            if "bm25" not in chunk_data[cid]["retrieval_sources"]:
                chunk_data[cid]["retrieval_sources"].append("bm25")
        else:
            chunk_data[cid] = res
            fused_scores[cid] = 1.0 / (RRF_K + rank + 1)
            
    # Sort by RRF score
    sorted_chunks = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    
    final_results = []
    for cid, rrf_score in sorted_chunks[:HYBRID_TOP_K]:
        item = chunk_data[cid]
        # Replace the raw score with the hybrid RRF rank score for display
        item["score"] = rrf_score
        final_results.append(item)
        
    timings["rrf_ms"] = (time.perf_counter() - rrf_s) * 1000
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Hybrid retrieval completed in {elapsed:.4f}s. Found {len(final_results)} results.")
    
    return final_results
