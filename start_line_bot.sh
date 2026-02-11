#!/bin/bash

# QuickChat ID LINE Bot Startup Script

echo "=========================================="
echo "QuickChat ID LINE Bot"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "agents/kyc_orchestrator/.env" ]; then
    echo "❌ Error: agents/kyc_orchestrator/.env not found"
    echo "Please create .env file with LINE credentials:"
    echo "  LINE_CHANNEL_ACCESS_TOKEN=your_token"
    echo "  LINE_CHANNEL_SECRET=your_secret"
    exit 1
fi

# Check if LINE credentials exist
if ! grep -q "LINE_CHANNEL_ACCESS_TOKEN" agents/kyc_orchestrator/.env; then
    echo "❌ Error: LINE_CHANNEL_ACCESS_TOKEN not found in .env"
    exit 1
fi

if ! grep -q "LINE_CHANNEL_SECRET" agents/kyc_orchestrator/.env; then
    echo "❌ Error: LINE_CHANNEL_SECRET not found in .env"
    exit 1
fi

echo "✓ LINE credentials found"
echo ""

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip install flask line-bot-sdk
fi

echo "✓ Dependencies installed"
echo ""

# Check if ngrok is available
if command -v ngrok &> /dev/null; then
    echo "✓ ngrok is installed"
    echo ""
    echo "📱 To expose your local server:"
    echo "   1. Run this script to start the server"
    echo "   2. In another terminal, run: ngrok http 5001"
    echo "   3. Copy the https URL from ngrok"
    echo "   4. Set it as webhook URL in LINE Developer Console"
else
    echo "⚠️  ngrok not found"
    echo "   Install ngrok for local testing:"
    echo "   - macOS: brew install ngrok"
    echo "   - Other: https://ngrok.com/download"
    echo ""
    echo "   Or deploy to a server with HTTPS"
fi

echo ""
echo "=========================================="
echo "Starting LINE Bot Server..."
echo "=========================================="
echo ""

# Start the LINE bot server
python line_webhook_app.py
