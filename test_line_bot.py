"""Quick test for LINE Bot setup"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('agents/kyc_orchestrator/.env')

print("=" * 60)
print("LINE Bot Setup Test")
print("=" * 60)

# Check LINE credentials
print("\n1. Checking LINE credentials:")
token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
secret = os.getenv('LINE_CHANNEL_SECRET')

if token:
    print(f"   ✓ LINE_CHANNEL_ACCESS_TOKEN: {token[:20]}...")
else:
    print("   ✗ LINE_CHANNEL_ACCESS_TOKEN: Not found")

if secret:
    print(f"   ✓ LINE_CHANNEL_SECRET: {secret[:20]}...")
else:
    print("   ✗ LINE_CHANNEL_SECRET: Not found")

# Check dependencies
print("\n2. Checking dependencies:")
try:
    import flask
    print(f"   ✓ Flask: {flask.__version__}")
except ImportError:
    print("   ✗ Flask: Not installed (run: pip install flask)")

try:
    import linebot
    print(f"   ✓ line-bot-sdk: {linebot.__version__}")
except ImportError:
    print("   ✗ line-bot-sdk: Not installed (run: pip install line-bot-sdk)")

# Check agent
print("\n3. Checking KYC agent:")
try:
    from agents.kyc_orchestrator.agent import root_agent
    print(f"   ✓ KYC Agent: Available")
    print(f"   ✓ Agent name: {root_agent.name}")
except Exception as e:
    print(f"   ✗ KYC Agent: {e}")

# Check LINE bot handler
print("\n4. Checking LINE bot components:")
try:
    from chat_platforms.line.line_bot import LineBotHandler, create_line_bot
    print("   ✓ LINE bot handler: Available")

    if token and secret:
        bot = create_line_bot(token, secret)
        print("   ✓ LINE bot instance: Created")
    else:
        print("   ⚠️  LINE bot instance: Skipped (no credentials)")
except Exception as e:
    print(f"   ✗ LINE bot handler: {e}")

# Check ngrok
print("\n5. Checking ngrok (for local testing):")
import shutil
if shutil.which('ngrok'):
    print("   ✓ ngrok: Installed")
    print("   → Run: ngrok http 5000")
else:
    print("   ⚠️  ngrok: Not found")
    print("   → Install: brew install ngrok")
    print("   → Or download from: https://ngrok.com/download")

print("\n" + "=" * 60)
if token and secret:
    print("✅ Setup complete! Ready to run LINE bot")
    print("\nNext steps:")
    print("  1. Run: python line_webhook_app.py")
    print("  2. In another terminal: ngrok http 5001")
    print("  3. Copy ngrok HTTPS URL")
    print("  4. Set webhook in LINE Developer Console")
    print("     URL: https://xxx.ngrok.io/webhook/line")
else:
    print("⚠️  Please add LINE credentials to .env file")
print("=" * 60)
