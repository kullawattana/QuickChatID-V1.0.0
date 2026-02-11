#!/usr/bin/env python3
"""Test Typhoon OCR directly"""
import sys
from pathlib import Path

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
print(f"Address: {result['address']}")
print(f"Issue Date: {result['issue_date']}")
print(f"Expiry Date: {result['expiry_date']}")
print(f"Confidence: {result['confidence_score']:.2%}")
print(f"Message: {result.get('message', 'N/A')}")
print("\n=== Raw Text (first 500 chars) ===")
print(result.get('raw_text', '')[:500])
