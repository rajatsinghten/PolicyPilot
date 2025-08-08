#!/usr/bin/env python3
"""
Test script to debug LLM connection issues
"""

import asyncio
import json
from app.reasoner import LLMReasoner
from app.parser import ParsedQuery, Gender
from app.ingestion import DocumentChunk

def test_llm_connection():
    """Test the LLM connection directly"""
    try:
        print("1. Creating LLMReasoner...")
        reasoner = LLMReasoner()
        print("✓ LLMReasoner created successfully")
        
        # Create a simple test query
        print("\n2. Creating test query...")
        parsed_query = ParsedQuery(
            original_query="What are the dental coverage benefits?",
            age=30,
            gender=Gender.MALE,
            procedure="dental checkup",
            confidence=0.8
        )
        print("✓ Test query created")
        
        # Create mock retrieved chunks
        print("\n3. Creating mock document chunks...")
        mock_chunks = [
            (DocumentChunk(
                text="Dental coverage includes routine checkups, cleanings, and basic procedures up to ₹10,000 per year.",
                source="Golden Shield Policy",
                chunk_id="test_chunk_1",
                section="Dental Benefits"
            ), 0.9)
        ]
        print("✓ Mock chunks created")
        
        # Create context
        context = "Dental coverage includes routine checkups, cleanings, and basic procedures up to ₹10,000 per year."
        
        print("\n4. Testing LLM analysis...")
        result = reasoner.analyze_claim(parsed_query, mock_chunks, context)
        print("✓ LLM analysis completed")
        
        print(f"\n5. Result: {result.decision.value}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Reasoning: {result.reasoning[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LLM Connection...")
    success = test_llm_connection()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
