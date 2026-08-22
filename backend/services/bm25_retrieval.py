import os
import json
import pickle
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Config
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_DIR = os.path.join(DATA_DIR, "index")

BM25_INDEX_FILE = os.path.join(INDEX_DIR, "bm25.pkl")
CHUNK_MAPPING_FILE = os.path.join(INDEX_DIR, "chunk_mapping.json")

class BM25Retriever:
    def __init__(self):
        self.bm25 = None
        self.mapping = None
        self.is_ready = False
        
    def load(self):
        if self.is_ready:
            return
            
        if not os.path.exists(BM25_INDEX_FILE) or not os.path.exists(CHUNK_MAPPING_FILE):
            logger.warning("BM25 index files not found. Keyword retrieval will be unavailable.")
            return
            
        try:
            logger.info("Loading BM25 index...")
            with open(BM25_INDEX_FILE, "rb") as f:
                self.bm25 = pickle.load(f)
                
            logger.info("Loading chunk mapping...")
            with open(CHUNK_MAPPING_FILE, "r", encoding="utf-8") as f:
                self.mapping = json.load(f)
                
            self.is_ready = True
            logger.info("BM25 Retriever initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load BM25 Retriever: {e}")
            
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.is_ready:
            return []
            
        start_time = time.perf_counter()
        
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            score = scores[idx]
            if score <= 0:
                continue # Skip zero-score documents
                
            idx_str = str(idx)
            if idx_str in self.mapping:
                chunk = self.mapping[idx_str]
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "score": float(score),
                    "metadata": chunk,
                    "retrieval_sources": ["bm25"]
                })
                
        elapsed = time.perf_counter() - start_time
        logger.info(f"BM25 search completed in {elapsed:.4f}s")
        return results

# Singleton instance
bm25_retriever = BM25Retriever()
