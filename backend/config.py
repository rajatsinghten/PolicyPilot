"""
Configuration settings for PolicyPilot
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)
EMBEDDINGS_DIR.mkdir(exist_ok=True)

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT") 
AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "temp-gpt-4o-mini")
AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
EMBEDDING_MODEL: str = "text-embedding-ada-002"

# Legacy OpenAI Configuration (for backward compatibility)
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = "gpt-3.5-turbo"  # Changed from gpt-4 to gpt-3.5-turbo

# Document Processing
CHUNK_SIZE: int = 500  # tokens
CHUNK_OVERLAP: int = 50  # tokens
MAX_DOCUMENT_SIZE: int = 50 * 1024 * 1024  # 50MB

# Embeddings
EMBEDDING_DIMENSION: int = 1536  # for text-embedding-ada-002
FAISS_INDEX_TYPE: str = "IndexFlatIP"  # Inner Product (cosine similarity)

# Retrieval
TOP_K_RESULTS: int = 5
SIMILARITY_THRESHOLD: float = 0.3  # Lowered for better retrieval
INCLUDE_NEIGHBORS: bool = True  # Include neighboring chunks by default
NEIGHBOR_RANGE: int = 1  # Include ±1 neighboring chunks

# API Configuration
API_HOST: str = "0.0.0.0"
API_PORT: int = 8000
API_RELOAD: bool = True

# Supported file types
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".eml", ".msg", ".txt"}

# Logging
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
