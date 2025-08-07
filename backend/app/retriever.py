"""
Semantic Retrieval Module

Handles semantic search and retrieval of relevant document chunks using
vector similarity search with FAISS.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pickle
from pathlib import Path

import faiss
from loguru import logger

import config
from app.ingestion import DocumentChunk
from app.embedder import EmbeddingGenerator
from app.parser import ParsedQuery


class SemanticRetriever:
    """Handles semantic search and retrieval using FAISS."""
    
    def __init__(
        self, 
        embedding_generator: EmbeddingGenerator,
        index_path: Optional[Path] = None
    ):
        """
        Initialize the semantic retriever.
        
        Args:
            embedding_generator: EmbeddingGenerator instance
            index_path: Path to save/load FAISS index
        """
        self.embedding_generator = embedding_generator
        self.index_path = index_path or (config.EMBEDDINGS_DIR / "faiss_index.bin")
        self.metadata_path = self.index_path.parent / "chunk_metadata.pkl"
        
        self.index = None
        self.chunks = []
        self.embedding_dimension = embedding_generator.get_embedding_dimension()
        
        logger.info(f"Initialized SemanticRetriever with embedding dimension: {self.embedding_dimension}")
    
    def create_index(self, chunks: List[DocumentChunk]) -> None:
        """
        Create a FAISS index from document chunks.
        
        Args:
            chunks: List of DocumentChunk objects with embeddings
        """
        if not chunks:
            logger.warning("No chunks provided for index creation")
            return
        
        # Filter chunks that have embeddings
        embedded_chunks = [
            chunk for chunk in chunks 
            if "embedding" in chunk.metadata and len(chunk.metadata["embedding"]) > 0
        ]
        
        if not embedded_chunks:
            logger.warning("No embedded chunks found")
            return
        
        # Extract embeddings
        embeddings = np.vstack([
            chunk.metadata["embedding"] for chunk in embedded_chunks
        ]).astype(np.float32)
        
        # Create FAISS index
        if config.FAISS_INDEX_TYPE == "IndexFlatIP":
            # Inner Product (cosine similarity for normalized vectors)
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
        elif config.FAISS_INDEX_TYPE == "IndexFlatL2":
            # L2 distance
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
        else:
            # Default to Inner Product
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Store chunks for metadata retrieval
        self.chunks = embedded_chunks
        
        logger.info(f"Created FAISS index with {len(embedded_chunks)} chunks")
    
    def save_index(self) -> None:
        """Save the FAISS index and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save chunk metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            
            logger.info(f"Saved index to {self.index_path} and metadata to {self.metadata_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def load_index(self) -> bool:
        """
        Load the FAISS index and metadata from disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.index_path.exists() or not self.metadata_path.exists():
                logger.warning("Index files not found")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load chunk metadata
            with open(self.metadata_path, 'rb') as f:
                self.chunks = pickle.load(f)
            
            logger.info(f"Loaded index with {len(self.chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def search(
        self, 
        query: str, 
        top_k: int = config.TOP_K_RESULTS,
        threshold: float = config.SIMILARITY_THRESHOLD,
        include_neighbors: bool = True,
        neighbor_range: int = 1
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform semantic search for a query.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            include_neighbors: Whether to include neighboring chunks
            neighbor_range: Number of neighboring chunks to include on each side (+-n)
            
        Returns:
            List of (DocumentChunk, similarity_score) tuples
        """
        if self.index is None:
            logger.error("Index not initialized. Call create_index() or load_index() first.")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        if len(query_embedding) == 0:
            logger.error("Failed to generate query embedding")
            return []
        
        # Normalize query embedding for cosine similarity
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)
        
        # Perform search with a larger top_k to have room for neighbor inclusion
        search_k = min(top_k * 3, len(self.chunks))  # Search more initially
        similarities, indices = self.index.search(query_embedding, search_k)
        
        # Filter initial results by threshold
        initial_results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if similarity >= threshold and idx < len(self.chunks):
                chunk = self.chunks[idx]
                initial_results.append((chunk, float(similarity), idx))
        
        if not include_neighbors:
            # Return original results without neighbors
            return [(chunk, score) for chunk, score, _ in initial_results[:top_k]]
        
        # Find neighboring chunks and add them
        enhanced_results = []
        used_chunk_ids = set()
        
        for chunk, original_score, original_idx in initial_results:
            if chunk.chunk_id in used_chunk_ids:
                continue
                
            # Add the original chunk
            enhanced_results.append((chunk, original_score))
            used_chunk_ids.add(chunk.chunk_id)
            
            # Find and add neighboring chunks
            neighbors = self._find_neighboring_chunks(chunk, neighbor_range)
            for neighbor_chunk in neighbors:
                if neighbor_chunk.chunk_id not in used_chunk_ids:
                    # Give neighbors a slightly lower score than the original
                    neighbor_score = original_score * 0.8  # 80% of original score
                    enhanced_results.append((neighbor_chunk, neighbor_score))
                    used_chunk_ids.add(neighbor_chunk.chunk_id)
            
            # Stop if we have enough results
            if len(enhanced_results) >= top_k:
                break
        
        # Sort by score and limit to top_k
        enhanced_results.sort(key=lambda x: x[1], reverse=True)
        final_results = enhanced_results[:top_k]
        
        logger.info(f"Found {len(initial_results)} direct matches, expanded to {len(final_results)} with neighbors")
        return final_results
    
    def _find_neighboring_chunks(
        self, 
        target_chunk: DocumentChunk, 
        neighbor_range: int = 1
    ) -> List[DocumentChunk]:
        """
        Find neighboring chunks based on chunk_id sequence.
        
        Args:
            target_chunk: The chunk to find neighbors for
            neighbor_range: Number of neighbors to find on each side
            
        Returns:
            List of neighboring DocumentChunk objects
        """
        neighbors = []
        
        # Parse the chunk ID to extract the counter
        # Format: {source}_chunk_{counter}
        try:
            chunk_id_parts = target_chunk.chunk_id.rsplit('_', 1)
            if len(chunk_id_parts) != 2:
                return neighbors
                
            base_id = chunk_id_parts[0]
            chunk_number = int(chunk_id_parts[1])
            
            # Find neighboring chunks
            for offset in range(-neighbor_range, neighbor_range + 1):
                if offset == 0:
                    continue  # Skip the original chunk
                
                neighbor_number = chunk_number + offset
                if neighbor_number < 0:
                    continue  # Skip negative indices
                
                neighbor_id = f"{base_id}_{neighbor_number}"
                
                # Find chunk with this ID
                for chunk in self.chunks:
                    if chunk.chunk_id == neighbor_id:
                        neighbors.append(chunk)
                        break
                        
        except (ValueError, IndexError) as e:
            logger.debug(f"Could not parse chunk ID {target_chunk.chunk_id}: {e}")
        
        return neighbors
    
    def search_parsed_query(
        self, 
        parsed_query: ParsedQuery,
        top_k: int = config.TOP_K_RESULTS,
        threshold: float = config.SIMILARITY_THRESHOLD,
        include_neighbors: bool = True,
        neighbor_range: int = 1
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform semantic search using a parsed query.
        
        Args:
            parsed_query: ParsedQuery object
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            include_neighbors: Whether to include neighboring chunks
            neighbor_range: Number of neighboring chunks to include on each side
            
        Returns:
            List of (DocumentChunk, similarity_score) tuples
        """
        # Create enhanced query string
        query_components = []
        
        if parsed_query.procedure:
            query_components.append(parsed_query.procedure)
        
        if parsed_query.medical_condition:
            query_components.append(parsed_query.medical_condition)
        
        if parsed_query.age:
            query_components.append(f"age {parsed_query.age}")
        
        if parsed_query.gender:
            query_components.append(parsed_query.gender.value.lower())
        
        if parsed_query.location:
            query_components.append(parsed_query.location)
        
        # Fallback to original query if no structured components
        if not query_components:
            enhanced_query = parsed_query.original_query
        else:
            enhanced_query = " ".join(query_components)
        
        logger.info(f"Searching with enhanced query: {enhanced_query}")
        return self.search(enhanced_query, top_k, threshold, include_neighbors, neighbor_range)
    
    def get_context_window(
        self, 
        results: List[Tuple[DocumentChunk, float]],
        max_tokens: int = 2000
    ) -> str:
        """
        Create a context window from search results.
        
        Args:
            results: List of (DocumentChunk, similarity_score) tuples
            max_tokens: Maximum tokens in context window
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = []
        current_tokens = 0
        
        for i, (chunk, score) in enumerate(results):
            # Estimate tokens in chunk
            chunk_tokens = len(chunk.text) // 4  # Rough approximation
            
            if current_tokens + chunk_tokens > max_tokens and context_parts:
                break
            
            # Format chunk with metadata
            chunk_context = f"""
Source: {chunk.source}
Relevance Score: {score:.3f}
{chunk.section or ""}

{chunk.text}
---
"""
            context_parts.append(chunk_context)
            current_tokens += chunk_tokens
        
        context = "\n".join(context_parts)
        logger.info(f"Created context window with {len(context_parts)} chunks, ~{current_tokens} tokens")
        
        return context
    
    def explain_results(self, results: List[Tuple[DocumentChunk, float]]) -> Dict[str, Any]:
        """
        Provide explanation for search results.
        
        Args:
            results: List of (DocumentChunk, similarity_score) tuples
            
        Returns:
            Dictionary with result explanations
        """
        if not results:
            return {"explanation": "No relevant results found"}
        
        explanation = {
            "total_results": len(results),
            "top_score": results[0][1] if results else 0.0,
            "sources": list(set(chunk.source for chunk, _ in results)),
            "average_score": sum(score for _, score in results) / len(results),
            "results_breakdown": []
        }
        
        for chunk, score in results:
            explanation["results_breakdown"].append({
                "source": chunk.source,
                "section": chunk.section,
                "score": score,
                "text_preview": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text
            })
        
        return explanation


class HybridRetriever(SemanticRetriever):
    """Enhanced retriever that combines semantic and keyword-based search."""
    
    def __init__(self, embedding_generator: EmbeddingGenerator, index_path: Optional[Path] = None):
        super().__init__(embedding_generator, index_path)
        self.keyword_index = {}  # Simple keyword index
    
    def build_keyword_index(self):
        """Build a simple keyword index for fallback searches."""
        self.keyword_index = {}
        
        for i, chunk in enumerate(self.chunks):
            words = chunk.text.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    if word not in self.keyword_index:
                        self.keyword_index[word] = []
                    self.keyword_index[word].append(i)
        
        logger.info(f"Built keyword index with {len(self.keyword_index)} terms")
    
    def keyword_search(self, query: str, top_k: int = config.TOP_K_RESULTS) -> List[Tuple[DocumentChunk, float]]:
        """
        Perform keyword-based search as fallback.
        
        Args:
            query: Query string
            top_k: Number of top results to return
            
        Returns:
            List of (DocumentChunk, score) tuples
        """
        if not self.keyword_index:
            self.build_keyword_index()
        
        query_words = query.lower().split()
        chunk_scores = {}
        
        for word in query_words:
            if word in self.keyword_index:
                for chunk_idx in self.keyword_index[word]:
                    if chunk_idx not in chunk_scores:
                        chunk_scores[chunk_idx] = 0
                    chunk_scores[chunk_idx] += 1
        
        # Sort by score and return top results
        sorted_results = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for chunk_idx, score in sorted_results[:top_k]:
            if chunk_idx < len(self.chunks):
                normalized_score = score / len(query_words)  # Normalize by query length
                results.append((self.chunks[chunk_idx], normalized_score))
        
        return results


# Example usage
if __name__ == "__main__":
    from app.embedder import EmbeddingGenerator, EmbeddingStorage
    from app.parser import QueryParser
    
    # Initialize components
    embedder = EmbeddingGenerator(model_type="huggingface")
    retriever = SemanticRetriever(embedder)
    parser = QueryParser(use_llm=False)
    storage = EmbeddingStorage()
    
    # Load existing embeddings or create new ones
    chunks = storage.load_embeddings()
    
    if chunks:
        # Create index
        retriever.create_index(chunks)
        
        # Test search
        test_query = "knee surgery for 46 year old male"
        parsed_query = parser.parse(test_query)
        
        print(f"Query: {test_query}")
        print(f"Parsed: {parsed_query.to_dict()}")
        
        results = retriever.search_parsed_query(parsed_query)
        
        print(f"\nFound {len(results)} results:")
        for chunk, score in results:
            print(f"Score: {score:.3f} | Source: {chunk.source}")
            print(f"Text: {chunk.text[:200]}...")
            print("---")
    else:
        print("No embedded chunks found. Run embedder first.")
