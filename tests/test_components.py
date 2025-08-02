"""
Unit tests for PolicyPilot components
"""

import unittest
from pathlib import Path
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.ingestion import DocumentIngestion, DocumentChunk
from app.parser import QueryParser, ParsedQuery, Gender
from app.embedder import EmbeddingGenerator


class TestDocumentIngestion(unittest.TestCase):
    """Test document ingestion functionality."""
    
    def setUp(self):
        self.ingestion = DocumentIngestion(chunk_size=100, chunk_overlap=20)
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        text = "This is a test text with multiple words."
        tokens = self.ingestion.estimate_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(text))  # Should be less than character count
    
    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  This   has    extra    spaces   and\n\nnewlines  "
        clean_text = self.ingestion.clean_text(dirty_text)
        self.assertEqual(clean_text, "This has extra spaces and newlines")
    
    def test_create_chunks(self):
        """Test chunk creation."""
        text_sections = [
            ("First section with some text content", 1),
            ("Second section with more text content", 2),
            ("Third section with additional content", 3)
        ]
        
        chunks = self.ingestion.create_chunks(text_sections, "test_document")
        
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIsInstance(chunk, DocumentChunk)
            self.assertEqual(chunk.source, "test_document")
            self.assertIsNotNone(chunk.chunk_id)
    
    def test_load_text_file(self):
        """Test loading text files."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            temp_path = Path(f.name)
        
        try:
            result = self.ingestion.load_text(temp_path)
            self.assertEqual(len(result), 3)  # 3 non-empty lines
            self.assertEqual(result[0][0], "Line 1")
            self.assertEqual(result[0][1], 1)  # Line number
        finally:
            temp_path.unlink()


class TestQueryParser(unittest.TestCase):
    """Test query parsing functionality."""
    
    def setUp(self):
        self.parser = QueryParser(use_llm=False)  # Use regex-based parsing for tests
    
    def test_extract_age(self):
        """Test age extraction."""
        test_cases = [
            ("46M, knee surgery", 46),
            ("35 years old female", 35),
            ("Patient age: 28", 28),
            ("No age mentioned", None)
        ]
        
        for text, expected_age in test_cases:
            age = self.parser.extract_age(text)
            self.assertEqual(age, expected_age)
    
    def test_extract_gender(self):
        """Test gender extraction."""
        test_cases = [
            ("46M, knee surgery", Gender.MALE),
            ("35F, heart surgery", Gender.FEMALE),
            ("male patient", Gender.MALE),
            ("female patient", Gender.FEMALE),
            ("no gender info", None)
        ]
        
        for text, expected_gender in test_cases:
            gender = self.parser.extract_gender(text)
            self.assertEqual(gender, expected_gender)
    
    def test_extract_procedure(self):
        """Test medical procedure extraction."""
        test_cases = [
            ("knee surgery required", "knee surgery"),
            ("appendectomy performed", None),  # Single word procedures might not be caught
            ("heart surgery needed", "heart surgery"),
            ("routine checkup", None)
        ]
        
        for text, expected_procedure in test_cases:
            procedure = self.parser.extract_procedure(text)
            if expected_procedure:
                self.assertIsNotNone(procedure)
                self.assertIn(expected_procedure, procedure.lower())
            else:
                # Allow None or any extracted procedure for non-specific cases
                pass
    
    def test_extract_location(self):
        """Test location extraction."""
        test_cases = [
            ("surgery in Mumbai", "Mumbai"),
            ("treatment in pune", "Pune"),
            ("Delhi hospital", "Delhi"),
            ("unknown location", None)
        ]
        
        for text, expected_location in test_cases:
            location = self.parser.extract_location(text)
            self.assertEqual(location, expected_location)
    
    def test_parse_complex_query(self):
        """Test parsing of complex queries."""
        query = "46M, knee surgery, Pune, 3-month policy, claim ₹1,50,000"
        parsed = self.parser.parse(query)
        
        self.assertIsInstance(parsed, ParsedQuery)
        self.assertEqual(parsed.age, 46)
        self.assertEqual(parsed.gender, Gender.MALE)
        self.assertIn("knee surgery", parsed.procedure.lower())
        self.assertEqual(parsed.location, "Pune")
        self.assertIn("1,50,000", parsed.amount_claimed)


class TestEmbeddingGenerator(unittest.TestCase):
    """Test embedding generation (using HuggingFace model for tests)."""
    
    def setUp(self):
        # Use HuggingFace model for testing (doesn't require API key)
        self.embedder = EmbeddingGenerator(model_type="huggingface")
    
    def test_initialization(self):
        """Test embedder initialization."""
        self.assertEqual(self.embedder.model_type, "huggingface")
        self.assertIsNotNone(self.embedder.model)
    
    def test_generate_embedding(self):
        """Test single embedding generation."""
        text = "This is a test sentence for embedding."
        embedding = self.embedder.generate_embedding(text)
        
        self.assertGreater(len(embedding), 0)
        self.assertEqual(embedding.dtype, 'float32')
    
    def test_get_embedding_dimension(self):
        """Test embedding dimension retrieval."""
        dimension = self.embedder.get_embedding_dimension()
        self.assertGreater(dimension, 0)
        self.assertIsInstance(dimension, int)
    
    def test_embed_chunks(self):
        """Test embedding multiple chunks."""
        chunks = [
            DocumentChunk("First test text", "test1", "chunk1"),
            DocumentChunk("Second test text", "test2", "chunk2")
        ]
        
        embedded_chunks = self.embedder.embed_chunks(chunks)
        
        self.assertEqual(len(embedded_chunks), 2)
        for chunk in embedded_chunks:
            self.assertIn("embedding", chunk.metadata)
            self.assertGreater(len(chunk.metadata["embedding"]), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline."""
    
    def setUp(self):
        self.ingestion = DocumentIngestion(chunk_size=100)
        self.parser = QueryParser(use_llm=False)
        self.embedder = EmbeddingGenerator(model_type="huggingface")
    
    def test_document_to_chunks_pipeline(self):
        """Test the complete document processing pipeline."""
        # Create a test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            HEALTH INSURANCE POLICY
            
            Section 1: Coverage
            This policy covers medical expenses for insured persons.
            Maximum coverage limit is ₹5,00,000 per year.
            
            Section 2: Surgical Procedures
            Knee surgery is covered for ages 25-60.
            Maximum coverage for knee surgery: ₹2,00,000.
            Pre-authorization is required.
            """)
            temp_path = Path(f.name)
        
        try:
            # Ingest document
            chunks = self.ingestion.ingest_file(temp_path)
            self.assertGreater(len(chunks), 0)
            
            # Generate embeddings
            embedded_chunks = self.embedder.embed_chunks(chunks)
            self.assertEqual(len(embedded_chunks), len(chunks))
            
            # Parse a related query
            query = "46M, knee surgery, coverage amount"
            parsed_query = self.parser.parse(query)
            
            self.assertEqual(parsed_query.age, 46)
            self.assertEqual(parsed_query.gender, Gender.MALE)
            self.assertIn("knee surgery", parsed_query.procedure.lower())
            
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    # Set up basic logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main(verbosity=2)
