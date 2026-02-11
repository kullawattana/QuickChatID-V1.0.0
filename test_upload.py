#!/usr/bin/env python3
"""
Test script to verify image upload functionality
"""
import requests
import json
from PIL import Image
import io

API_BASE_URL = "http://localhost:5003/api"

def create_test_image(width=800, height=600, color=(100, 150, 200)):
    """Create a simple test image"""
    img = Image.new('RGB', (width, height), color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_workflow():
    """Test complete upload workflow"""

    print("=" * 60)
    print("🧪 Testing QuickChat ID Upload Workflow")
    print("=" * 60)

    # Step 1: Initialize session
    print("\n1️⃣  Initializing session...")
    response = requests.post(f"{API_BASE_URL}/session/init")

    if response.status_code != 200:
        print(f"❌ Failed to initialize session: {response.status_code}")
        return

    data = response.json()
    session_id = data.get('session_id')
    print(f"✅ Session created: {session_id}")

    # Step 2: Send initial message
    print("\n2️⃣  Sending initial message...")
    response = requests.post(
        f"{API_BASE_URL}/chat/message",
        json={
            "session_id": session_id,
            "message": "พร้อมค่ะ"
        }
    )

    if response.status_code != 200:
        print(f"❌ Failed to send message: {response.status_code}")
        return

    data = response.json()
    print(f"✅ Response: {data.get('response', '')[:100]}...")

    # Step 3: Upload ID card
    print("\n3️⃣  Uploading ID card...")
    test_id_card = create_test_image(color=(255, 200, 200))

    files = {'file': ('id_card.jpg', test_id_card, 'image/jpeg')}
    form_data = {
        'session_id': session_id,
        'image_type': 'id_card'
    }

    response = requests.post(
        f"{API_BASE_URL}/chat/image",
        files=files,
        data=form_data
    )

    print(f"   Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Failed to upload ID card")
        print(f"   Response: {response.text[:200]}")
        return

    data = response.json()
    print(f"✅ ID Card uploaded successfully")
    print(f"   Response: {data.get('response', '')[:150]}...")
    print(f"   Next step: {data.get('next_step')}")

    # Step 4: Upload selfie
    print("\n4️⃣  Uploading selfie...")
    test_selfie = create_test_image(color=(200, 255, 200))

    files = {'file': ('selfie.jpg', test_selfie, 'image/jpeg')}
    form_data = {
        'session_id': session_id,
        'image_type': 'selfie'
    }

    response = requests.post(
        f"{API_BASE_URL}/chat/image",
        files=files,
        data=form_data
    )

    print(f"   Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Failed to upload selfie")
        print(f"   Response: {response.text[:200]}")
        return

    data = response.json()
    print(f"✅ Selfie uploaded successfully")
    print(f"   Response: {data.get('response', '')[:150]}...")
    print(f"   Next step: {data.get('next_step')}")

    # Check for trust badge
    if 'trust_badge' in data:
        badge = data['trust_badge']
        print(f"\n🏆 Trust Badge Generated:")
        print(f"   Level: {badge.get('level', 'N/A')}")
        print(f"   Score: {badge.get('score', 0)}/100")
        print(f"   Transaction Limit: ฿{badge.get('transactionLimit', 0):,}")

    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_workflow()
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
