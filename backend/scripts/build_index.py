import os
import json
import faiss
import pickle
import logging
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Config
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
INDEX_DIR = os.path.join(DATA_DIR, "index")

CHUNKS_FILE = os.path.join(PROCESSED_DIR, "chunks.jsonl")
MANIFEST_FILE = os.path.join(PROCESSED_DIR, "manifest.json")

FAISS_INDEX_FILE = os.path.join(INDEX_DIR, "faiss.index")
BM25_INDEX_FILE = os.path.join(INDEX_DIR, "bm25.pkl")
CHUNK_MAPPING_FILE = os.path.join(INDEX_DIR, "chunk_mapping.json")
INDEX_MANIFEST_FILE = os.path.join(INDEX_DIR, "index_manifest.json")

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

def build_indices():
    logger.info("Starting index build process...")
    
    if not os.path.exists(CHUNKS_FILE) or not os.path.exists(MANIFEST_FILE):
        logger.error("Processed artifacts not found. Please run preprocessing first.")
        return
        
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        preprocessing_manifest = json.load(f)
        
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    # Load chunks
    chunks = []
    logger.info("Loading chunks from disk...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    if not chunks:
        logger.error("No chunks found to index.")
        return
        
    texts = [c["text"] for c in chunks]
    
    logger.info(f"Loaded {len(chunks)} chunks.")
    
    # --- 1. Build BM25 Index ---
    logger.info("Building BM25 Index...")
    # Simple whitespace tokenization; in production, use a better tokenizer if multilingual
    tokenized_corpus = [doc.lower().split() for doc in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    with open(BM25_INDEX_FILE, "wb") as f:
        pickle.dump(bm25, f)
    logger.info("BM25 Index saved.")
    
    # --- 2. Build FAISS Index ---
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embedding_dim = model.get_sentence_embedding_dimension()
    
    # We use Inner Product (cosine similarity since we normalize)
    index = faiss.IndexFlatIP(embedding_dim)
    
    logger.info("Generating embeddings in batches...")
    all_embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        # Encode and normalize for cosine similarity
        batch_embeddings = model.encode(batch_texts, normalize_embeddings=True, convert_to_numpy=True)
        index.add(batch_embeddings)
        all_embeddings.append(batch_embeddings)
        if (i + BATCH_SIZE) % (BATCH_SIZE * 10) == 0:
            logger.info(f"Embedded {i + BATCH_SIZE} / {len(texts)} chunks...")
            
    faiss.write_index(index, FAISS_INDEX_FILE)
    logger.info("FAISS Index saved.")
    
    # --- 3. Save mapping ---
    mapping = {}
    for i, chunk in enumerate(chunks):
        mapping[str(i)] = chunk
        
    with open(CHUNK_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False)
    logger.info("Chunk mapping saved.")
    
    # --- 4. Generate Manifest ---
    manifest = {
        "dataset_name": preprocessing_manifest.get("dataset_name"),
        "dataset_config": preprocessing_manifest.get("dataset_config"),
        "dataset_split": preprocessing_manifest.get("dataset_split"),
        "preprocessing_timestamp": preprocessing_manifest.get("processing_timestamp"),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_dimension": embedding_dim,
        "faiss_index_type": "IndexFlatIP",
        "indexed_chunks": len(chunks),
        "build_timestamp": datetime.utcnow().isoformat() + "Z",
        "batch_size": BATCH_SIZE,
        "sample_mode": preprocessing_manifest.get("sample_mode"),
        "sample_size": preprocessing_manifest.get("sample_size")
    }
    
    with open(INDEX_MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    logger.info("Index build complete!")
    logger.info(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    build_indices()
