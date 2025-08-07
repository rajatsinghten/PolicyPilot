#!/bin/bash

echo "🚀 Starting PolicyPilot Development Environment..."
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to handle cleanup
cleanup() {
    echo -e "\n${RED}Shutting down services...${NC}"
    jobs -p | xargs -r kill
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}❌ Backend virtual environment not found!${NC}"
    echo "Please run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}❌ Frontend dependencies not found!${NC}"
    echo "Please run: cd frontend && npm install"
    exit 1
fi

# Start backend
echo -e "${BLUE}🔧 Starting Backend (FastAPI)...${NC}"
cd backend
source venv/bin/activate
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started at http://localhost:8000${NC}"
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
echo -e "${BLUE}🎨 Starting Frontend (React)...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend will start at http://localhost:3000${NC}"
cd ..

echo ""
echo -e "${GREEN}🎉 Both services are starting up!${NC}"
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend UI: http://localhost:3000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop both services${NC}"

# Wait for background processes
wait
