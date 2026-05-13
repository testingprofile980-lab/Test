#!/usr/bin/env bash
set -e

echo "=== LinkedIn Job Matcher ==="
echo ""

# Backend setup
echo "[1/4] Setting up Python backend..."
cd backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt -q
echo "     Backend dependencies installed."

# Start backend in background
echo "[2/4] Starting FastAPI backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "     Backend PID: $BACKEND_PID"

cd ..

# Frontend setup
echo "[3/4] Setting up React frontend..."
cd frontend
npm install --silent
echo "     Frontend dependencies installed."

echo "[4/4] Starting React frontend on port 3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== App is starting ==="
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

wait $FRONTEND_PID $BACKEND_PID
