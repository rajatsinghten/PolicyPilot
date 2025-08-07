"""
Main Orchestration Script

Provides a unified interface to the PolicyPilot system for document processing
and query analysis.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

# Add app directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

import config
from app.ingestion import DocumentIngestion
from app.embedder import EmbeddingGenerator, EmbeddingStorage
from app.parser import QueryParser
from app.retriever import SemanticRetriever
from app.reasoner import LLMReasoner


class PolicyPilot:
    """Main class that orchestrates the document processing pipeline."""
    
    def __init__(
        self,
        use_openai: bool = None,
        embedding_model_type: str = "huggingface",
        use_llm_reasoning: bool = None
    ):
        """
        Initialize the PolicyPilot system.
        
        Args:
            use_openai: Whether to use OpenAI for embeddings (auto-detected if None)
            embedding_model_type: Type of embedding model ("openai" or "huggingface")
            use_llm_reasoning: Whether to use LLM for reasoning (auto-detected if None)
        """
        # Auto-detect Azure OpenAI or OpenAI availability
        if use_openai is None:
            use_openai = bool(config.AZURE_OPENAI_API_KEY or config.OPENAI_API_KEY)
        
        if use_llm_reasoning is None:
            use_llm_reasoning = bool(config.AZURE_OPENAI_API_KEY or config.OPENAI_API_KEY)
        
        # Determine embedding model type
        if use_openai and embedding_model_type == "openai":
            embedding_model_type = "openai"
        else:
            embedding_model_type = "huggingface"
        
        self.use_openai = use_openai
        self.use_llm_reasoning = use_llm_reasoning
        
        logger.info(f"Initializing PolicyPilot:")
        logger.info(f"  - Azure OpenAI/OpenAI embeddings: {use_openai}")
        logger.info(f"  - Embedding model: {embedding_model_type}")
        logger.info(f"  - LLM reasoning: {use_llm_reasoning}")
        
        # Initialize components
        self._initialize_components(embedding_model_type)
    
    def _initialize_components(self, embedding_model_type: str):
        """Initialize all system components."""
        try:
            # Document ingestion
            self.ingestion = DocumentIngestion()
            
            # Embedding generation
            self.embedder = EmbeddingGenerator(model_type=embedding_model_type)
            
            # Storage
            self.storage = EmbeddingStorage()
            
            # Query parsing
            self.parser = QueryParser(use_llm=self.use_openai)
            
            # Semantic retrieval
            self.retriever = SemanticRetriever(self.embedder)
            
            # LLM reasoning (if available)
            if self.use_llm_reasoning:
                try:
                    self.reasoner = LLMReasoner()
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM reasoner: {e}")
                    self.reasoner = None
                    self.use_llm_reasoning = False
            else:
                self.reasoner = None
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def ingest_documents(self, document_path: Path, rebuild_index: bool = True) -> int:
        """
        Ingest documents from a file or directory.
        
        Args:
            document_path: Path to document file or directory
            rebuild_index: Whether to rebuild the search index
            
        Returns:
            Number of chunks created
        """
        document_path = Path(document_path)
        
        if not document_path.exists():
            raise FileNotFoundError(f"Path not found: {document_path}")
        
        logger.info(f"Ingesting documents from: {document_path}")
        
        # Ingest documents
        if document_path.is_file():
            chunks = self.ingestion.ingest_file(document_path)
        else:
            chunks = self.ingestion.ingest_directory(document_path)
        
        if not chunks:
            logger.warning("No chunks created from documents")
            return 0
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embedded_chunks = self.embedder.embed_chunks(chunks)
        
        # Load existing chunks and combine
        existing_chunks = self.storage.load_embeddings()
        all_chunks = existing_chunks + embedded_chunks
        
        # Save embeddings
        self.storage.save_embeddings(all_chunks)
        logger.info(f"Saved {len(all_chunks)} total chunks")
        
        # Rebuild search index
        if rebuild_index:
            logger.info("Building search index...")
            self.retriever.create_index(all_chunks)
            self.retriever.save_index()
        
        logger.info(f"Document ingestion completed: {len(chunks)} new chunks created")
        return len(chunks)
    
    def load_existing_index(self) -> bool:
        """
        Load existing search index from storage.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Loading existing search index...")
        return self.retriever.load_index()
    
    def process_query(
        self,
        query: str,
        top_k: int = config.TOP_K_RESULTS,
        use_reasoning: bool = None
    ) -> Dict[str, Any]:
        """
        Process a natural language query.
        
        Args:
            query: Natural language query
            top_k: Number of top results to retrieve
            use_reasoning: Whether to use LLM reasoning (defaults to system setting)
            
        Returns:
            Dictionary with processing results
        """
        if use_reasoning is None:
            use_reasoning = self.use_llm_reasoning
        
        logger.info(f"Processing query: {query}")
        
        # Check if index is available
        if not self.retriever.index:
            if not self.load_existing_index():
                raise RuntimeError("No search index available. Please ingest documents first.")
        
        # Parse query
        parsed_query = self.parser.parse(query)
        logger.info(f"Parsed query: {parsed_query.to_dict()}")
        
        # Retrieve relevant chunks
        retrieved_chunks = self.retriever.search_parsed_query(parsed_query, top_k=top_k)
        
        if not retrieved_chunks:
            return {
                "decision": "No Information",
                "reasoning": "No relevant information found in the documents",
                "confidence": 0.0,
                "query_understanding": parsed_query.to_dict(),
                "retrieved_chunks": 0
            }
        
        # Create context
        context = self.retriever.get_context_window(retrieved_chunks)
        
        # Use LLM reasoning if available and requested
        if self.reasoner and use_reasoning:
            logger.info("Using LLM reasoning for decision making...")
            result = self.reasoner.analyze_claim(parsed_query, retrieved_chunks, context)
            
            response = result.to_dict()
            response["retrieved_chunks"] = len(retrieved_chunks)
            response["context_length"] = len(context)
            
            return response
        
        else:
            # Fallback without LLM reasoning
            logger.info("Using fallback reasoning (no LLM)")
            
            return {
                "decision": "Manual Review Required",
                "reasoning": f"Found {len(retrieved_chunks)} relevant document sections. Manual review recommended due to lack of automated reasoning capability.",
                "confidence": 0.7,
                "justification": {
                    "clauses": [
                        {
                            "text": chunk.text[:200] + "...",
                            "source": chunk.source,
                            "section": chunk.section or "Unknown",
                            "relevance_score": float(score)
                        }
                        for chunk, score in retrieved_chunks[:3]
                    ]
                },
                "recommendations": [
                    "Manual review by policy expert recommended",
                    "Consider enabling LLM reasoning for automated decisions"
                ],
                "query_understanding": parsed_query.to_dict(),
                "retrieved_chunks": len(retrieved_chunks),
                "context_length": len(context)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status and statistics.
        
        Returns:
            System status information
        """
        # Get document statistics
        chunks = self.storage.load_embeddings()
        sources = list(set(chunk.source for chunk in chunks)) if chunks else []
        
        status = {
            "system_ready": bool(self.retriever.index),
            "components": {
                "ingestion": "ready",
                "embedder": "ready",
                "parser": "ready",
                "retriever": "ready" if self.retriever.index else "no_index",
                "reasoner": "ready" if self.reasoner else "disabled"
            },
            "documents": {
                "total_documents": len(sources),
                "total_chunks": len(chunks),
                "sources": sources
            },
            "configuration": {
                "openai_available": bool(config.OPENAI_API_KEY),
                "embedding_model": self.embedder.model_name,
                "embedding_type": self.embedder.model_type,
                "llm_reasoning": self.use_llm_reasoning
            }
        }
        
        return status
    
    def clear_documents(self):
        """Clear all documents and rebuild empty index."""
        logger.info("Clearing all documents...")
        
        # Clear storage
        self.storage.save_embeddings([])
        
        # Clear index
        self.retriever.index = None
        
        # Remove index files
        if self.retriever.index_path.exists():
            self.retriever.index_path.unlink()
        if self.retriever.metadata_path.exists():
            self.retriever.metadata_path.unlink()
        
        logger.info("All documents cleared")


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PolicyPilot - LLM-Powered Document Processing")
    parser.add_argument("command", choices=["ingest", "query", "status", "clear"], help="Command to execute")
    parser.add_argument("--path", type=str, help="Path to documents (for ingest command)")
    parser.add_argument("--query", type=str, help="Query string (for query command)")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM reasoning")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI embeddings")
    
    args = parser.parse_args()
    
    # Initialize PolicyPilot
    pilot = PolicyPilot(
        use_openai=args.openai,
        use_llm_reasoning=not args.no_llm
    )
    
    if args.command == "ingest":
        if not args.path:
            print("Error: --path required for ingest command")
            return
        
        chunks_created = pilot.ingest_documents(Path(args.path))
        print(f"Successfully ingested documents: {chunks_created} chunks created")
    
    elif args.command == "query":
        if not args.query:
            print("Error: --query required for query command")
            return
        
        result = pilot.process_query(args.query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "status":
        status = pilot.get_system_status()
        print(json.dumps(status, indent=2))
    
    elif args.command == "clear":
        pilot.clear_documents()
        print("All documents cleared")


if __name__ == "__main__":
    main()
