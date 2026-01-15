"""
Vector store module using Qdrant Cloud.
Handles embedding generation and vector storage.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import settings
import uuid
import time


class VectorStore:
    """Manages vector embeddings and Qdrant Cloud storage."""
    
    def __init__(self):
        """Initialize Qdrant client and embedding model."""
        # Configure Google Gemini
        genai.configure(api_key=settings.google_api_key)
        
        # Initialize Qdrant Cloud client
        self.qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
        )
        
        self.collection_name = settings.collection_name
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if self.collection_name not in collection_names:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.vector_dimensions,
                    distance=Distance.COSINE,
                ),
            )
            print(f"Created collection: {self.collection_name}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query.
        
        Args:
            query: Query string
        
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(query)
    
    def add_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add document chunks to vector store.
        
        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'
            document_id: Optional document identifier
        
        Returns:
            Dictionary with ingestion stats
        """
        if not chunks:
            return {"status": "error", "message": "No chunks provided"}
        
        start_time = time.time()
        
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())
        
        # Extract texts
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Prepare points for Qdrant
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            
            payload = {
                "text": chunk["text"],
                "document_id": document_id,
                **chunk["metadata"],
            }
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
            points.append(point)
        
        # Upsert to Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        
        elapsed_time = time.time() - start_time
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_added": len(chunks),
            "time_seconds": round(elapsed_time, 2),
        }
    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using vector similarity.
        
        Args:
            query: Query string
            top_k: Number of results to return
            score_threshold: Minimum similarity score
        
        Returns:
            List of results with text, metadata, and scores
        """
        # Generate query embedding
        query_embedding = self.embed_query(query)
        
        # Search in Qdrant using query method
        try:
            search_response = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
            )
            search_results = search_response.points if hasattr(search_response, 'points') else search_response
        except Exception as e:
            print(f"Search error: {e}")
            return []
        
        # Format results
        results = []
        for hit in search_results:
            # Handle different response formats
            score = getattr(hit, 'score', 0.0)
            payload = getattr(hit, 'payload', {})
            
            result = {
                "text": payload.get("text", ""),
                "score": score,
                "metadata": {
                    k: v for k, v in payload.items() 
                    if k != "text"
                },
            }
            results.append(result)
        
        return results
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Deletion status
        """
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        
        return {"status": "success", "document_id": document_id}
    
    def clear_collection(self):
        """Clear all documents from collection."""
        self.qdrant_client.delete_collection(self.collection_name)
        self._ensure_collection()
        return {"status": "success", "message": "Collection cleared"}
