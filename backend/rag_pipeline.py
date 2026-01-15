"""
RAG Pipeline orchestrator.
Coordinates chunking, retrieval, reranking, and answer generation.
"""

from typing import Dict, Any, List
from chunker import DocumentChunker
from vector_store import VectorStore
from reranker import JinaReranker
from llm import LLMGenerator
from config import settings
import time


class RAGPipeline:
    """Main RAG pipeline coordinating all components."""
    
    def __init__(self):
        """Initialize all RAG components."""
        self.chunker = DocumentChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.vector_store = VectorStore()
        self.reranker = JinaReranker()
        self.llm = LLMGenerator()
    
    def ingest_document(
        self, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document: chunk, embed, and store.
        
        Args:
            text: Document text
            metadata: Optional metadata (source, title, etc.)
        
        Returns:
            Ingestion status and statistics
        """
        start_time = time.time()
        
        # Step 1: Chunk the document
        chunks = self.chunker.chunk_text(text, metadata)
        
        if not chunks:
            return {
                "status": "error",
                "message": "No chunks generated from document",
            }
        
        # Step 2: Add chunks to vector store
        result = self.vector_store.add_chunks(chunks)
        
        elapsed_time = time.time() - start_time
        
        return {
            **result,
            "total_time_seconds": round(elapsed_time, 2),
            "chunk_stats": {
                "total_chunks": len(chunks),
                "avg_chunk_size": sum(c["metadata"]["token_count"] for c in chunks) // len(chunks),
            },
        }
    
    def query(
        self, 
        query: str,
        include_timings: bool = True,
    ) -> Dict[str, Any]:
        """
        Query the RAG system: retrieve, rerank, and generate answer.
        
        Args:
            query: User's question
            include_timings: Whether to include detailed timing info
        
        Returns:
            Answer with sources and metadata
        """
        import time  # Ensure time is available in this scope
        timings = {}
        overall_start = time.time()
        
        # Step 1: Retrieve top-k chunks using vector similarity
        retrieval_start = time.time()
        retrieved_chunks = self.vector_store.search(
            query=query,
            top_k=settings.top_k_retrieval,
            score_threshold=settings.similarity_threshold,
        )
        timings["retrieval"] = round(time.time() - retrieval_start, 2)
        
        print(f"Retrieved {len(retrieved_chunks)} chunks")  # Debug
        if retrieved_chunks:
            print(f"Top score: {retrieved_chunks[0].get('score', 0)}")  # Debug
        
        # Check if we have any results
        if not retrieved_chunks:
            return {
                "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                "sources": [],
                "confidence": "low",
                "timings": timings if include_timings else None,
            }
        
        # Step 2: Rerank retrieved chunks (if enabled)
        if settings.use_reranker:
            rerank_start = time.time()
            reranked_chunks = self.reranker.rerank(
                query=query,
                documents=retrieved_chunks,
                top_k=settings.top_k_rerank,
            )
            timings["reranking"] = round(time.time() - rerank_start, 2)
        else:
            reranked_chunks = retrieved_chunks[:settings.top_k_rerank]
            timings["reranking"] = 0
        
        # Step 3: Generate answer with LLM
        generation_start = time.time()
        result = self.llm.generate_answer(query, reranked_chunks)
        timings["generation"] = result.get("time_seconds", 0)
        
        # Add overall timing
        timings["total"] = round(time.time() - overall_start, 2)
        
        # Add cost estimation
        prompt_tokens = self.llm.estimate_tokens(query + str([c["text"] for c in reranked_chunks]))
        completion_tokens = self.llm.estimate_tokens(result["answer"])
        estimated_cost = self.llm.estimate_cost(prompt_tokens, completion_tokens)
        
        return {
            **result,
            "timings": timings if include_timings else None,
            "token_stats": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "estimated_cost_usd": estimated_cost,
            "retrieval_stats": {
                "initial_retrieved": len(retrieved_chunks),
                "after_reranking": len(reranked_chunks),
            },
        }
    
    def clear_all_data(self) -> Dict[str, Any]:
        """Clear all documents from the knowledge base."""
        return self.vector_store.clear_collection()
