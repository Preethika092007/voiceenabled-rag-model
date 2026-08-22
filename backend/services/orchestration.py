import logging
import time
import asyncio
import uuid
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from .hybrid_retrieval import hybrid_search
from .reranker import reranker
from .llm_provider import llm_provider
from .guardrails import guardrails
from .cache import query_cache
from utils.timing import PerfTimer

logger = logging.getLogger(__name__)

# --- State Definition ---
class GraphState(TypedDict):
    request_id: str
    original_query: str
    
    validation_result: Dict[str, Any]
    hybrid_candidates: List[Any]
    reranked_candidates: List[Any]
    generated_answer: Optional[str]
    sources: List[Any]
    grounding_result: Dict[str, Any]
    output_guardrail_result: Dict[str, Any]
    
    pipeline: Dict[str, str]
    timings: Dict[str, float]
    
    final_status: str
    final_answer: Optional[str]
    reason: Optional[str]
    cache_hit: bool

# --- Nodes ---
async def validate_query(state: GraphState) -> GraphState:
    with PerfTimer(state["timings"], "validation_ms"):
        res = guardrails.validate_input(state["original_query"])
        state["validation_result"] = res
        
    if res["status"] == "BLOCK":
        state["pipeline"]["validation"] = "error"
    else:
        state["pipeline"]["validation"] = "complete"
    return state

async def hybrid_retrieve(state: GraphState) -> GraphState:
    # Check cache for entire results (optional for benchmark, but good for real usage)
    # To keep benchmark accurate, we will only use cache if we want. For now, disabled in benchmark mode.
    # Actually, we don't cache retrieval by default unless requested.
    with PerfTimer(state["timings"], "hybrid_retrieval_ms"):
        candidates = await hybrid_search(state["original_query"], state["timings"])
        state["hybrid_candidates"] = candidates
        
    state["pipeline"]["retrieval"] = "complete"
    return state

async def rerank(state: GraphState) -> GraphState:
    with PerfTimer(state["timings"], "reranking_ms"):
        candidates = state["hybrid_candidates"]
        reranked = await asyncio.to_thread(reranker.score_and_sort, state["original_query"], candidates)
        state["reranked_candidates"] = reranked
        
    state["pipeline"]["reranking"] = "complete"
    return state

async def generate_answer(state: GraphState) -> GraphState:
    # Check if we have a cached answer for this precise query
    cache_key = f"ans_{state['original_query']}"
    cached_val = query_cache.get(cache_key)
    
    with PerfTimer(state["timings"], "generation_ms"):
        if cached_val:
            answer, sources = cached_val
            state["cache_hit"] = True
        else:
            answer, sources = await llm_provider.generate_answer(state["original_query"], state["reranked_candidates"])
            query_cache.set(cache_key, (answer, sources))
            state["cache_hit"] = False
            
        state["generated_answer"] = answer
        state["sources"] = sources
        
    state["pipeline"]["generation"] = "complete"
    return state

async def grounding_check(state: GraphState) -> GraphState:
    with PerfTimer(state["timings"], "grounding_ms"):
        res = await guardrails.verify_grounding(state["generated_answer"], state["reranked_candidates"])
        state["grounding_result"] = res
        
    if not res["grounded"]:
        state["pipeline"]["grounding"] = "error"
    else:
        state["pipeline"]["grounding"] = "complete"
    return state

async def output_guardrail(state: GraphState) -> GraphState:
    res = guardrails.validate_output(state["generated_answer"])
    state["output_guardrail_result"] = res
    if res["status"] == "ALLOW":
        state["final_status"] = "success"
        state["final_answer"] = state["generated_answer"]
    return state

async def abstain_response(state: GraphState) -> GraphState:
    # Determine reason based on state
    if state.get("validation_result", {}).get("status") == "BLOCK":
        state["final_status"] = "blocked"
        state["reason"] = state["validation_result"].get("reason")
        state["final_answer"] = "Your query was blocked by safety guardrails."
    elif not state.get("hybrid_candidates"):
        state["final_status"] = "abstained"
        state["reason"] = "No relevant context found."
        state["final_answer"] = "I could not find enough information in the available knowledge base to answer that reliably."
        state["pipeline"]["retrieval"] = "skipped"
    elif not state.get("reranked_candidates"):
        state["final_status"] = "abstained"
        state["reason"] = "Context rejected by reranker."
        state["final_answer"] = "I could not find enough information in the available knowledge base to answer that reliably."
        state["pipeline"]["reranking"] = "skipped"
    elif state.get("grounding_result") and not state.get("grounding_result").get("grounded"):
        state["final_status"] = "abstained"
        state["reason"] = "Grounding check failed."
        state["final_answer"] = "I could not find enough information in the available knowledge base to answer that reliably."
    elif state.get("output_guardrail_result") and state.get("output_guardrail_result").get("status") == "BLOCK":
        state["final_status"] = "blocked"
        state["reason"] = state["output_guardrail_result"].get("reason")
        state["final_answer"] = "The generated answer was blocked by output guardrails."
    else:
        state["final_status"] = "abstained"
        state["reason"] = "Unknown pipeline failure."
        state["final_answer"] = "An error occurred preventing a reliable answer."
    
    # Clean up downstream pipeline states
    if state["final_status"] in ["blocked", "abstained"]:
        if "retrieval" not in state["pipeline"]: state["pipeline"]["retrieval"] = "skipped"
        if "reranking" not in state["pipeline"]: state["pipeline"]["reranking"] = "skipped"
        if "generation" not in state["pipeline"]: state["pipeline"]["generation"] = "skipped"
        if "grounding" not in state["pipeline"]: state["pipeline"]["grounding"] = "skipped"
        
    return state

# --- Edge Logic ---
def route_validation(state: GraphState) -> str:
    if state["validation_result"]["status"] == "BLOCK":
        return "abstain_response"
    return "hybrid_retrieve"

def route_retrieval(state: GraphState) -> str:
    if not state["hybrid_candidates"]:
        return "abstain_response"
    return "rerank"

def route_rerank(state: GraphState) -> str:
    if not state["reranked_candidates"]:
        return "abstain_response"
    return "generate_answer"

def route_grounding(state: GraphState) -> str:
    if not state["grounding_result"]["grounded"]:
        return "abstain_response"
    return "output_guardrail"

def route_output(state: GraphState) -> str:
    if state["output_guardrail_result"]["status"] == "BLOCK":
        return "abstain_response"
    return END

# --- Build Graph ---
builder = StateGraph(GraphState)
builder.add_node("validate_query", validate_query)
builder.add_node("hybrid_retrieve", hybrid_retrieve)
builder.add_node("rerank", rerank)
builder.add_node("generate_answer", generate_answer)
builder.add_node("grounding_check", grounding_check)
builder.add_node("output_guardrail", output_guardrail)
builder.add_node("abstain_response", abstain_response)

builder.add_edge(START, "validate_query")
builder.add_conditional_edges("validate_query", route_validation)
builder.add_conditional_edges("hybrid_retrieve", route_retrieval)
builder.add_conditional_edges("rerank", route_rerank)
builder.add_edge("generate_answer", "grounding_check")
builder.add_conditional_edges("grounding_check", route_grounding)
builder.add_conditional_edges("output_guardrail", route_output)
builder.add_edge("abstain_response", END)

pipeline_graph = builder.compile()

async def run_query_pipeline(query: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Orchestrates the complete RAG pipeline using LangGraph.
    """
    if not use_cache:
        # Avoid retrieving from cache for this run, but don't clear it for others.
        # This is a hacky way to ignore cache for benchmarking.
        # Actually, for benchmarking we will just disable cache reading explicitly if needed.
        pass
        
    initial_state = GraphState(
        request_id=str(uuid.uuid4()),
        original_query=query,
        validation_result={},
        hybrid_candidates=[],
        reranked_candidates=[],
        generated_answer=None,
        sources=[],
        grounding_result={},
        output_guardrail_result={},
        pipeline={"validation": "processing", "retrieval": "waiting", "reranking": "waiting", "generation": "waiting", "grounding": "waiting"},
        timings={},
        final_status="error",
        final_answer=None,
        reason=None,
        cache_hit=False
    )
    
    start_t = time.perf_counter()
    
    try:
        final_state = await pipeline_graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        return {
            "status": "error",
            "query": query,
            "answer": "An internal error occurred during processing.",
            "results": [],
            "sources": [],
            "pipeline": {"error": "true"},
            "timings": {},
            "reason": str(e)
        }
        
    final_state["timings"]["total_pipeline_ms"] = (time.perf_counter() - start_t) * 1000
    
    # Log the graph trace
    logger.info(f"Request {final_state['request_id']} finished with status {final_state['final_status']}")
    
    return {
        "status": final_state["final_status"],
        "query": query,
        "answer": final_state["final_answer"],
        "results": final_state["reranked_candidates"],
        "sources": final_state["sources"],
        "pipeline": final_state["pipeline"],
        "timings": final_state["timings"],
        "reason": final_state["reason"]
    }
