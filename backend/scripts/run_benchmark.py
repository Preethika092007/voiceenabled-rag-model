import os
import sys
import json
import time
import asyncio
from datetime import datetime
import numpy as np

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.vector_retrieval import vector_retriever
from services.bm25_retrieval import bm25_retriever
from services.reranker import reranker
from services.orchestration import run_query_pipeline
from services.cache import query_cache

N_WARMUP = int(os.getenv("BENCHMARK_WARMUP", "2"))
N_REPETITIONS = int(os.getenv("BENCHMARK_REPETITIONS", "3"))

async def run_benchmarks():
    print("Loading models and indices...")
    vector_retriever.load()
    bm25_retriever.load()
    reranker.load()
    print("Models loaded successfully.")
    
    queries_path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_queries.json")
    if not os.path.exists(queries_path):
        print(f"Benchmark queries not found at {queries_path}")
        return
        
    with open(queries_path, "r", encoding="utf-8") as f:
        queries = json.load(f)
        
    print(f"Loaded {len(queries)} queries.")
    
    # Warmup
    print(f"Running {N_WARMUP} warmup queries...")
    for i in range(N_WARMUP):
        query = queries[i % len(queries)]["query"]
        await run_query_pipeline(query, use_cache=False)
        
    print("Warmup complete. Starting benchmark...")
    
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "benchmark_mode": "local_text_pipeline",
        "dataset_version": "ai4bharat/MSMARCO-XI",
        "samples": len(queries) * N_REPETITIONS,
        "successful_requests": 0,
        "abstained_requests": 0,
        "blocked_requests": 0,
        "failed_requests": 0,
        "timings": {
            "validation_ms": [],
            "hybrid_retrieval_ms": [],
            "reranking_ms": [],
            "generation_ms": [],
            "grounding_ms": [],
            "total_pipeline_ms": []
        },
        "percentiles": {}
    }
    
    for rep in range(N_REPETITIONS):
        print(f"--- Repetition {rep + 1}/{N_REPETITIONS} ---")
        for q in queries:
            query_text = q["query"]
            print(f"Benchmarking: '{query_text}'")
            # Clear cache to force real execution
            query_cache.clear()
            
            try:
                res = await run_query_pipeline(query_text, use_cache=False)
                
                status = res.get("status")
                if status == "success":
                    results["successful_requests"] += 1
                elif status == "abstained":
                    results["abstained_requests"] += 1
                elif status == "blocked":
                    results["blocked_requests"] += 1
                else:
                    results["failed_requests"] += 1
                    
                t = res.get("timings", {})
                
                # Only log stages if they were actually executed (not skipped)
                if "validation_ms" in t: results["timings"]["validation_ms"].append(t["validation_ms"])
                if "hybrid_retrieval_ms" in t: results["timings"]["hybrid_retrieval_ms"].append(t["hybrid_retrieval_ms"])
                if "reranking_ms" in t: results["timings"]["reranking_ms"].append(t["reranking_ms"])
                if "generation_ms" in t: results["timings"]["generation_ms"].append(t["generation_ms"])
                if "grounding_ms" in t: results["timings"]["grounding_ms"].append(t["grounding_ms"])
                if "total_pipeline_ms" in t: results["timings"]["total_pipeline_ms"].append(t["total_pipeline_ms"])
                
            except Exception as e:
                print(f"Error during benchmark query: {e}")
                results["failed_requests"] += 1

    print("\nCalculating percentiles...")
    for stage, times in results["timings"].items():
        if not times:
            continue
        arr = np.array(times)
        results["percentiles"][stage] = {
            "count": len(times),
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p70": round(float(np.percentile(arr, 70)), 2),
            "p100": round(float(np.max(arr)), 2),
            "avg": round(float(np.mean(arr)), 2),
            "min": round(float(np.min(arr)), 2)
        }
        
    # Print summary
    print("\nBenchmark Summary:")
    print("-" * 50)
    for stage, stats in results["percentiles"].items():
        print(f"{stage.upper():<25} | P50: {stats['p50']:>6.2f}ms | P70: {stats['p70']:>6.2f}ms | P100: {stats['p100']:>6.2f}ms")
    print("-" * 50)
    
    # Save results
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
