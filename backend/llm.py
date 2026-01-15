"""
LLM module for answer generation using Google Gemini.
Generates grounded answers with inline citations.
"""

from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
import time


class LLMGenerator:
    """Generates answers using Google Gemini with citation support."""
    
    def __init__(self):
        """Initialize Gemini LLM."""
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.google_api_key,
            temperature=0.3,
        )
        print(f"Using Gemini model via LangChain: gemini-2.0-flash")
    
    def generate_answer(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate an answer based on retrieved context.
        
        Args:
            query: User's question
            context_chunks: List of relevant chunks with text and metadata
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        start_time = time.time()
        
        # Check if we have any context
        if not context_chunks:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "confidence": "low",
                "time_seconds": round(time.time() - start_time, 2),
            }
        
        # Build context with numbered sources
        context_text = ""
        sources = []
        
        for idx, chunk in enumerate(context_chunks, start=1):
            context_text += f"\n[{idx}] {chunk['text']}\n"
            
            # Prepare source metadata
            metadata = chunk.get("metadata", {})
            source_info = {
                "citation_id": idx,
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "score": chunk.get("score", chunk.get("rerank_score", 0)),
                "source": metadata.get("source", "Unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
            }
            sources.append(source_info)
        
        # Create prompt with instructions for citation
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context.

CONTEXT:
{context_text}

INSTRUCTIONS:
1. Answer the question using ONLY information from the context above.
2. Use inline citations [1], [2], [3] etc. to reference the sources.
3. If the context doesn't contain enough information to fully answer the question, say so.
4. Be concise but comprehensive.
5. Do not make up information or use external knowledge.

QUESTION: {query}

ANSWER:"""
        
        # Generate response with retry logic
        max_retries = 3
        answer = ""
        
        try:
            for attempt in range(max_retries):
                try:
                    print(f"Attempting LLM call (attempt {attempt + 1}/{max_retries})...")
                    response = self.model.invoke(prompt)
                    answer = response.content
                    print(f"LLM Response received: {len(answer)} chars")
                    if answer:
                        print(f"Answer preview: {answer[:200]}...")
                    break
                except Exception as e:
                    error_msg = str(e)
                    print(f"LLM error on attempt {attempt + 1}: {error_msg}")
                    
                    if "Resource exhausted" in error_msg or "429" in error_msg or "rate" in error_msg.lower():
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 5  # Longer waits: 5s, 10s, 15s
                            print(f"Rate limit hit, waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print("Max retries reached, returning fallback response")
                            answer = "I'm experiencing rate limits with the AI service. Please wait a moment and try again."
                            break
                    else:
                        # Non-rate-limit error, raise it
                        raise
            
            if not answer:
                print("Warning: LLM returned empty answer!")
                answer = "I received the documents but couldn't generate an answer. Please try again."
            
            # Calculate confidence based on source quality
            avg_score = sum(s["score"] for s in sources) / len(sources)
            if avg_score >= 0.8:
                confidence = "high"
            elif avg_score >= 0.6:
                confidence = "medium"
            else:
                confidence = "low"
            
            elapsed_time = time.time() - start_time
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "time_seconds": round(elapsed_time, 2),
                "num_sources": len(sources),
            }
        
        except Exception as e:
            print(f"LLM generation error: {e}")
            return {
                "answer": f"An error occurred while generating the answer: {str(e)}",
                "sources": sources,
                "confidence": "low",
                "time_seconds": round(time.time() - start_time, 2),
            }
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 chars ≈ 1 token).
        
        Args:
            text: Input text
        
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate API cost for Gemini Pro.
        (Free tier: 60 requests/minute)
        
        Args:
            prompt_tokens: Input token count
            completion_tokens: Output token count
        
        Returns:
            Estimated cost in USD
        """
        # Gemini Pro pricing (as of 2024)
        # Free tier available, paid pricing:
        # $0.00025 per 1K characters for input
        # $0.0005 per 1K characters for output
        
        input_cost = (prompt_tokens * 4) / 1000 * 0.00025
        output_cost = (completion_tokens * 4) / 1000 * 0.0005
        
        return round(input_cost + output_cost, 6)
