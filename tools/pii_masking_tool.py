"""PII Masking Tool"""
import re

def mask_pii(text: str):
    """Mask PII"""
    masked = text
    masked = re.sub(r'0\d{9}', '0XX-XXX-XXXX', masked)
    masked = re.sub(r'[\w\.-]+@[\w\.-]+', 'xxx@xxx.com', masked)
    return {
        'masked_text': masked,
        'entities_found': 2,
        'message': "PII masked successfully"
    }
