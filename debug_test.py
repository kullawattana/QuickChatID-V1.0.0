#!/usr/bin/env python3
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('agents/kyc_orchestrator/.env')
sys.path.insert(0, str(Path(__file__).parent))

from services.ocr_service import get_ocr_service

# Get OCR service
ocr_service = get_ocr_service(primary_backend='typhoon-ocr', lang='th')

# Extract text
result = ocr_service.extract_text('test_id_card.jpg', preprocess=False)

print("\n=== RAW OCR OUTPUT ===")
print(result['text'])
print("\n=== EXTRACTED FIELDS ===")

# Extract fields
fields = ocr_service.extract_thai_id_fields(result)
for key, value in fields.items():
    print(f"{key}: {value}")
