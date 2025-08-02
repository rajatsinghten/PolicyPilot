#!/usr/bin/env python3
"""
Setup script for PolicyPilot
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Command: {command}")
        print(f"  Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✓ Python version {sys.version.split()[0]} is compatible")
    return True


def setup_virtual_environment():
    """Set up virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    print("\n📦 Setting up virtual environment...")
    
    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    print("✓ Virtual environment created")
    print("\nTo activate the virtual environment:")
    print("  On macOS/Linux: source venv/bin/activate")
    print("  On Windows: venv\\Scripts\\activate")
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\n📚 Installing dependencies...")
    
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            print("Please activate virtual environment and run setup again")
            return False
    
    # Install requirements
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    print("✓ All dependencies installed successfully")
    return True


def setup_environment_file():
    """Create .env file template."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    print("\n🔧 Creating environment configuration...")
    
    env_template = """# PolicyPilot Environment Configuration

# OpenAI API Key (required for LLM reasoning and OpenAI embeddings)
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Override default configurations
# OPENAI_MODEL=gpt-4
# EMBEDDING_MODEL=text-embedding-ada-002
# CHUNK_SIZE=500
# CHUNK_OVERLAP=50
# TOP_K_RESULTS=5

# API Configuration
# API_HOST=0.0.0.0
# API_PORT=8000

# Logging
# LOG_LEVEL=INFO
"""
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print("✓ Created .env file template")
    print("📝 Please edit .env file and add your OpenAI API key")
    return True


def run_basic_tests():
    """Run basic tests to verify installation."""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test imports
        print("Testing imports...")
        import numpy
        import sentence_transformers
        import faiss
        import fastapi
        print("✓ All required packages imported successfully")
        
        # Test basic functionality
        print("Testing basic functionality...")
        from app.ingestion import DocumentIngestion
        from app.embedder import EmbeddingGenerator
        from app.parser import QueryParser
        
        # Test document ingestion
        ingestion = DocumentIngestion()
        print("✓ Document ingestion module loaded")
        
        # Test embedder (HuggingFace)
        embedder = EmbeddingGenerator(model_type="huggingface")
        test_embedding = embedder.generate_embedding("test text")
        print(f"✓ Embedding generation working (dimension: {len(test_embedding)})")
        
        # Test parser
        parser = QueryParser(use_llm=False)
        parsed = parser.parse("46M, knee surgery, Pune")
        print(f"✓ Query parsing working (age: {parsed.age}, gender: {parsed.gender})")
        
        return True
        
    except Exception as e:
        print(f"✗ Tests failed: {e}")
        return False


def setup_sample_data():
    """Set up sample data if needed."""
    documents_dir = Path("data/documents")
    
    if not documents_dir.exists():
        print("\n📁 Creating data directories...")
        documents_dir.mkdir(parents=True, exist_ok=True)
        Path("data/embeddings").mkdir(exist_ok=True)
    
    # Check if sample documents exist
    sample_files = list(documents_dir.glob("*.txt"))
    if sample_files:
        print(f"✓ Found {len(sample_files)} sample documents")
    else:
        print("ℹ️  No sample documents found in data/documents/")
        print("   You can add your own PDF, DOCX, or TXT files to get started")
    
    return True


def main():
    """Main setup function."""
    print("🚀 PolicyPilot Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Setup virtual environment
    if not setup_virtual_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup environment file
    if not setup_environment_file():
        return False
    
    # Setup sample data
    if not setup_sample_data():
        return False
    
    # Run basic tests
    if not run_basic_tests():
        print("\n⚠️  Setup completed but tests failed")
        print("   You may need to activate virtual environment or install dependencies manually")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 PolicyPilot setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Add documents to data/documents/ directory")
    print("3. Run: python main.py ingest --path data/documents/")
    print("4. Run: python main.py query --query 'your query here'")
    print("5. Or start API: python -m uvicorn app.api:app --reload")
    print("\n📖 See README.md for detailed usage instructions")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
