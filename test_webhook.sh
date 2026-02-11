#!/bin/bash

echo "=========================================="
echo "LINE Webhook Debug & Test"
echo "=========================================="
echo ""

# Test 1: Check if server is running
echo "1. Checking if LINE Bot server is running..."
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "   ✓ Server is running on port 5001"
    curl -s http://localhost:5001/health | python -m json.tool
else
    echo "   ✗ Server is NOT running on port 5001"
    echo "   → Start with: python line_webhook_app.py"
    exit 1
fi

echo ""

# Test 2: Check webhook endpoints
echo "2. Testing webhook endpoints..."

# Test default endpoint
echo "   Testing: /webhook/line"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5001/webhook/line)
if [ "$response" = "400" ]; then
    echo "   ✓ /webhook/line exists (400 = missing signature, expected)"
elif [ "$response" = "404" ]; then
    echo "   ✗ /webhook/line NOT FOUND"
else
    echo "   ? /webhook/line returned: $response"
fi

# Test alternative endpoint
echo "   Testing: /webhook-test/line-bot"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5001/webhook-test/line-bot)
if [ "$response" = "400" ]; then
    echo "   ✓ /webhook-test/line-bot exists (400 = missing signature, expected)"
elif [ "$response" = "404" ]; then
    echo "   ✗ /webhook-test/line-bot NOT FOUND"
else
    echo "   ? /webhook-test/line-bot returned: $response"
fi

echo ""

# Test 3: Check ngrok
echo "3. Checking ngrok connection..."
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "   ✓ ngrok is running"
    echo ""
    echo "   Public URLs:"
    curl -s http://localhost:4040/api/tunnels | python -c "
import sys, json
data = json.load(sys.stdin)
for tunnel in data.get('tunnels', []):
    print(f\"   - {tunnel['public_url']} -> {tunnel['config']['addr']}\")
"
else
    echo "   ✗ ngrok is NOT running"
    echo "   → Start with: ngrok http 5001"
fi

echo ""
echo "=========================================="
echo "Next steps:"
echo "=========================================="
echo ""
echo "If server is running but webhook fails:"
echo "1. Check that ngrok forwards to port 5001"
echo "2. Use the HTTPS URL from ngrok"
echo "3. In LINE Console, set webhook URL to:"
echo "   https://your-ngrok-url.ngrok-free.dev/webhook-test/line-bot"
echo ""
echo "To test manually:"
echo "  curl -X POST http://localhost:5001/webhook-test/line-bot"
echo ""
