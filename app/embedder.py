"""
Text Embedding Module

Handles generation and management of text embeddings using various embedding models.
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import numpy as np

from openai import AzureOpenAI, OpenAI
from sentence_transformers import SentenceTransformer
from loguru import logger

import config
from app.ingestion import DocumentChunk


class EmbeddingGenerator:
    """Generates and manages text embeddings."""
    
    def __init__(self, model_type: str = "openai", model_name: Optional[str] = None):
        """
        Initialize the embedding generator.
        
        Args:
            model_type: Type of embedding model ("openai" or "huggingface")
            model_name: Specific model name (optional)
        """
        self.model_type = model_type
        self.model_name = model_name or self._get_default_model()
        self.model = None
        
        self._initialize_model()
        logger.info(f"Initialized {model_type} embedding generator with model: {self.model_name}")
    
    def _get_default_model(self) -> str:
        """Get default model name based on model type."""
        if self.model_type == "openai":
            return config.EMBEDDING_MODEL
        elif self.model_type == "huggingface":
            return "all-MiniLM-L6-v2"  # Good balance of speed and quality
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            if self.model_type == "openai":
                # Check for Azure OpenAI configuration first
                if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
                    self.client = AzureOpenAI(
                        api_key=config.AZURE_OPENAI_API_KEY,
                        api_version=config.AZURE_OPENAI_API_VERSION,
                        azure_endpoint=config.AZURE_OPENAI_ENDPOINT
                    )
                elif config.OPENAI_API_KEY:
                    # Fallback to regular OpenAI
                    self.client = OpenAI(api_key=config.OPENAI_API_KEY)
                else:
                    raise ValueError("Neither Azure OpenAI nor OpenAI API key found in environment variables")
                
            elif self.model_type == "huggingface":
                self.model = SentenceTransformer(self.model_name)
                
        except Exception as e:
            logger.error(f"Failed to initialize {self.model_type} model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            if self.model_type == "openai":
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=text
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)
                
            elif self.model_type == "huggingface":
                embedding = self.model.encode([text])[0]
                
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for text: {e}")
            return np.array([])
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[np.ndarray]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                if self.model_type == "openai":
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch
                    )
                    batch_embeddings = [
                        np.array(data.embedding, dtype=np.float32) 
                        for data in response.data
                    ]
                    
                elif self.model_type == "huggingface":
                    batch_embeddings = self.model.encode(batch)
                    batch_embeddings = [
                        np.array(emb, dtype=np.float32) 
                        for emb in batch_embeddings
                    ]
                
                embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Add empty embeddings for failed batch
                embeddings.extend([np.array([]) for _ in batch])
        
        return embeddings
    
    def embed_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Generate embeddings for document chunks.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            List of DocumentChunk objects with embeddings added to metadata
        """
        if not chunks:
            return []
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts)
        
        # Add embeddings to chunk metadata
        for chunk, embedding in zip(chunks, embeddings):
            if len(embedding) > 0:
                chunk.metadata["embedding"] = embedding
                chunk.metadata["embedding_model"] = self.model_name
            else:
                logger.warning(f"Failed to generate embedding for chunk: {chunk.chunk_id}")
        
        return chunks
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the current model.
        
        Returns:
            Embedding dimension
        """
        if self.model_type == "openai":
            return config.EMBEDDING_DIMENSION
        elif self.model_type == "huggingface":
            # Get dimension by encoding a sample text
            sample_embedding = self.generate_embedding("sample text")
            return len(sample_embedding)
        else:
            return 768  # Default dimension


class EmbeddingStorage:
    """Handles storage and retrieval of embeddings."""
    
    def __init__(self, storage_path: Path = config.EMBEDDINGS_DIR):
        """
        Initialize embedding storage.
        
        Args:
            storage_path: Path to store embeddings
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        logger.info(f"Initialized embedding storage at: {storage_path}")
    
    def save_embeddings(self, chunks: List[DocumentChunk], filename: str = "embeddings.pkl"):
        """
        Save embedded chunks to file.
        
        Args:
            chunks: List of DocumentChunk objects with embeddings
            filename: Name of the file to save
        """
        file_path = self.storage_path / filename
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(chunks, f)
            logger.info(f"Saved {len(chunks)} embedded chunks to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
    
    def load_embeddings(self, filename: str = "embeddings.pkl") -> List[DocumentChunk]:
        """
        Load embedded chunks from file.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            List of DocumentChunk objects with embeddings
        """
        file_path = self.storage_path / filename
        
        if not file_path.exists():
            logger.warning(f"Embeddings file not found: {file_path}")
            return []
        
        try:
            with open(file_path, 'rb') as f:
                chunks = pickle.load(f)
            logger.info(f"Loaded {len(chunks)} embedded chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return []
    
    def get_embeddings_matrix(self, chunks: List[DocumentChunk]) -> np.ndarray:
        """
        Extract embeddings matrix from chunks.
        
        Args:
            chunks: List of DocumentChunk objects with embeddings
            
        Returns:
            Matrix of embeddings (n_chunks x embedding_dim)
        """
        embeddings = []
        
        for chunk in chunks:
            if "embedding" in chunk.metadata:
                embeddings.append(chunk.metadata["embedding"])
        
        if not embeddings:
            logger.warning("No embeddings found in chunks")
            return np.array([])
        
        return np.vstack(embeddings)
    
    def save_metadata(self, chunks: List[DocumentChunk], filename: str = "metadata.pkl"):
        """
        Save chunk metadata separately.
        
        Args:
            chunks: List of DocumentChunk objects
            filename: Name of the metadata file
        """
        file_path = self.storage_path / filename
        
        metadata = [chunk.to_dict() for chunk in chunks]
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(metadata, f)
            logger.info(f"Saved metadata for {len(chunks)} chunks to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")


# Example usage
if __name__ == "__main__":
    from app.ingestion import DocumentIngestion
    
    # Initialize components
    ingestion = DocumentIngestion()
    embedder = EmbeddingGenerator(model_type="huggingface")  # Use HuggingFace for demo
    storage = EmbeddingStorage()
    
    # Ingest documents
    chunks = ingestion.ingest_directory(config.DOCUMENTS_DIR)
    
    if chunks:
        # Generate embeddings
        embedded_chunks = embedder.embed_chunks(chunks)
        
        # Save embeddings
        storage.save_embeddings(embedded_chunks)
        
        print(f"Processed {len(embedded_chunks)} chunks")
        print(f"Embedding dimension: {embedder.get_embedding_dimension()}")
    else:
        print("No documents found to process")
