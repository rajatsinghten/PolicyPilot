"""
FastAPI Application

REST API endpoints for the PolicyPilot document processing system.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from loguru import logger

import config
from app.ingestion import DocumentIngestion
from app.embedder import EmbeddingGenerator, EmbeddingStorage
from app.parser import QueryParser
from app.retriever import SemanticRetriever
from app.reasoner import LLMReasoner


# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    """Request model for query processing."""
    query: str
    top_k: Optional[int] = config.TOP_K_RESULTS
    use_llm_reasoning: Optional[bool] = True


class QueryResponse(BaseModel):
    """Response model for query processing."""
    decision: str
    amount: Optional[str] = None
    confidence: float
    reasoning: str
    justification: Dict[str, Any]
    recommendations: List[str]
    query_understanding: Dict[str, Any]
    processing_time: float


class UploadResponse(BaseModel):
    """Response model for file upload."""
    message: str
    filename: str
    chunks_created: int
    success: bool


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    components: Dict[str, str]


# Initialize FastAPI app
app = FastAPI(
    title="PolicyPilot API",
    description="LLM-Powered Document Processing System for Insurance Claims",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized on startup)
ingestion = None
embedder = None
storage = None
parser = None
retriever = None
reasoner = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup."""
    global ingestion, embedder, storage, parser, retriever, reasoner
    
    try:
        logger.info("Initializing PolicyPilot components...")
        
        # Initialize components
        ingestion = DocumentIngestion()
        embedder = EmbeddingGenerator(model_type="huggingface")  # Use HuggingFace by default
        storage = EmbeddingStorage()
        parser = QueryParser(use_llm=bool(config.OPENAI_API_KEY))
        retriever = SemanticRetriever(embedder)
        
        if config.OPENAI_API_KEY:
            reasoner = LLMReasoner()
        else:
            logger.warning("OpenAI API key not found. LLM reasoning will be disabled.")
            reasoner = None
        
        # Try to load existing index
        if retriever.load_index():
            logger.info("Loaded existing FAISS index")
        else:
            logger.info("No existing index found. Will create new one when documents are uploaded.")
        
        logger.info("PolicyPilot API initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic API information."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components={
            "ingestion": "ready",
            "embedder": "ready",
            "parser": "ready",
            "retriever": "ready" if retriever and retriever.index else "no_index",
            "reasoner": "ready" if reasoner else "disabled"
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return await root()


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload and process a document.
    
    Args:
        file: Document file to upload
        background_tasks: Background tasks for async processing
        
    Returns:
        Upload response with processing information
    """
    try:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in config.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported types: {config.SUPPORTED_EXTENSIONS}"
            )
        
        # Check file size
        if file.size > config.MAX_DOCUMENT_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {config.MAX_DOCUMENT_SIZE} bytes"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)
        
        # Process document
        chunks = ingestion.ingest_file(temp_path)
        
        if not chunks:
            # Clean up temp file
            temp_path.unlink()
            raise HTTPException(
                status_code=400,
                detail="Failed to extract content from document"
            )
        
        # Generate embeddings
        embedded_chunks = embedder.embed_chunks(chunks)
        
        # Save to storage
        existing_chunks = storage.load_embeddings()
        all_chunks = existing_chunks + embedded_chunks
        storage.save_embeddings(all_chunks)
        
        # Update retriever index in background
        background_tasks.add_task(update_index, all_chunks)
        
        # Clean up temp file
        temp_path.unlink()
        
        logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks created")
        
        return UploadResponse(
            message="Document uploaded and processed successfully",
            filename=file.filename,
            chunks_created=len(chunks),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_index(chunks: List):
    """Background task to update the FAISS index."""
    try:
        retriever.create_index(chunks)
        retriever.save_index()
        logger.info("Updated FAISS index with new documents")
    except Exception as e:
        logger.error(f"Error updating index: {e}")


@app.post("/process", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query.
    
    Args:
        request: Query request with query string and options
        
    Returns:
        Query response with decision and reasoning
    """
    import time
    start_time = time.time()
    
    try:
        # Check if retriever has an index
        if not retriever or not retriever.index:
            raise HTTPException(
                status_code=400,
                detail="No documents have been indexed. Please upload documents first."
            )
        
        # Parse the query
        parsed_query = parser.parse(request.query)
        logger.info(f"Parsed query: {parsed_query.to_dict()}")
        
        # Retrieve relevant chunks
        retrieved_chunks = retriever.search_parsed_query(
            parsed_query,
            top_k=request.top_k
        )
        
        if not retrieved_chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant information found for the query"
            )
        
        # Create context
        context = retriever.get_context_window(retrieved_chunks)
        
        # Use LLM reasoning if available and requested
        if reasoner and request.use_llm_reasoning:
            result = reasoner.analyze_claim(parsed_query, retrieved_chunks, context)
            
            processing_time = time.time() - start_time
            
            return QueryResponse(
                decision=result.decision.value,
                amount=result.amount,
                confidence=result.confidence,
                reasoning=result.reasoning,
                justification={
                    "clauses": [
                        {
                            "text": clause.text,
                            "source": clause.source,
                            "section": clause.section,
                            "relevance_score": clause.relevance_score
                        }
                        for clause in result.justification
                    ]
                },
                recommendations=result.recommendations,
                query_understanding=result.query_understanding,
                processing_time=processing_time
            )
        
        else:
            # Fallback response without LLM reasoning
            processing_time = time.time() - start_time
            
            return QueryResponse(
                decision="Pending",
                confidence=0.7,
                reasoning="Retrieved relevant policy information. Manual review recommended.",
                justification={
                    "clauses": [
                        {
                            "text": chunk.text[:200] + "...",
                            "source": chunk.source,
                            "section": chunk.section,
                            "relevance_score": score
                        }
                        for chunk, score in retrieved_chunks[:3]
                    ]
                },
                recommendations=["Manual review recommended", "Consult with policy expert"],
                query_understanding=parsed_query.to_dict(),
                processing_time=processing_time
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents():
    """List all processed documents."""
    try:
        chunks = storage.load_embeddings()
        
        # Get unique sources
        sources = list(set(chunk.source for chunk in chunks))
        
        # Get document statistics
        doc_stats = {}
        for chunk in chunks:
            source = chunk.source
            if source not in doc_stats:
                doc_stats[source] = {"chunks": 0, "total_tokens": 0}
            doc_stats[source]["chunks"] += 1
            doc_stats[source]["total_tokens"] += chunk.metadata.get("token_count", 0)
        
        return {
            "total_documents": len(sources),
            "total_chunks": len(chunks),
            "documents": [
                {
                    "name": source,
                    "chunks": doc_stats[source]["chunks"],
                    "estimated_tokens": doc_stats[source]["total_tokens"]
                }
                for source in sources
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_name}")
async def delete_document(document_name: str):
    """Delete a specific document and its chunks."""
    try:
        chunks = storage.load_embeddings()
        
        # Filter out chunks from the specified document
        remaining_chunks = [
            chunk for chunk in chunks 
            if chunk.source != document_name
        ]
        
        if len(remaining_chunks) == len(chunks):
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_name}' not found"
            )
        
        # Save updated chunks
        storage.save_embeddings(remaining_chunks)
        
        # Update index
        if remaining_chunks:
            retriever.create_index(remaining_chunks)
            retriever.save_index()
        else:
            # Clear index if no documents remain
            retriever.index = None
        
        deleted_chunks = len(chunks) - len(remaining_chunks)
        
        return {
            "message": f"Document '{document_name}' deleted successfully",
            "chunks_deleted": deleted_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/{query}")
async def search_documents(query: str, top_k: int = 5):
    """Search documents without LLM reasoning."""
    try:
        if not retriever or not retriever.index:
            raise HTTPException(
                status_code=400,
                detail="No documents have been indexed"
            )
        
        # Perform search
        results = retriever.search(query, top_k=top_k)
        
        # Format results
        formatted_results = [
            {
                "text": chunk.text,
                "source": chunk.source,
                "section": chunk.section,
                "similarity_score": float(score),
                "metadata": {k: v for k, v in chunk.metadata.items() if k != "embedding"}
            }
            for chunk, score in results
        ]
        
        return {
            "query": query,
            "results_found": len(results),
            "results": formatted_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD
    )
