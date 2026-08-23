import os
import logging
import time
from typing import List, Dict, Any
import requests

logger = logging.getLogger(__name__)

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))

class CrossEncoderRetriever:
    def __init__(self):
        self.model = None
        self.model_url = None
        self.is_ready = False
        
    def load(self):
        if self.is_ready:
            return
            
        try:
            self.model_url = f"https://router.huggingface.co/hf-inference/models/{RERANKER_MODEL}"
            self.is_ready = True
            logger.info("Reranker setup complete via HF Inference API")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder reranker: {e}")
            
    def score_and_sort(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.load()
        if not self.is_ready or not candidates:
            return []
            
        start_time = time.perf_counter()
        
        passages = [c["text"] for c in candidates]
        
        # Query HuggingFace API
        headers = {"Authorization": f"Bearer {os.environ.get('HF_TOKEN')}"}
        payload = {
            "inputs": {
                "source_sentence": query,
                "sentences": passages
            }
        }
        
        response = requests.post(self.model_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"HF API Reranker Error: {response.text}")
            # Fallback to original order
            return candidates[:RERANK_TOP_K]
            
        scores = response.json()
        
        # Add scores and sort
        scored_candidates = []
        for idx, score in enumerate(scores):
            candidates[idx]["reranker_score"] = float(score)
            scored_candidates.append(candidates[idx])
            
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
