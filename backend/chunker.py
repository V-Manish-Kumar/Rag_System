"""
Text chunking module.
Splits documents into overlapping chunks with metadata preservation.
"""

from typing import List, Dict, Any
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Handles document chunking with token-aware splitting."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        """
        Initialize chunker with specified parameters.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Use tiktoken for accurate token counting (GPT tokenizer)
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # LangChain's recursive splitter with token counting
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping segments with metadata.
        
        Args:
            text: Input text to chunk
            metadata: Additional metadata (source, title, etc.)
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            return []
        
        # Split text using LangChain
        chunks = self.text_splitter.split_text(text)
        
        # Prepare metadata
        base_metadata = metadata or {}
        
        # Create chunk objects with metadata
        chunk_objects = []
        for idx, chunk_text in enumerate(chunks):
            chunk_obj = {
                "text": chunk_text,
                "metadata": {
                    **base_metadata,
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "position": idx,
                    "token_count": len(self.encoding.encode(chunk_text)),
                }
            }
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def get_token_count(self, text: str) -> int:
        """Get token count for a given text."""
        return len(self.encoding.encode(text))
