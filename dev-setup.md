# PolicyPilot Development Setup

## Development Environment Status
✅ Backend: Python virtual environment with FastAPI
✅ Frontend: React with TypeScript
✅ Integration: Proxy configured for seamless communication

## Quick Commands

### Start Everything
```bash
./start-dev.sh
# or
npm run dev
```

### Individual Services
```bash
npm run backend    # Backend only (port 8000)
npm run frontend   # Frontend only (port 3000)
```

### Environment Setup
- Backend: `backend/venv/` virtual environment
- Frontend: Node.js dependencies in `frontend/node_modules/`
- Environment variables: `backend/.env`

### API Integration
- Frontend proxy: Configured to forward API calls to `http://localhost:8000`
- Backend CORS: Enabled for frontend development
- Communication: Frontend uses axios for API calls

## Troubleshooting

### Backend Issues
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -c "import sys; print(sys.executable)"  # Verify Python path
```

### Frontend Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port Conflicts
- Backend: Change port in start script (default: 8000)
- Frontend: Change port with `PORT=3001 npm start` (default: 3000)

## File Structure
- Backend code: `backend/app/`
- Frontend components: `frontend/src/components/`
- Documents: `backend/data/documents/`
- Vector storage: `backend/data/embeddings/`
