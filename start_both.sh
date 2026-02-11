#!/bin/bash

# Script to start both LINE Bot and Web Frontend

echo "============================================================"
echo "🚀 Starting QuickChat ID - Both Channels"
echo "============================================================"
echo ""

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Starting LINE Bot (port 5001)..."
    osascript -e 'tell application "Terminal" to do script "cd '$(pwd)' && python line_webhook_app.py"'

    echo "⏳ Waiting 2 seconds..."
    sleep 2

    echo "🌐 Starting Web API (port 5003)..."
    osascript -e 'tell application "Terminal" to do script "cd '$(pwd)' && PORT=5003 python web_api_app.py"'

    echo "⏳ Waiting 2 seconds..."
    sleep 2

    echo "🎨 Starting Frontend..."
    osascript -e 'tell application "Terminal" to do script "cd '$(pwd)'/frontend && npm run dev"'

    echo ""
    echo "✅ All services starting in separate Terminal windows!"
    echo ""
    echo "📡 LINE Bot: http://localhost:5001"
    echo "🌐 Web API: http://localhost:5003"
    echo "🎨 Frontend: http://localhost:5173"
    echo ""
else
    echo "📱 Starting LINE Bot..."
    python line_webhook_app.py > logs/line_bot.log 2>&1 &
    LINE_PID=$!

    echo "⏳ Waiting 2 seconds..."
    sleep 2

    echo "🌐 Starting Web API..."
    PORT=5003 python web_api_app.py > logs/web_api.log 2>&1 &
    WEB_PID=$!

    echo "⏳ Waiting 2 seconds..."
    sleep 2

    echo "🎨 Starting Frontend..."
    cd frontend && npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..

    echo ""
    echo "✅ All services started!"
    echo ""
    echo "📡 LINE Bot: http://localhost:5001 (PID: $LINE_PID)"
    echo "🌐 Web API: http://localhost:5003 (PID: $WEB_PID)"
    echo "🎨 Frontend: http://localhost:5173 (PID: $FRONTEND_PID)"
    echo ""
    echo "To stop:"
    echo "  kill $LINE_PID $WEB_PID $FRONTEND_PID"
fi

echo "============================================================"
