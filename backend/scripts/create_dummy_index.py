import os
import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
# pyrefly: ignore [missing-import]
from rank_bm25 import BM25Okapi

def create_dummy_index():
    print("Creating local dummy index...")
    index_dir = os.path.join(os.path.dirname(__file__), "..", "data", "index")
    os.makedirs(index_dir, exist_ok=True)
    
    # Dummy MSMARCO data
    passages = [
        {"id": "0", "text": "The normal resting heart rate for adults ranges from 60 to 100 beats per minute."},
        {"id": "1", "text": "A physician assistant (PA) is a mid-level medical practitioner who works under the supervision of a licensed doctor."},
        {"id": "2", "text": "A corporation is an organization usually a group of people or a company authorized by the state to act as a single entity."},
        {"id": "3", "text": "The typical real estate agent commission is between 5% and 6% of the home's sale price."},
        {"id": "4", "text": "Alaska is the largest state in the United States by total area."}
    ]
    
    print("Generating embeddings (this may take a few seconds)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode([p["text"] for p in passages])
    
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    faiss.write_index(index, os.path.join(index_dir, "faiss.index"))
    
    print("Building BM25 index...")
    tokenized_corpus = [p["text"].lower().split() for p in passages]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(os.path.join(index_dir, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
        
    print("Writing chunk mapping...")
    # chunk_mapping.json format: dict with str keys mapping to dicts
    chunk_mapping = {str(i): {"chunk_id": str(i), "text": p["text"], "parent_id": p["id"]} for i, p in enumerate(passages)}
    with open(os.path.join(index_dir, "chunk_mapping.json"), "w", encoding="utf-8") as f:
        json.dump(chunk_mapping, f, indent=2)

    print("Writing index manifest...")
    manifest = {
        "num_chunks": len(passages),
        "embedding_model": "all-MiniLM-L6-v2",
        "vector_dimension": dimension
    }
    with open(os.path.join(index_dir, "index_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print("Dummy index successfully created!")

if __name__ == "__main__":
    create_dummy_index()
