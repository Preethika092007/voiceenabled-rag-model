import os
import json
import faiss
import logging
import time
import torch
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Config
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_DIR = os.path.join(DATA_DIR, "index")

FAISS_INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")
CHUNK_MAPPING_FILE = os.path.join(INDEX_DIR, "chunk_mapping.json")
INDEX_MANIFEST_FILE = os.path.join(INDEX_DIR, "index_manifest.json")

class VectorRetriever:
    def __init__(self):
        self.index = None
        self.mapping = None
        self.model = None
        self.is_ready = False
        
    def load(self):
        if self.is_ready:
            return
            
        if not os.path.exists(FAISS_INDEX_FILE) or not os.path.exists(CHUNK_MAPPING_FILE) or not os.path.exists(INDEX_MANIFEST_FILE):
            logger.warning("FAISS index files not found. Vector retrieval will be unavailable.")
            return
            
        try:
            with open(INDEX_MANIFEST_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                
            model_name = manifest.get("embedding_model", "all-MiniLM-L6-v2")
            logger.info(f"Loading embedding model: {model_name}...")
            self.model = SentenceTransformer(model_name, device="cpu")
            self.model.eval()
            
            logger.info("Loading FAISS index...")
            self.index = faiss.read_index(FAISS_INDEX_FILE)
            
            logger.info("Loading chunk mapping...")
            with open(CHUNK_MAPPING_FILE, "r", encoding="utf-8") as f:
                self.mapping = json.load(f)
                
            self.is_ready = True
            logger.info("Vector Retriever initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load Vector Retriever: {e}")
            
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        self.load()
        if not self.is_ready:
            return []
            
        start_time = time.perf_counter()
        
        # Encode query
        with torch.no_grad():
            query_embedding = self.model.encode([query], normalize_embeddings=True, convert_to_numpy=True)
        
        # Search
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1: # FAISS returns -1 if there are not enough results
                continue
            idx_str = str(idx)
            if idx_str in self.mapping:
                chunk = self.mapping[idx_str]
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "score": float(scores[0][i]),
                    "metadata": chunk,
                    "retrieval_sources": ["faiss"]
                })
                
        elapsed = time.perf_counter() - start_time
        logger.info(f"Vector search completed in {elapsed:.4f}s")
        return results

# Singleton instance
vector_retriever = VectorRetriever()
