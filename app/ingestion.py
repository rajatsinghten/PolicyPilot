"""
Document Ingestion Module

Handles loading, processing, and chunking of various document types including
PDF, DOCX, and email files.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib

import PyPDF2
from docx import Document
from loguru import logger

import config


class DocumentChunk:
    """Represents a chunk of text from a document with metadata."""
    
    def __init__(
        self,
        text: str,
        source: str,
        chunk_id: str,
        page_number: Optional[int] = None,
        section: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.source = source
        self.chunk_id = chunk_id
        self.page_number = page_number
        self.section = section
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary representation."""
        return {
            "text": self.text,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "page_number": self.page_number,
            "section": self.section,
            "metadata": self.metadata
        }


class DocumentIngestion:
    """Handles document loading, processing, and chunking."""
    
    def __init__(self, chunk_size: int = config.CHUNK_SIZE, chunk_overlap: int = config.CHUNK_OVERLAP):
        """
        Initialize the document ingestion system.
        
        Args:
            chunk_size: Size of text chunks in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"Initialized DocumentIngestion with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def load_pdf(self, file_path: Path) -> List[Tuple[str, int]]:
        """
        Load text content from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of tuples containing (text, page_number)
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pages = []
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        pages.append((text, page_num))
                        
                logger.info(f"Loaded {len(pages)} pages from {file_path}")
                return pages
                
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            return []
    
    def load_docx(self, file_path: Path) -> List[Tuple[str, int]]:
        """
        Load text content from a DOCX file.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            List of tuples containing (text, paragraph_number)
        """
        try:
            doc = Document(file_path)
            paragraphs = []
            
            for para_num, paragraph in enumerate(doc.paragraphs, 1):
                text = paragraph.text.strip()
                if text:
                    paragraphs.append((text, para_num))
                    
            logger.info(f"Loaded {len(paragraphs)} paragraphs from {file_path}")
            return paragraphs
            
        except Exception as e:
            logger.error(f"Error loading DOCX {file_path}: {e}")
            return []
    
    def load_text(self, file_path: Path) -> List[Tuple[str, int]]:
        """
        Load text content from a plain text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of tuples containing (text, line_number)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = []
                for line_num, line in enumerate(file, 1):
                    text = line.strip()
                    if text:
                        lines.append((text, line_num))
                        
            logger.info(f"Loaded {len(lines)} lines from {file_path}")
            return lines
            
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")
            return []
    
    def load_document(self, file_path: Path) -> List[Tuple[str, int]]:
        """
        Load document content based on file extension.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of tuples containing (text, section_number)
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self.load_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            return self.load_docx(file_path)
        elif extension in ['.txt', '.md']:
            return self.load_text(file_path)
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        Uses a simple approximation: ~4 characters per token.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def create_chunks(self, text_sections: List[Tuple[str, int]], source: str) -> List[DocumentChunk]:
        """
        Split text sections into overlapping chunks.
        
        Args:
            text_sections: List of (text, section_number) tuples
            source: Source document identifier
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_counter = 1
        
        for text, section_num in text_sections:
            cleaned_text = self.clean_text(text)
            text_tokens = self.estimate_tokens(cleaned_text)
            
            # If adding this text would exceed chunk size, finalize current chunk
            if current_tokens + text_tokens > self.chunk_size and current_chunk:
                chunk_id = f"{source}_chunk_{chunk_counter}"
                
                chunk = DocumentChunk(
                    text=current_chunk.strip(),
                    source=source,
                    chunk_id=chunk_id,
                    section=f"Section {section_num}",
                    metadata={
                        "token_count": current_tokens,
                        "section_numbers": [section_num]
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + " " + cleaned_text
                current_tokens = self.estimate_tokens(current_chunk)
                chunk_counter += 1
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += " " + cleaned_text
                else:
                    current_chunk = cleaned_text
                current_tokens = self.estimate_tokens(current_chunk)
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunk_id = f"{source}_chunk_{chunk_counter}"
            chunk = DocumentChunk(
                text=current_chunk.strip(),
                source=source,
                chunk_id=chunk_id,
                metadata={
                    "token_count": current_tokens
                }
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from {source}")
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """
        Extract overlap text from the end of a chunk.
        
        Args:
            text: Full text
            overlap_tokens: Number of overlap tokens desired
            
        Returns:
            Overlap text
        """
        words = text.split()
        if len(words) <= overlap_tokens:
            return text
        
        # Take last N words as approximation for overlap tokens
        overlap_words = words[-overlap_tokens:]
        return " ".join(overlap_words)
    
    def ingest_file(self, file_path: Path) -> List[DocumentChunk]:
        """
        Ingest a single file and return document chunks.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of DocumentChunk objects
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        if file_path.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {file_path.suffix}")
            return []
        
        # Check file size
        if file_path.stat().st_size > config.MAX_DOCUMENT_SIZE:
            logger.error(f"File too large: {file_path}")
            return []
        
        logger.info(f"Ingesting file: {file_path}")
        
        # Load document content
        text_sections = self.load_document(file_path)
        if not text_sections:
            return []
        
        # Create chunks
        source = file_path.name
        chunks = self.create_chunks(text_sections, source)
        
        return chunks
    
    def ingest_directory(self, directory_path: Path) -> List[DocumentChunk]:
        """
        Ingest all supported files in a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            List of all DocumentChunk objects
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        all_chunks = []
        
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
                chunks = self.ingest_file(file_path)
                all_chunks.extend(chunks)
        
        logger.info(f"Ingested {len(all_chunks)} total chunks from {directory_path}")
        return all_chunks
    
    def get_document_hash(self, file_path: Path) -> str:
        """
        Generate a hash for a document to track changes.
        
        Args:
            file_path: Path to the document
            
        Returns:
            MD5 hash of the file
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


# Example usage
if __name__ == "__main__":
    # Initialize ingestion system
    ingestion = DocumentIngestion()
    
    # Ingest a single file
    chunks = ingestion.ingest_file(Path("data/documents/sample_policy.pdf"))
    
    # Print first chunk
    if chunks:
        print(f"First chunk: {chunks[0].text[:200]}...")
        print(f"Source: {chunks[0].source}")
        print(f"Chunk ID: {chunks[0].chunk_id}")
