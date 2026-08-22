import os
import logging
import time
from typing import List, Dict, Any, Tuple
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# The strict grounded RAG prompt
SYSTEM_PROMPT = """You are a strictly grounded AI assistant for the EchoRAG system.
Your ONLY task is to answer the user's question based strictly on the provided context.

RULES:
1. Answer ONLY using the provided retrieved context.
2. Do not use unsupported facts, even if you know them to be true from your general knowledge.
3. If the context does not contain enough information to answer the question, you MUST reply EXACTLY with:
   "I could not find enough information in the available knowledge base to answer that reliably."
4. Do not invent or hallucinate sources.
5. Be concise and direct in your answer.
"""

class LLMProvider:
    def __init__(self):
        if not LLM_API_KEY:
            logger.warning("LLM_API_KEY is not set. Answer generation will fail.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
            
    def _build_context_string(self, chunks: List[Dict[str, Any]]) -> str:
        """Formats the retrieved chunks into a single context string."""
        if not chunks:
            return ""
            
        context_parts = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            text = chunk.get("text", "")
            context_parts.append(f"[Source: {chunk_id}]\n{text}")
            
        return "\n\n".join(context_parts)
        
    async def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        if not self.client:
            return "Configuration Error: LLM_API_KEY is not configured.", []
            
        if not context_chunks:
            return "I could not find enough information in the available knowledge base to answer that reliably.", []
            
        start_time = time.perf_counter()
        
        context_str = self._build_context_string(context_chunks)
        
        user_message = f"Context:\n{context_str}\n\nQuestion:\n{query}"
        
        try:
            response = await self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0, # Zero temperature for strict grounding
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            elapsed = time.perf_counter() - start_time
            logger.info(f"LLM Generation completed in {elapsed:.4f}s")
            
            # Map sources based on what was passed in
            sources = [{"chunk_id": c["chunk_id"], "rank": c.get("final_rank", i+1)} for i, c in enumerate(context_chunks)]
            
            return answer, sources
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error communicating with LLM provider: {str(e)}", []

llm_provider = LLMProvider()
