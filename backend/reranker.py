"""
Reranker module using Jina AI Reranker API.
Improves retrieval quality by reranking initial results.
"""

from typing import List, Dict, Any
import requests
from config import settings


class JinaReranker:
    """Reranks retrieved chunks using Jina AI's reranker API."""
    
    def __init__(self):
        """Initialize Jina reranker with API key."""
        self.api_key = settings.jina_api_key
        self.api_url = "https://api.jina.ai/v1/rerank"
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: User query
            documents: List of document dictionaries with 'text' field
            top_k: Number of top results to return
        
        Returns:
            Reranked list of documents with relevance scores
        """
        if not documents:
            return []
        
        # Extract texts for reranking
        texts = [doc["text"] for doc in documents]
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": texts,
            "top_n": min(top_k, len(texts)),
        }
        
        try:
            # Call Jina reranker API
            response = requests.post(
                self.api_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Reranker API error: {response.status_code} - {response.text}")
                return documents[:top_k]
            
            result = response.json()
            
            # Map reranked results back to original documents
            reranked_docs = []
            for item in result.get("results", []):
                idx = item["index"]
                rerank_score = item["relevance_score"]
                
                # Get original document and add rerank score
                doc = documents[idx].copy()
                doc["rerank_score"] = rerank_score
                reranked_docs.append(doc)
            
            return reranked_docs
        
        except requests.exceptions.RequestException as e:
            print(f"Reranker API error: {e}")
            # Fallback: return original documents with their vector scores
            return documents[:top_k]
        except Exception as e:
            print(f"Reranking failed: {e}")
            return documents[:top_k]
