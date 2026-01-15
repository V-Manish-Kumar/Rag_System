"""
Configuration module for Mini RAG application.
Loads environment variables and provides app-wide settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    jina_api_key: str
    
    # Chunking Parameters
    chunk_size: int = 1000
    chunk_overlap: int = 150
    
    # Vector Database
    collection_name: str = "mini_rag_docs"
    embedding_model: str = "models/embedding-001"
    vector_dimensions: int = 768
    
    # LLM Settings
    llm_model: str = "gemini-pro"
    
    # Retrieval Settings
    top_k_retrieval: int = 10
    top_k_rerank: int = 5
    similarity_threshold: float = 0.7
    use_reranker: bool = True
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
