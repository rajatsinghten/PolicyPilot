# PolicyPilot - LLM-Powered Document Processing System

An intelligent document processing system that uses Large Language Models to analyze insurance policies, contracts, and other documents to provide automated decision-making and information retrieval.

## 🚀 Features

- **Document Ingestion**: Supports PDF, DOCX, and email files (.eml/.msg)
- **Intelligent Chunking**: Splits documents into overlapping chunks for better context
- **Semantic Search**: Uses embeddings and FAISS for efficient similarity search
- **Query Understanding**: Parses natural language queries and extracts structured data
- **LLM Reasoning**: Uses GPT-4 for intelligent decision making with justifications
- **REST API**: FastAPI endpoint for easy integration

## 📁 Project Structure

```
PolicyPilot/
├── app/
│   ├── __init__.py
│   ├── ingestion.py       # Document loading and processing
│   ├── embedder.py        # Text embedding generation
│   ├── parser.py          # Query parsing and structuring
│   ├── retriever.py       # Semantic search and retrieval
│   ├── reasoner.py        # LLM-based reasoning and decision making
│   └── api.py             # FastAPI endpoints
├── data/                  # Sample documents and storage
│   ├── documents/         # Input documents
│   └── embeddings/        # Stored embeddings and indices
├── tests/                 # Unit tests
├── main.py                # Main orchestration script
├── requirements.txt       # Python dependencies
├── config.py             # Configuration settings
└── README.md             # This file
```

## 🛠️ Installation

1. Clone the repository and navigate to the project directory
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

## 🚀 Quick Start

1. **Ingest Documents**:
   ```python
   from app.ingestion import DocumentIngestion
   
   ingestion = DocumentIngestion()
   ingestion.ingest_directory("data/documents/")
   ```

2. **Query Processing**:
   ```python
   from main import PolicyPilot
   
   pilot = PolicyPilot()
   result = pilot.process_query("46M, knee surgery, Pune, 3-month policy")
   print(result)
   ```

3. **API Server**:
   ```bash
   python -m uvicorn app.api:app --reload
   ```
   Then visit `http://localhost:8000/docs` for the interactive API documentation.

## 📝 API Usage

### Process Query
```bash
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{"query": "46M, knee surgery, Pune, 3-month policy"}'
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@policy.pdf"
```

## 🔧 Configuration

Modify `config.py` to customize:
- OpenAI model settings
- Embedding dimensions
- Chunk sizes and overlap
- FAISS index parameters

## 📊 Example Response

```json
{
  "decision": "Approved",
  "amount": "₹1,50,000",
  "confidence": 0.85,
  "justification": {
    "clauses": [
      {
        "text": "Knee surgery is covered under Section 2.1 for males aged 40-50",
        "source": "PolicyDoc.pdf - Section 2.1",
        "relevance_score": 0.92
      }
    ]
  },
  "query_understanding": {
    "age": 46,
    "gender": "Male",
    "procedure": "knee surgery",
    "location": "Pune",
    "policy_duration": "3 months"
  }
}
```

## 🧪 Testing

Run tests with:
```bash
python -m pytest tests/
```

## 📄 License

MIT License
