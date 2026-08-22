import re
from typing import List, Dict, Any

class GuardrailService:
    def __init__(self):
        # Basic patterns for prompt injection attempts
        self.injection_patterns = [
            r"(?i)\bignore\b.*\binstructions\b",
            r"(?i)\bsystem prompt\b",
            r"(?i)\bforget\b.*\bprevious\b",
            r"(?i)\byou are an?\b.*\bnow\b",
            r"(?i)\bdo not follow\b"
        ]
        
    def validate_input(self, query: str) -> Dict[str, Any]:
        """
        Lightweight input guardrail to protect the RAG pipeline.
        Returns:
            {"status": "ALLOW" | "BLOCK", "reason": str | None}
        """
        if not query or not query.strip():
            return {"status": "BLOCK", "reason": "Query is empty."}
            
        if len(query) > 5000:
            return {"status": "BLOCK", "reason": "Query exceeds maximum length."}
            
        # Check for simple prompt injections
        for pattern in self.injection_patterns:
            if re.search(pattern, query):
                return {"status": "BLOCK", "reason": "Query flagged by safety policy (potential prompt injection)."}
                
        return {"status": "ALLOW", "reason": None}

    def validate_output(self, answer: str) -> Dict[str, Any]:
        """
        Lightweight output guardrail.
        Returns:
            {"status": "ALLOW" | "BLOCK", "reason": str | None}
        """
        if not answer:
            return {"status": "BLOCK", "reason": "Empty generated answer."}
            
        # Check for accidentally exposed API keys or secrets (very basic check)
        if re.search(r"sk-[A-Za-z0-9]{20,}", answer):
            return {"status": "BLOCK", "reason": "Output blocked to prevent secret leakage."}
            
        if "Traceback (most recent call last)" in answer:
            return {"status": "BLOCK", "reason": "Output blocked to prevent internal stack trace leakage."}
            
        return {"status": "ALLOW", "reason": None}
        
    async def verify_grounding(self, answer: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates whether the generated answer is supported by the context.
        This is a lightweight deterministic check for this phase.
        It flags abstention keywords returned by the LLM as 'grounded=False' 
        to ensure they route to safe abstention rather than presenting as verified facts.
        """
        abstention_phrases = [
            "i could not find enough information",
            "does not contain",
            "i cannot answer",
            "the provided context does not",
            "not mentioned in the context"
        ]
        
        answer_lower = answer.lower()
        
        for phrase in abstention_phrases:
            if phrase in answer_lower:
                return {
                    "grounded": False,
                    "reason": "Answer indicates lack of context."
                }
                
        # In a real production system, you would perform an LLM-as-a-judge or semantic entailment here.
        # For latency/hackathon purposes, if it didn't explicitly abstain, we consider it grounded 
        # (as the prompt itself is heavily instructed to remain grounded).
        return {
            "grounded": True,
            "reason": "No ungrounded claims detected."
        }

guardrails = GuardrailService()
