# PolicyPilot - AI-Powered Insurance Policy Assistant

A sophisticated full-stack RAG (Retrieval Augmented Generation) system with FastAPI backend and React frontend for intelligent insurance policy analysis and claims processing.

## 🎯 Overview

PolicyPilot is an AI-powered assistant that helps users understand insurance policies, check coverage, and get intelligent answers to policy-related questions. It uses advanced RAG technology with Azure OpenAI for natural language understanding and decision-making.

## ✨ Key Features

🔍 **Intelligent RAG System**: Advanced retrieval with context-aware search  
🧠 **Azure OpenAI Integration**: GPT-4 powered reasoning and analysis  
📄 **Multi-format Document Support**: PDF, DOCX, TXT processing  
🎨 **Beautiful Modern UI**: Glass morphism design with smooth animations  
⚡ **Real-time Chat Interface**: Interactive natural language queries  
📤 **Drag & Drop Upload**: Seamless document upload experience  
📚 **Document Management**: View, manage, and delete uploaded documents  
🛡️ **Insurance-Focused**: Specialized for policy analysis and claims processing  
🔗 **Context-Aware Retrieval**: Includes neighboring chunks for complete context  

## 🏗️ Architecture

```
PolicyPilot/
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── api.py         # FastAPI endpoints
│   │   ├── ingestion.py   # Document processing & chunking
│   │   ├── embedder.py    # Text embeddings (Azure OpenAI/HuggingFace)
│   │   ├── parser.py      # Query parsing & understanding
│   │   ├── retriever.py   # Semantic search with FAISS
│   │   └── reasoner.py    # LLM reasoning & decision making
│   ├── data/
│   │   ├── documents/     # Upload documents here
│   │   └── embeddings/    # Vector storage (auto-generated)
│   ├── config.py          # System configuration
│   ├── main.py            # CLI interface
│   └── requirements.txt   # Python dependencies
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

### Prerequisites
- Python 3.8+
- Node.js 16+
- Azure OpenAI API key (optional, for enhanced reasoning)

### One-Command Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/PolicyPilot.git
cd PolicyPilot

# Install all dependencies and start both services
npm run install
npm run dev
```

This will:
- Set up the Python virtual environment in `backend/`
- Install all Python dependencies
- Install all Node.js dependencies in `frontend/`
- Start both backend (port 8000) and frontend (port 3000)

### Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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
python -m uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

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

## 🔧 Configuration

### Environment Variables (.env)
Create a `.env` file in the `backend/` directory:

```env
# Azure OpenAI Configuration (for enhanced reasoning)
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# RAG Settings
CHUNK_SIZE=500
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.3
```

## 📡 API Endpoints

### Core Endpoints

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
  "query": "What are the dental coverage benefits?",
  "use_llm_reasoning": true,
  "top_k": 5
}
```

**Response Format**:
```json
{
  "decision": "Insufficient Information",
  "confidence": 0.7,
  "reasoning": "The query does not specify the type of dental treatment...",
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
  "recommendations": ["Provide specific details..."],
  "query_understanding": {
    "age": null,
    "gender": null,
    "procedure": "dental treatment"
  },
  "processing_time": 4.2
}
```

#### 3. Upload Document
```http
POST /upload
Content-Type: multipart/form-data

file: [PDF/DOCX/TXT file]
```

#### 4. List Documents
```http
GET /documents
```

#### 5. Delete Document
```http
DELETE /documents/{document_name}
```

## 🎯 Usage Examples

### Query Types
The system can handle various insurance-related queries:

- **Coverage Questions**: "What dental treatments are covered?"
- **Exclusions**: "What are the policy exclusions?"
- **Claims**: "46M, knee surgery, Mumbai, coverage amount?"
- **Benefits**: "What are the maternity benefits?"
- **Waiting Periods**: "What are the waiting periods for pre-existing conditions?"

### Frontend Integration

```javascript
// Process a query with LLM reasoning
async function processQuery(query) {
  const response = await fetch('http://localhost:8000/process', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      use_llm_reasoning: true,
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
```

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

## 🔧 Development

### Backend Development
```bash
cd backend
source venv/bin/activate

# Start with auto-reload
python -m uvicorn app.api:app --reload

# CLI operations
python main.py ingest --path data/documents/
python main.py query --query "your question"
python main.py status
```

### Frontend Development
```bash
cd frontend
npm start          # Start development server
npm run build      # Build for production
npm test           # Run tests
```

## 🎨 UI Features

### Modern Design
- **Glass Morphism**: Semi-transparent containers with backdrop blur
- **Smooth Animations**: Fade-in effects and hover interactions
- **Gradient Backgrounds**: Beautiful purple-blue gradients
- **Responsive Layout**: Works on desktop and mobile

### Interactive Elements
- **Real-time Chat**: Instant message display with typing indicators
- **Document Upload**: Drag & drop with progress feedback
- **Status Indicators**: Live backend connection status
- **Hover Effects**: Enhanced button and input interactions

## 🔒 Security

- **Environment Variables**: API keys stored securely in `.env` files
- **CORS Configuration**: Properly configured for development
- **Input Validation**: File type and size validation
- **Error Handling**: Graceful error responses

## 📊 Performance

- **Document Processing**: ~1-2 seconds per document
- **Query Processing**: ~2-5 seconds per query (with LLM reasoning)
- **Concurrent Requests**: Supported via FastAPI async
- **File Size Limit**: 50MB per document
- **Supported Formats**: PDF, DOCX, TXT

## 🐛 Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Check if backend is running on port 8000
   - Verify virtual environment is activated
   - Check API health at http://localhost:8000/health

2. **LLM Reasoning Not Working**
   - Verify Azure OpenAI credentials in `.env`
   - Check API endpoint and deployment name
   - Ensure sufficient API quota

3. **Document Upload Fails**
   - Check file format (PDF, DOCX, TXT only)
   - Verify file size (max 50MB)
   - Check backend logs for errors

### Error Codes
- `200` - Success
- `400` - Bad Request (invalid query/file)
- `404` - Not Found (no relevant documents)
- `500` - Internal Server Error

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Live Demo**: [Add your demo link]
- **API Documentation**: http://localhost:8000/docs
- **Azure OpenAI**: https://azure.microsoft.com/services/openai/
- **FastAPI**: https://fastapi.tiangolo.com/

---

**Ready to use!** Start with the health check endpoint to verify connectivity, then upload documents and start asking questions about your insurance policies.
