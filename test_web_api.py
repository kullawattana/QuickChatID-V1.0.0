#!/usr/bin/env python3
"""
Test script for Web API
Tests all endpoints to ensure they work correctly
"""

import requests
import json
import sys

API_BASE = "http://localhost:5001/api"


def test_health():
    """Test health check endpoint"""
    print("1️⃣  Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed")
            print(f"      Status: {data.get('status')}")
            print(f"      Service: {data.get('service')}")
            print(f"      Version: {data.get('version')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to API server")
        print(f"      Make sure web_api_app.py is running on port 5001")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_session_init():
    """Test session initialization"""
    print("\n2️⃣  Testing session initialization...")
    try:
        response = requests.post(f"{API_BASE}/session/init", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Session initialized")
                print(f"      Session ID: {data.get('session_id')}")
                print(f"      User ID: {data.get('user_id')}")
                print(f"      Welcome: {data.get('message', {}).get('content', '')[:50]}...")
                return data.get('session_id')
            else:
                print(f"   ❌ Session init failed: {data.get('error')}")
                return None
        else:
            print(f"   ❌ Session init failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def test_send_message(session_id):
    """Test sending a message"""
    print("\n3️⃣  Testing chat message...")
    try:
        response = requests.post(
            f"{API_BASE}/chat/message",
            json={
                "session_id": session_id,
                "message": "พร้อม"
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Message sent successfully")
                print(f"      Response: {data.get('response', '')[:100]}...")
                print(f"      Next Step: {data.get('next_step')}")
                return True
            else:
                print(f"   ❌ Message failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Message failed: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_verification_status(session_id):
    """Test getting verification status"""
    print("\n4️⃣  Testing verification status...")
    try:
        response = requests.get(
            f"{API_BASE}/verification/status/{session_id}",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Status retrieved")
                print(f"      Current Step: {data.get('current_step')}")
                print(f"      Completed: {data.get('is_completed')}")
                return True
            else:
                print(f"   ❌ Status failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 QuickChat ID - Web API Test Suite")
    print("=" * 60)

    # Test 1: Health Check
    if not test_health():
        print("\n❌ Health check failed - API server not running?")
        print("\nTo start the API server:")
        print("   python web_api_app.py")
        sys.exit(1)

    # Test 2: Session Init
    session_id = test_session_init()
    if not session_id:
        print("\n❌ Session initialization failed")
        sys.exit(1)

    # Test 3: Send Message
    if not test_send_message(session_id):
        print("\n❌ Sending message failed")
        sys.exit(1)

    # Test 4: Verification Status
    if not test_verification_status(session_id):
        print("\n❌ Getting status failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\n🎉 Web API is working correctly!")
    print("\nNext steps:")
    print("1. Start the frontend:")
    print("   cd frontend && npm run dev")
    print("\n2. Open browser:")
    print("   http://localhost:5173")
    print("")


if __name__ == '__main__':
    main()
