#!/bin/bash

echo "🚀 Starting RivaFlow Web App..."
echo ""

# Check if dependencies are installed
if [ ! -d "web/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd web && npm install && cd ..
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $API_PID $WEB_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start FastAPI backend
echo "🔧 Starting FastAPI backend on http://localhost:8000..."
python -m uvicorn rivaflow.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start
sleep 2

# Start Vite frontend
echo "⚛️  Starting React frontend on http://localhost:5173..."
cd web && npm run dev &
WEB_PID=$!
cd ..

echo ""
echo "✅ RivaFlow is running!"
echo ""
echo "   🌐 Web App: http://localhost:5173"
echo "   📡 API: http://localhost:8000"
echo "   📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait
