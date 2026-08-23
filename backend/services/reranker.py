import os
import logging
import time
import torch
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))

class CrossEncoderRetriever:
    def __init__(self):
        self.model = None
        self.is_ready = False
        
    def load(self):
        if self.is_ready:
            return
            
        try:
            import gc
            gc.collect() # Force garbage collection before loading heavy model
            logger.info(f"Loading CrossEncoder reranker: {RERANKER_MODEL}...")
            self.model = CrossEncoder(RERANKER_MODEL, device="cpu")
            self.model.model.eval()
            self.is_ready = True
            logger.info("CrossEncoder loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder reranker: {e}")
            
    def score_and_sort(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.load()
        if not self.is_ready or not candidates:
            return []
            
        start_time = time.perf_counter()
        
        # Create (query, text) pairs
        pairs = [[query, c["text"]] for c in candidates]
        
        # Predict scores
        with torch.no_grad():
            scores = self.model.predict(pairs)
        
        # Attach scores and sort
        scored_candidates = []
        for i, candidate in enumerate(candidates):
            candidate["reranker_score"] = float(scores[i])
            scored_candidates.append(candidate)
            
        # Sort by reranker score descending
        sorted_candidates = sorted(scored_candidates, key=lambda x: x["reranker_score"], reverse=True)
        
        # Truncate to top_k and attach final rank
        final_results = []
        for rank, candidate in enumerate(sorted_candidates[:RERANK_TOP_K]):
            candidate["final_rank"] = rank + 1
            final_results.append(candidate)
            
        elapsed = time.perf_counter() - start_time
        logger.info(f"Reranking completed in {elapsed:.4f}s. Returned {len(final_results)} top chunks.")
        
        return final_results

# Singleton
reranker = CrossEncoderRetriever()
