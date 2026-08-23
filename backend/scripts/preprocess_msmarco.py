import os
import json
import logging
import hashlib
from datetime import datetime
# pyrefly: ignore [missing-import]
from datasets import load_dataset
from typing import List, Dict, Any

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants and Configuration
DATASET_NAME = os.getenv("DATASET_NAME", "ai4bharat/MSMARCO-XI")
DATASET_CONFIG = os.getenv("DATASET_CONFIG", "default")
DATASET_SPLIT = os.getenv("DATASET_SPLIT", "train")
PREPROCESS_SAMPLE_SIZE = os.getenv("PREPROCESS_SAMPLE_SIZE", None)

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "chunks.jsonl")
MANIFEST_FILE = os.path.join(OUTPUT_DIR, "manifest.json")


def clean_text(text: str) -> str:
    """Normalizes whitespace without removing meaningful punctuation."""
    if not text:
        return ""
    # Replace multiple spaces with a single space
    text = " ".join(text.split())
    return text


def split_by_semantic_boundaries(text: str) -> List[str]:
    """Strategy 1: Attempt to split text by paragraphs or sentences."""
    if not text:
        return []
    
    # Try splitting by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if len(paragraphs) > 1:
        return paragraphs
        
    # If no paragraphs, try splitting by sentences roughly
    sentences = [s.strip() + "." for s in text.split('. ') if s.strip()]
    if not sentences:
        return [text]
    
    # Reconstruct small blocks so we don't end up with tiny chunks
    blocks = []
    current_block = ""
    for s in sentences:
        if len(current_block) + len(s) < CHUNK_SIZE:
            current_block += s + " "
        else:
            if current_block:
                blocks.append(current_block.strip())
            current_block = s + " "
    if current_block:
        blocks.append(current_block.strip())
        
    return blocks if blocks else [text]


def overlap_chunking(text: str, size: int, overlap: int) -> List[str]:
    """Strategy 2: Fixed size chunking with overlap for very long texts."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (size - overlap)
    return chunks


def adaptive_chunking(text: str) -> List[Dict[str, Any]]:
    """Strategy 4: Selects chunking behavior based on content."""
    text = clean_text(text)
    if not text:
        return []

    # Short text: Single chunk
    if len(text) <= CHUNK_SIZE:
        return [{"text": text, "strategy": "single_chunk"}]
        
    # Medium/Long text: Try semantic split first
    semantic_blocks = split_by_semantic_boundaries(text)
    
    final_chunks = []
    for block in semantic_blocks:
        if len(block) <= CHUNK_SIZE:
            final_chunks.append({"text": block, "strategy": "semantic"})
        else:
            # If a semantic block is still too large, apply overlap chunking
            overlap_blocks = overlap_chunking(block, CHUNK_SIZE, CHUNK_OVERLAP)
            for ob in overlap_blocks:
                final_chunks.append({"text": ob, "strategy": "size_overlap"})
                
    return final_chunks


def generate_id(text: str) -> str:
    """Stable identifier based on text content."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def process_dataset():
    logger.info(f"Starting offline preprocessing for {DATASET_NAME} ({DATASET_CONFIG}, {DATASET_SPLIT})")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load dataset
    try:
        if PREPROCESS_SAMPLE_SIZE:
            sample_size = int(PREPROCESS_SAMPLE_SIZE)
            dataset = load_dataset(DATASET_NAME, DATASET_CONFIG, split=DATASET_SPLIT, streaming=True)
            dataset = dataset.take(sample_size)
            logger.info(f"Using development sample mode: Streaming {sample_size} records.")
            total_records = sample_size
        else:
            dataset = load_dataset(DATASET_NAME, DATASET_CONFIG, split=DATASET_SPLIT)
            total_records = len(dataset)
            logger.info(f"Processing all {total_records} records.")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return
        
    processed_count = 0
    skipped_count = 0
    exact_duplicates = 0
    total_chunks = 0
    
    seen_hashes = set()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for record in dataset:
            # MSMARCO-XI schema inspection shows passages -> Translated_passages (or English_passages)
            passages_data = record.get("passages", [])
            passages = []
            
            # Handle if it's a dict of lists (Standard HF Sequence)
            if isinstance(passages_data, dict):
                passages = passages_data.get("Translated_passage", passages_data.get("Translated_passages", []))
                if not passages:
                    passages = passages_data.get("English_passage", passages_data.get("English_passages", []))
            # Handle if it's a list of dicts
            elif isinstance(passages_data, list) and passages_data and isinstance(passages_data[0], dict):
                for p in passages_data:
                    text = p.get("Translated_passage", p.get("Translated_passages", ""))
                    if not text:
                        text = p.get("English_passage", p.get("English_passages", ""))
                    if text:
                        passages.append(text)
                
            if not passages:
                skipped_count += 1
                continue
                
            for passage_text in passages:
                passage_text = clean_text(passage_text)
                if not passage_text:
                    continue
                    
                doc_hash = generate_id(passage_text)
                
                # Duplicate handling (exact match)
                if doc_hash in seen_hashes:
                    exact_duplicates += 1
                    continue
                    
                seen_hashes.add(doc_hash)
                
                # Apply adaptive chunking
                chunks = adaptive_chunking(passage_text)
                
                # Strategy 3: Parent-Child relationship
                # Save each child chunk with its parent ID
                for i, chunk_info in enumerate(chunks):
                    chunk_text = chunk_info["text"]
                    chunk_id = f"{doc_hash}_{i}"
                    
                    chunk_record = {
                        "chunk_id": chunk_id,
                        "parent_id": doc_hash,
                        "document_id": str(record.get("query_id", "")),
                        "text": chunk_text,
                        "chunk_strategy": chunk_info["strategy"],
                        "chunk_index": i,
                        "chunk_count": len(chunks),
                        "dataset_name": DATASET_NAME,
                        "dataset_config": DATASET_CONFIG,
                        "dataset_split": DATASET_SPLIT,
                        "char_count": len(chunk_text)
                    }
                    
                    f.write(json.dumps(chunk_record, ensure_ascii=False) + '\n')
                    total_chunks += 1
                    
            processed_count += 1
            if processed_count % 1000 == 0:
                logger.info(f"Processed {processed_count} records...")

    # Generate Manifest
    manifest = {
        "dataset_name": DATASET_NAME,
        "dataset_config": DATASET_CONFIG,
        "dataset_split": DATASET_SPLIT,
        "processing_timestamp": datetime.utcnow().isoformat() + "Z",
        "records_processed": processed_count,
        "records_skipped": skipped_count,
        "duplicates_removed": exact_duplicates,
        "total_parent_records": len(seen_hashes),
        "total_chunks": total_chunks,
        "chunking_config": {
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP
        },
        "sample_mode": bool(PREPROCESS_SAMPLE_SIZE),
        "sample_size": PREPROCESS_SAMPLE_SIZE
    }
    
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)
        
    logger.info("Preprocessing complete.")
    logger.info(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    process_dataset()
