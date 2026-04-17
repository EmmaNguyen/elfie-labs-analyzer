#!/bin/bash
# Start both backend and frontend servers

echo "🚀 Starting Elfie AI Labs Analyzer..."

# Stop existing servers
echo "🛑 Stopping existing servers..."
pkill -9 -f "python main.py" 2>/dev/null
pkill -9 -f "next" 2>/dev/null
lsof -ti:3000,8000 | xargs kill -9 2>/dev/null
sleep 2

# Start backend
echo "🔧 Starting backend on port 8000..."
cd /Users/emma/CascadeProjects/elfie-labs-analyzer/backend
source .venv/bin/activate

# Load API key from .env.local
if [ -f "../.env.local" ]; then
    export $(grep -v '^#' ../.env.local | xargs)
    echo "✅ Loaded environment from .env.local"
else
    echo "❌ .env.local not found!"
    exit 1
fi

nohup python main.py > /tmp/backend.log 2>&1 &
sleep 3

# Verify backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start. Check /tmp/backend.log"
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend on port 3000..."
cd /Users/emma/CascadeProjects/elfie-labs-analyzer
nohup npm run dev > /tmp/frontend.log 2>&1 &
sleep 4

echo ""
echo "✨ Servers started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend:  http://localhost:8000"
echo ""
echo "📝 Logs:"
echo "  Backend: tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 To stop all servers:"
echo "  pkill -9 -f 'python main.py'"
echo "  pkill -9 -f 'next'"
echo "  lsof -ti:3000,8000 | xargs kill -9"
