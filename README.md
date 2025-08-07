# PolicyPilot - AI-Powered Insurance Policy Assistant

A complete full-stack RAG (Retrieval Augmented Generation) system with FastAPI backend and React frontend for processing insurance documents and answering policy-related queries using AI.

## 🏗️ Project Structure

```
PolicyPilot/
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── api.py         # FastAPI endpoints
│   │   ├── ingestion.py   # Document processing
│   │   ├── embedder.py    # Text embeddings
│   │   ├── parser.py      # Query parsing
│   │   ├── retriever.py   # Semantic search
│   │   └── reasoner.py    # LLM reasoning
│   ├── data/
│   │   ├── documents/     # Upload documents here
│   │   └── embeddings/    # Vector storage
│   ├── venv/              # Python virtual environment
│   ├── config.py          # System configuration
│   ├── main.py            # CLI interface
│   ├── requirements.txt   # Python dependencies
│   └── .env               # Environment variables
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.tsx        # Main App component
│   │   └── index.tsx      # Entry point
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── tsconfig.json      # TypeScript config
├── start-dev.sh           # Development startup script
└── package.json           # Root package.json
```

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)
```bash
# Install all dependencies and start both services
npm run install
npm run dev
```

This will:
- Set up the Python virtual environment in `backend/`
- Install all Python dependencies
- Install all Node.js dependencies in `frontend/`
- Start both backend (port 8000) and frontend (port 3000)

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

#### Start Services
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

## 🌐 Access the Application

After starting:
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 Available Scripts

From the root directory:
```bash
npm run dev              # Start both backend and frontend
npm run backend          # Start only backend
npm run frontend         # Start only frontend
npm run backend:install  # Install Python dependencies
npm run frontend:install # Install Node.js dependencies
npm run install          # Install all dependencies
npm run frontend:build   # Build frontend for production
npm run clean            # Clean all dependencies and cache
```

## 📡 API Endpoints

### Core Endpoints for Frontend Integration

#### 1. Health Check
```http
GET /health
```
Returns system status and component availability.

#### 2. Process Query (Main RAG Endpoint)
```http
POST /process
Content-Type: application/json

{
  "query": "What are the exclusions in health insurance?",
  "top_k": 5,
  "use_llm_reasoning": false
}
```

**Response Format**:
```json
{
  "decision": "Pending",
  "confidence": 0.7,
  "reasoning": "Found relevant policy information...",
  "justification": {
    "clauses": [
      {
        "text": "Policy clause text...",
        "source": "Document.pdf",
        "section": "Section 2.1",
        "relevance_score": 0.85
      }
    ]
  },
  "recommendations": ["Manual review recommended"],
  "query_understanding": {
    "age": 46,
    "gender": "Male",
    "procedure": "knee surgery"
  },
  "processing_time": 2.5
}
```

#### 3. Document Search
```http
GET /search/{query}?top_k=5
```
Direct document search without reasoning.

#### 4. Upload Document
```http
POST /upload
Content-Type: multipart/form-data

file: [PDF/DOCX/TXT file]
```

#### 5. List Documents
```http
GET /documents
```
Returns all uploaded documents and their statistics.

#### 6. Delete Document
```http
DELETE /documents/{document_name}
```

## 🎯 Frontend Integration Examples

### JavaScript/TypeScript

```javascript
// Process a query
async function processQuery(query) {
  const response = await fetch('http://localhost:8000/process', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      use_llm_reasoning: false,
      top_k: 5
    })
  });
  return await response.json();
}

// Upload a document
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/upload', {
    method: 'POST',
    body: formData
  });
  return await response.json();
}

// Get system health
async function getHealth() {
  const response = await fetch('http://localhost:8000/health');
  return await response.json();
}
```

### React Hook Example

```tsx
import { useState } from 'react';

interface QueryResult {
  decision: string;
  confidence: number;
  reasoning: string;
  justification: {
    clauses: Array<{
      text: string;
      source: string;
      relevance_score: number;
    }>;
  };
  processing_time: number;
}

export const usePolicyPilot = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  
  const processQuery = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query, 
          use_llm_reasoning: false,
          top_k: 5 
        })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Query processing failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return { processQuery, loading, result };
};
```

## 📋 Query Examples

The system can handle various types of insurance queries:

- **Coverage Questions**: "What dental treatments are covered?"
- **Exclusions**: "What are the policy exclusions?"
- **Claims**: "46M, knee surgery, Mumbai, coverage amount?"
- **Benefits**: "What are the maternity benefits?"
- **Waiting Periods**: "What are the waiting periods for pre-existing conditions?"

## 🔧 Configuration

### Environment Variables (.env)
```env
# Optional: OpenAI API Key for enhanced reasoning
OPENAI_API_KEY=your-openai-api-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# RAG Settings
CHUNK_SIZE=500
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.3
```

## � Project Structure

```
PolicyPilot/
├── app/
│   ├── api.py              # FastAPI endpoints
│   ├── ingestion.py        # Document processing
│   ├── embedder.py         # Text embeddings
│   ├── parser.py           # Query parsing
│   ├── retriever.py        # Semantic search
│   └── reasoner.py         # LLM reasoning
├── data/
│   ├── documents/          # Upload documents here
│   └── embeddings/         # Vector storage (auto-generated)
├── config.py               # System configuration
├── main.py                 # CLI interface
└── requirements.txt        # Python dependencies
```

## � Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid query/file)
- `404` - Not Found (no relevant documents)
- `429` - Rate Limit Exceeded (OpenAI quota)
- `500` - Internal Server Error

Example error response:
```json
{
  "detail": "No relevant information found for the query"
}
```

## 🔄 CORS Configuration

The API is configured with CORS enabled for frontend development:

```python
# Already configured in app/api.py
allow_origins=["*"]
allow_methods=["*"]
allow_headers=["*"]
```

For production, update CORS settings to specific domains.

## � Performance Notes

- **Document Processing**: ~1-2 seconds per document
- **Query Processing**: ~2-5 seconds per query
- **Concurrent Requests**: Supported via FastAPI async
- **File Size Limit**: 50MB per document
- **Supported Formats**: PDF, DOCX, TXT

## �️ Development Commands

```bash
# Start development server with auto-reload
python -m uvicorn app.api:app --reload

# Process documents via CLI
python main.py ingest --path data/documents/

# Test query via CLI
python main.py query --query "your question"

# Check system status
python main.py status
```

## 🔗 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **OpenAI Documentation**: https://platform.openai.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

## 📞 Support

For API issues or integration questions, check the `/health` endpoint first to verify system status.

---

**Ready to integrate!** Start with the `/health` endpoint to test connectivity, then use `/process` for your main RAG queries.
