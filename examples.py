"""
Example usage scripts for PolicyPilot
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from main import PolicyPilot
import config


def example_basic_usage():
    """Demonstrate basic PolicyPilot usage."""
    print("=== PolicyPilot Basic Usage Example ===\n")
    
    # Initialize PolicyPilot (will use HuggingFace embeddings by default)
    pilot = PolicyPilot(use_openai=False, use_llm_reasoning=False)
    
    # Check system status
    status = pilot.get_system_status()
    print("System Status:")
    print(f"  - System Ready: {status['system_ready']}")
    print(f"  - Documents: {status['documents']['total_documents']}")
    print(f"  - Chunks: {status['documents']['total_chunks']}")
    print()
    
    # Ingest sample documents
    print("Ingesting sample documents...")
    try:
        chunks_created = pilot.ingest_documents(config.DOCUMENTS_DIR)
        print(f"Successfully ingested documents: {chunks_created} chunks created\n")
    except Exception as e:
        print(f"Error ingesting documents: {e}\n")
        return
    
    # Test queries
    test_queries = [
        "46M, knee surgery, Pune, 3-month policy",
        "Female patient, 35 years old, heart surgery in Mumbai",
        "Emergency treatment for accident in Delhi",
        "Travel insurance claim for medical emergency abroad"
    ]
    
    print("Processing test queries:\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 50)
        
        try:
            result = pilot.process_query(query)
            
            print(f"Decision: {result['decision']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Reasoning: {result['reasoning'][:200]}...")
            print(f"Retrieved Chunks: {result['retrieved_chunks']}")
            
            if result.get('justification', {}).get('clauses'):
                print("\nRelevant Policy Sections:")
                for j, clause in enumerate(result['justification']['clauses'][:2], 1):
                    print(f"  {j}. {clause['source']} (Score: {clause['relevance_score']:.3f})")
                    print(f"     {clause['text'][:100]}...")
            
        except Exception as e:
            print(f"Error processing query: {e}")
        
        print("\n" + "="*70 + "\n")


def example_with_openai():
    """Demonstrate PolicyPilot with OpenAI features (requires API key)."""
    print("=== PolicyPilot with OpenAI Example ===\n")
    
    if not config.OPENAI_API_KEY:
        print("OpenAI API key not found. This example requires OPENAI_API_KEY environment variable.")
        print("Set it using: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize with OpenAI features
    pilot = PolicyPilot(use_openai=True, use_llm_reasoning=True)
    
    # Ingest documents if needed
    status = pilot.get_system_status()
    if not status['system_ready']:
        print("Ingesting documents...")
        pilot.ingest_documents(config.DOCUMENTS_DIR)
    
    # Test with LLM reasoning
    query = "46 year old male needs knee surgery in Pune, has 3-month policy, claiming ₹1,50,000"
    
    print(f"Query: {query}\n")
    print("Processing with LLM reasoning...\n")
    
    try:
        result = pilot.process_query(query, use_reasoning=True)
        
        print(f"Decision: {result['decision']}")
        if result.get('amount'):
            print(f"Amount: {result['amount']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"\nReasoning:\n{result['reasoning']}")
        
        if result.get('justification', {}).get('clauses'):
            print("\nSupporting Evidence:")
            for i, clause in enumerate(result['justification']['clauses'], 1):
                print(f"{i}. Source: {clause['source']}")
                print(f"   Text: {clause['text']}")
                print(f"   Relevance: {clause['relevance_score']:.3f}\n")
        
        if result.get('recommendations'):
            print("Recommendations:")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"{i}. {rec}")
    
    except Exception as e:
        print(f"Error: {e}")


def example_api_usage():
    """Demonstrate API usage with sample requests."""
    print("=== PolicyPilot API Usage Example ===\n")
    
    print("To start the API server, run:")
    print("  python -m uvicorn app.api:app --reload")
    print("\nThen you can make requests like:")
    print()
    
    # Example curl commands
    curl_examples = [
        {
            "description": "Upload a document",
            "command": 'curl -X POST "http://localhost:8000/upload" -F "file=@data/documents/sample_health_policy.txt"'
        },
        {
            "description": "Process a query",
            "command": '''curl -X POST "http://localhost:8000/process" \\
     -H "Content-Type: application/json" \\
     -d '{"query": "46M, knee surgery, Pune, 3-month policy"}'
'''
        },
        {
            "description": "List documents",
            "command": 'curl "http://localhost:8000/documents"'
        },
        {
            "description": "Search documents",
            "command": 'curl "http://localhost:8000/search/knee%20surgery%20coverage"'
        },
        {
            "description": "Check API health",
            "command": 'curl "http://localhost:8000/health"'
        }
    ]
    
    for example in curl_examples:
        print(f"{example['description']}:")
        print(f"  {example['command']}")
        print()
    
    print("API Documentation: http://localhost:8000/docs")


def example_batch_processing():
    """Demonstrate batch processing of multiple queries."""
    print("=== Batch Processing Example ===\n")
    
    pilot = PolicyPilot(use_openai=False)
    
    # Ensure documents are ingested
    status = pilot.get_system_status()
    if not status['system_ready']:
        print("Ingesting documents...")
        pilot.ingest_documents(config.DOCUMENTS_DIR)
    
    # Batch of queries to process
    batch_queries = [
        "25F, appendectomy, Chennai, emergency claim",
        "55M, heart bypass surgery, Mumbai, ₹4,00,000 claim",
        "30F, maternity benefits, Bangalore, delivery expenses",
        "42M, travel insurance, medical emergency in Thailand",
        "65M, cataract surgery, Delhi, outpatient procedure",
        "28F, dental emergency, Pune, accident-related"
    ]
    
    print(f"Processing {len(batch_queries)} queries in batch:\n")
    
    results = []
    for i, query in enumerate(batch_queries, 1):
        print(f"Processing {i}/{len(batch_queries)}: {query[:50]}...")
        
        try:
            result = pilot.process_query(query)
            results.append({
                "query": query,
                "decision": result["decision"],
                "confidence": result["confidence"],
                "chunks_found": result["retrieved_chunks"]
            })
        except Exception as e:
            results.append({
                "query": query,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70)
    
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    print(f"Successfully processed: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        avg_confidence = sum(r["confidence"] for r in successful) / len(successful)
        print(f"Average confidence: {avg_confidence:.2f}")
        
        print("\nResults:")
        for result in successful:
            print(f"  {result['query'][:40]}... -> {result['decision']} ({result['confidence']:.2f})")
    
    if failed:
        print("\nFailed queries:")
        for result in failed:
            print(f"  {result['query'][:40]}... -> Error: {result['error']}")


def main():
    """Main function to run examples."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PolicyPilot Examples")
    parser.add_argument(
        "example", 
        choices=["basic", "openai", "api", "batch"],
        help="Example to run"
    )
    
    args = parser.parse_args()
    
    if args.example == "basic":
        example_basic_usage()
    elif args.example == "openai":
        example_with_openai()
    elif args.example == "api":
        example_api_usage()
    elif args.example == "batch":
        example_batch_processing()


if __name__ == "__main__":
    main()
