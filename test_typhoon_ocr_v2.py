#!/usr/bin/env python3
"""Test Typhoon OCR with API key"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from agent's .env
env_path = Path(__file__).parent / 'agents' / 'kyc_orchestrator' / '.env'
load_dotenv(env_path)

print(f"API Key loaded: {'Yes' if os.getenv('TYPHOON_OCR_API_KEY') else 'No'}")
print(f"API Key (first 10 chars): {os.getenv('TYPHOON_OCR_API_KEY', '')[:10]}...")

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from tools.ocr_tool import extract_thai_id

# Test with real image
result = extract_thai_id(
    image_path='test_id_card.jpg',
    backend='typhoon-ocr'
)

print("\n=== Typhoon OCR Test Result ===")
print(f"Success: {result['success']}")
print(f"Backend: {result['backend']}")
print(f"ID Number: {result['id_number']}")
print(f"ID Valid: {result.get('id_valid', 'N/A')}")
print(f"Name (TH): {result['name_th']}")
print(f"Name (EN): {result['name_en']}")
print(f"Date of Birth: {result['date_of_birth']}")
print(f"Confidence: {result['confidence_score']:.2%}")
print(f"Message: {result.get('message', 'N/A')}")
print("\n=== Raw Text (first 1000 chars) ===")
print(result.get('raw_text', '')[:1000])
