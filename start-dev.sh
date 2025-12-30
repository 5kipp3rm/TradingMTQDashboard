#!/bin/bash

# TradingMTQ Dashboard Development Setup
echo "🚀 Starting TradingMTQ with React Dashboard..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dashboard dependencies are installed
if [ ! -d "dashboard/node_modules" ]; then
    echo "📦 Installing dashboard dependencies..."
    cd dashboard && yarn install && cd ..
fi

# Start FastAPI backend in background
echo "🔧 Starting FastAPI backend on http://localhost:8000..."
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Start Vite development server using bash to avoid zsh config issues
echo "⚛️  Starting React dashboard on http://localhost:8080..."
cd dashboard && /bin/bash -c "yarn dev" &
FRONTEND_PID=$!

echo ""
echo "✅ TradingMTQ is running!"
echo ""
echo "📊 Dashboard: http://localhost:8080"
echo "🔌 API:       http://localhost:8000/api"
echo "📖 Docs:      http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user interrupt
trap "echo '\n🛑 Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
