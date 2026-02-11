#!/bin/bash

# QuickChat ID - Web Frontend Startup Script
# This script starts both Backend API and Frontend

echo "============================================================"
echo "🚀 QuickChat ID - Web Frontend Startup"
echo "============================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use osascript to open new Terminal windows

    echo "📱 Starting Backend API..."
    osascript -e 'tell application "Terminal" to do script "cd '$(pwd)' && python web_api_app.py"'

    echo "⏳ Waiting 3 seconds for backend to start..."
    sleep 3

    echo "🌐 Starting Frontend..."
    osascript -e 'tell application "Terminal" to do script "cd '$(pwd)'/frontend && npm run dev"'

    echo ""
    echo "✅ Services starting in separate Terminal windows!"
    echo ""
    echo "📡 Backend API: http://localhost:5001"
    echo "🌐 Frontend: http://localhost:5173"
    echo ""
    echo "Open your browser to http://localhost:5173"
    echo ""
else
    # Linux/Other - use simple background processes

    echo "📱 Starting Backend API..."
    python web_api_app.py > logs/web_api.log 2>&1 &
    BACKEND_PID=$!
    echo "   PID: $BACKEND_PID"

    echo "⏳ Waiting 3 seconds for backend to start..."
    sleep 3

    echo "🌐 Starting Frontend..."
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   PID: $FRONTEND_PID"
    cd ..

    echo ""
    echo "✅ Services started!"
    echo ""
    echo "📡 Backend API: http://localhost:5001 (PID: $BACKEND_PID)"
    echo "🌐 Frontend: http://localhost:5173 (PID: $FRONTEND_PID)"
    echo ""
    echo "📝 Logs:"
    echo "   Backend: logs/web_api.log"
    echo "   Frontend: logs/frontend.log"
    echo ""
    echo "To stop services:"
    echo "   kill $BACKEND_PID $FRONTEND_PID"
    echo ""
fi

echo "============================================================"
