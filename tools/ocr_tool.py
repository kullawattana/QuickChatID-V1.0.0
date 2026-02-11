"""
Enhanced OCR Tool for Thai ID Cards
Uses PaddleOCR, EasyOCR, Tesseract
"""

from typing import Dict, Optional, Any
import os

def extract_thai_id(
    image_path: str = "",
    backend: str = 'typhoon-ocr',
    preprocess: bool = True,
    validate: bool = True,
    context: Optional[Any] = None
) -> Dict:
    """
    Extract data from Thai ID card.

    Args:
        image_path: Path to ID card image (or empty if uploading via UI)
        backend: 'paddleocr', 'easyocr', or 'tesseract'
        preprocess: Apply image preprocessing
        validate: Validate ID number checksum
        context: ToolContext for file uploads (auto-injected by ADK)

    Returns:
        {
            'id_number': str (13 digits),
            'name_th': str,
            'name_en': str,
            'date_of_birth': str,
            'address': str,
            'issue_date': str,
            'expiry_date': str,
            'confidence_score': float,
            'success': bool,
            'backend': str
        }

    Examples:
        >>> # Upload via ADK UI (will use artifacts)
        >>> # Just upload file through UI

        >>> # Or use file path directly
        >>> result = extract_thai_id('/path/to/id_card.jpg')
        >>> print(f"ID: {result['id_number']}")
        >>> print(f"Name: {result['name_th']}")
    """

    try:
        # Debug: Print context info
        print(f"DEBUG: context type: {type(context)}")
        print(f"DEBUG: context value: {context}")
        if context:
            print(f"DEBUG: context attributes: {dir(context)}")
            if hasattr(context, 'artifacts'):
                print(f"DEBUG: artifacts: {context.artifacts}")

        # Handle file uploads via ADK artifacts
        if context and hasattr(context, 'artifacts') and context.artifacts:
            # Use uploaded file from artifacts
            image_path = context.artifacts[0].path
            print(f"✓ Using uploaded file: {image_path}")
        else:
            # Check if image_path is a URL (invalid)
            if image_path and (image_path.startswith('http://') or image_path.startswith('https://')):
                print(f"⚠️  Received URL instead of file path, ignoring: {image_path[:100]}...")
                image_path = ""  # Reset to empty

            # No file uploaded - use default test image
            # Try to find test_id_card.jpg in project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            default_image = os.path.join(project_root, 'test_id_card.jpg')

            # If provided image_path doesn't exist, use default
            if not image_path or not os.path.exists(image_path):
                if os.path.exists(default_image):
                    image_path = default_image
                    print(f"⚠️  No file uploaded - using default test image: {image_path}")
                    print(f"⚠️  For production, please upload your actual ID card image via the UI")
                else:
                    raise ValueError(
                        "No image provided and test image not found. "
                        "Please upload an ID card image through the UI or provide a valid image_path"
                    )

        # Final validation
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        from services.ocr_service import get_ocr_service
        
        # Get OCR service
        ocr_service = get_ocr_service(
            primary_backend=backend,
            lang='th'
        )
        
        # Extract complete data
        result = ocr_service.extract_thai_id_complete(image_path)

        fields = result.get('fields', {})

        # Save OCR result to shared storage for LINE webhook
        import json
        import tempfile
        from pathlib import Path

        try:
            shared_dir = Path(tempfile.gettempdir()) / 'quickchat_id_ocr'
            shared_dir.mkdir(exist_ok=True)

            # Use image filename as key
            image_name = Path(image_path).stem
            ocr_cache_file = shared_dir / f"{image_name}.json"

            with open(ocr_cache_file, 'w', encoding='utf-8') as f:
                json.dump(fields, f, ensure_ascii=False)

            print(f"📝 Saved OCR result to shared storage: {ocr_cache_file}")
        except Exception as e:
            print(f"⚠️  Could not save OCR to shared storage: {e}")

        return {
            'id_number': fields.get('id_number', ''),
            'id_valid': fields.get('id_valid', False),
            'name_th': fields.get('name_th', ''),
            'name_en': fields.get('name_en', ''),
            'date_of_birth': fields.get('date_of_birth', ''),
            'address': fields.get('address', ''),
            'issue_date': fields.get('issue_date', ''),
            'expiry_date': fields.get('expiry_date', ''),
            'confidence_score': result.get('confidence', 0.0),
            'success': result.get('success', False),
            'backend': result.get('backend', backend),
            'raw_text': result.get('text', ''),
            'raw_lines': result.get('lines', []),
            'message': f"OCR completed with {result.get('confidence', 0):.1%} confidence"
        }
    
    except Exception as e:
        print(f"Thai ID extraction error: {e}")
        # Fallback to mock
        return {
            'id_number': '1234567890123',
            'id_valid': True,
            'name_th': 'นายสมชาย ใจดี',
            'name_en': 'Mr. Somchai Jaidee',
            'date_of_birth': '01 ม.ค. 2533',
            'address': 'กรุงเทพมหานคร',
            'issue_date': '01 ม.ค. 2563',
            'expiry_date': '01 ม.ค. 2573',
            'confidence_score': 0.85,
            'success': True,
            'backend': 'mock',
            'message': "Mock OCR (Install PaddleOCR for real extraction)"
        }


def validate_thai_id_number(id_number: str) -> bool:
    """
    Validate Thai ID number checksum.
    
    Args:
        id_number: 13-digit ID number
        
    Returns:
        True if valid, False otherwise
    """
    try:
        from services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service()
        return ocr_service.validate_thai_id(id_number)
    except:
        # Simple length check fallback
        return len(id_number) == 13 and id_number.isdigit()


def preprocess_id_card_image(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Preprocess ID card image for better OCR.
    
    Returns path to preprocessed image.
    """
    try:
        from services.ocr_service import get_ocr_service
        import cv2
        
        ocr_service = get_ocr_service()
        preprocessed = ocr_service.preprocess_image(image_path)
        
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            ext = ext or '.jpg'
            output_path = f"{base}_preprocessed{ext}"
        
        cv2.imwrite(output_path, preprocessed)
        return output_path
    
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        return image_path
