"""
FastAPI application for Mini RAG.
Provides REST API endpoints for document ingestion and querying.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from rag_pipeline import RAGPipeline
from config import settings
import time
import pypdf
import io


# Initialize FastAPI app
app = FastAPI(
    title="Mini RAG API",
    description="Retrieval-Augmented Generation API with Qdrant, Gemini, and Jina",
    version="1.0.0",
    root_path="/api"  # For Vercel serverless routing
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline with error handling
try:
    rag = RAGPipeline()
    initialization_error = None
except Exception as e:
    rag = None
    initialization_error = str(e)
    print(f"ERROR: Failed to initialize RAG pipeline: {e}")


# Request/Response Models
class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    text: str = Field(..., description="Document text to ingest")
    source: Optional[str] = Field(None, description="Source identifier")
    title: Optional[str] = Field(None, description="Document title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class QueryRequest(BaseModel):
    """Request model for querying."""
    query: str = Field(..., description="User's question")


class IngestResponse(BaseModel):
    """Response model for ingestion."""
    status: str
    document_id: Optional[str] = None
    chunks_added: Optional[int] = None
    total_time_seconds: Optional[float] = None
    chunk_stats: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class Source(BaseModel):
    """Source citation model."""
    citation_id: int
    text: str
    score: float
    source: str
    chunk_index: int


class QueryResponse(BaseModel):
    """Response model for queries."""
    answer: str
    sources: List[Source]
    confidence: str
    timings: Optional[Dict[str, float]] = None
    token_stats: Optional[Dict[str, int]] = None
    estimated_cost_usd: Optional[float] = None
    retrieval_stats: Optional[Dict[str, int]] = None


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Mini RAG API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    if initialization_error:
        return {
            "status": "error",
            "error": initialization_error,
            "timestamp": time.time(),
        }
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "config": {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "collection_name": settings.collection_name,
            "top_k_retrieval": settings.top_k_retrieval,
            "top_k_rerank": settings.top_k_rerank,
        },
    }


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingest a document into the knowledge base.
    
    The document will be:
    1. Chunked into overlapping segments
    2. Embedded using Google Gemini
    3. Stored in Qdrant Cloud
    """
    try:
        # Prepare metadata
        metadata = request.metadata or {}
        if request.source:
            metadata["source"] = request.source
        if request.title:
            metadata["title"] = request.title
        
        # Ingest document
        result = rag.ingest_document(request.text, metadata)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """
    Ingest a document from file upload (PDF, TXT, or DOCX).
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.endswith(".pdf"):
            # Parse PDF
            pdf_file = io.BytesIO(content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        elif file.filename.endswith(".txt"):
            # Plain text
            text = content.decode("utf-8")
        
        elif file.filename.endswith(".docx"):
            # Parse DOCX
            from docx import Document
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            text = "\n".join([para.text for para in doc.paragraphs])
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, TXT, or DOCX."
            )
        
        # Ingest the extracted text
        metadata = {
            "source": file.filename,
            "title": file.filename,
        }
        
        result = rag.ingest_document(text, metadata)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge base.
    
    The system will:
    1. Retrieve top-k relevant chunks
    2. Rerank using Jina Reranker
    3. Generate an answer with citations using Gemini
    """
    try:
        result = rag.query(request.query)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/retrieve")
async def retrieve_context(request: QueryRequest):
    """
    Retrieve relevant context chunks without LLM generation.
    Returns chunks for frontend to use with Puter.js
    """
    try:
        import time
        # Step 1: Retrieve chunks
        retrieved_chunks = rag.vector_store.search(
            query=request.query,
            top_k=settings.top_k_retrieval,
            score_threshold=settings.similarity_threshold,
        )
        
        print(f"Retrieved {len(retrieved_chunks)} chunks")
        for i, chunk in enumerate(retrieved_chunks[:3]):
            print(f"  Chunk {i+1}: source={chunk.get('metadata', {}).get('source', 'Unknown')}, score={chunk.get('score', 0)}")
        
        if not retrieved_chunks:
            return {
                "chunks": [],
                "query": request.query,
                "message": "No relevant documents found"
            }
        
        # Step 2: Optionally rerank
        if settings.use_reranker:
            reranked_chunks = rag.reranker.rerank(
                query=request.query,
                documents=retrieved_chunks,
                top_k=settings.top_k_rerank,
            )
        else:
            reranked_chunks = retrieved_chunks[:settings.top_k_rerank]
        
        return {
            "chunks": reranked_chunks,
            "query": request.query,
            "num_chunks": len(reranked_chunks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@app.delete("/clear")
async def clear_knowledge_base():
    """Clear all documents from the knowledge base."""
    try:
        result = rag.clear_all_data()
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get statistics about the knowledge base."""
    try:
        # Get collection info from Qdrant
        collection_info = rag.vector_store.qdrant_client.get_collection(
            settings.collection_name
        )
        
        # Get unique document sources
        scroll_result = rag.vector_store.qdrant_client.scroll(
            collection_name=settings.collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        
        unique_sources = set()
        unique_doc_ids = set()
        for point in scroll_result[0]:
            if point.payload:
                if 'source' in point.payload:
                    unique_sources.add(point.payload['source'])
                if 'document_id' in point.payload:
                    unique_doc_ids.add(point.payload['document_id'])
        
        return {
            "collection_name": settings.collection_name,
            "total_vectors": collection_info.points_count,
            "unique_documents": len(unique_doc_ids),
            "unique_sources": len(unique_sources),
            "source_names": list(unique_sources),
            "vector_dimensions": settings.vector_dimensions,
            "config": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "top_k_retrieval": settings.top_k_retrieval,
                "top_k_rerank": settings.top_k_rerank,
            },
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=True
    )
