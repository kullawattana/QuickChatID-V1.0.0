#!/usr/bin/env python3
"""Quick test - Extract Thai ID with Typhoon OCR"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv('agents/kyc_orchestrator/.env')

sys.path.insert(0, str(Path(__file__).parent))

from tools.ocr_tool import extract_thai_id

print("\n🔍 Testing Typhoon OCR with Thai ID Card...\n")

# Test with the test image
result = extract_thai_id(
    image_path='test_id_card.jpg',
    backend='typhoon-ocr'
)

print("=" * 60)
print("✅ EXTRACTION RESULTS")
print("=" * 60)
print(f"📱 Backend:        {result['backend']}")
print(f"🆔 ID Number:      {result['id_number']}")
print(f"✓  ID Valid:       {result.get('id_valid', False)}")
print(f"👤 Name (Thai):    {result['name_th']}")
print(f"👤 Name (English): {result['name_en']}")
print(f"🎂 Date of Birth:  {result['date_of_birth']}")
print(f"📍 Address:        {result.get('address', 'N/A')}")
print(f"📅 Issue Date:     {result.get('issue_date', 'N/A')}")
print(f"📅 Expiry Date:    {result.get('expiry_date', 'N/A')}")
print(f"📊 Confidence:     {result['confidence_score']:.1%}")
print(f"✅ Success:        {result['success']}")
print("=" * 60)
