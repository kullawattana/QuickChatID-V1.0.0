"""
Comprehensive OCR Service for Thai ID Cards
Supports: PaddleOCR, EasyOCR, Tesseract
"""

import os
import re
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class OCRService:
    """
    Production-grade OCR service for Thai ID cards.
    
    Features:
    - PaddleOCR (best for Thai, 82.68% accuracy)
    - EasyOCR (backup, good multilingual)
    - Tesseract (fallback)
    - Image preprocessing
    - Field extraction & validation
    - ID number checksum validation
    """
    
    def __init__(self, 
                 primary_backend: str = 'typhoon-ocr',
                 lang: str = 'th',
                 use_gpu: bool = False):
        """
        Initialize OCR Service.
        
        Args:
            primary_backend: 'typhoon-ocr', 'paddleocr', or 'tesseract'
            lang: Language code ('th' for Thai)
            use_gpu: Use GPU acceleration
        """
        self.primary_backend = primary_backend
        self.lang = lang
        self.use_gpu = use_gpu
        
        self.paddleocr_available = self._check_paddleocr()
        self.easyocr_available = self._check_easyocr()
        self.tesseract_available = self._check_tesseract()
        self.typhoon_available = self._check_typhoon()

        if self.primary_backend in ('typhoon', 'typhoon-ocr') and os.getenv('ENABLE_LOCAL_OCR', '0') != '1':
            self.paddleocr_available = False
            self.easyocr_available = False
            self.tesseract_available = False
        
        self._init_ocr_engines()
    
    def _check_paddleocr(self) -> bool:
        """Check if PaddleOCR is available"""
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False
    
    def _check_easyocr(self) -> bool:
        """Check if EasyOCR is available"""
        if os.getenv('ENABLE_EASYOCR', '0') != '1':
            return False
        try:
            import easyocr
            return True
        except ImportError:
            return False
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

    def _check_typhoon(self) -> bool:
        """Check if Typhoon OCR is available (library + API key)"""
        try:
            import typhoon_ocr  # noqa: F401
        except ImportError:
            return False
        return bool(os.getenv('TYPHOON_OCR_API_KEY') or os.getenv('OPENAI_API_KEY'))
    
    def _init_ocr_engines(self):
        """Initialize OCR engines"""
        # PaddleOCR - Best for Thai
        if self.paddleocr_available:
            try:
                from paddleocr import PaddleOCR
                import os
                os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
                self.paddle_ocr = PaddleOCR(
                    use_textline_orientation=True,
                    lang=self.lang
                )
            except Exception as e:
                print(f"Failed to initialize PaddleOCR: {e}")
                self.paddle_ocr = None
        
        # EasyOCR - Backup
        if self.easyocr_available:
            try:
                import easyocr
                # Store EasyOCR models at user-provided location (avoid home dir permission issues)
                easyocr_dir = os.getenv('EASYOCR_MODEL_DIR', '/Users/topgun/Desktop/EasyOCR')
                os.makedirs(easyocr_dir, exist_ok=True)
                self.easy_reader = easyocr.Reader(
                    ['th', 'en'],
                    gpu=self.use_gpu,
                    model_storage_directory=easyocr_dir,
                    user_network_directory=easyocr_dir
                )
            except Exception as e:
                print(f"Failed to initialize EasyOCR: {e}")
                self.easy_reader = None
    
    def extract_text(self, 
                     image_path: str,
                     backend: Optional[str] = None,
                     preprocess: bool = True) -> Dict:
        """
        Extract text from image.
        
        Args:
            image_path: Path to image
            backend: Override backend
            preprocess: Apply preprocessing
            
        Returns:
            {
                'text': str,
                'lines': List[str],
                'confidence': float,
                'backend': str,
                'boxes': List[coordinates]
            }
        """
        backend = backend or self.primary_backend
        if backend in ('typhoon', 'typhoon-ocr'):
            return self._extract_typhoon(image_path)
        
        # Preprocess image
        if preprocess:
            img = self.preprocess_image(image_path)
            # Save preprocessed with a valid extension
            base, ext = os.path.splitext(image_path)
            ext = ext or '.jpg'
            preprocessed_path = f"{base}_preprocessed{ext}"
            written = cv2.imwrite(preprocessed_path, img)
            if not written:
                raise RuntimeError(f"Failed to write preprocessed image: {preprocessed_path}")
            image_to_ocr = preprocessed_path
        else:
            image_to_ocr = image_path
        
        # Run OCR
        if backend == 'paddleocr' and self.paddle_ocr:
            result = self._extract_paddleocr(image_to_ocr)
        elif backend == 'easyocr' and self.easy_reader:
            result = self._extract_easyocr(image_to_ocr)
        elif backend == 'tesseract' and self.tesseract_available:
            result = self._extract_tesseract(image_to_ocr)
        else:
            # Mock fallback
            result = self._extract_mock(image_to_ocr)

        # Optional Typhoon OCR fallback if local OCR is unavailable/mocked
        if result.get('backend') == 'mock' and self.typhoon_available:
            try:
                return self._extract_typhoon(image_to_ocr)
            except Exception as e:
                print(f"Typhoon OCR fallback failed: {e}")

        return result
    
    def _extract_paddleocr(self, image_path: str) -> Dict:
        """Extract using PaddleOCR"""
        try:
            # Support both old and new PaddleOCR APIs
            if hasattr(self.paddle_ocr, 'predict'):
                result = self.paddle_ocr.predict(image_path)

                if not result or len(result) == 0:
                    return {
                        'text': '',
                        'lines': [],
                        'confidence': 0.0,
                        'backend': 'paddleocr',
                        'boxes': []
                    }

                # New API returns OCRResult object
                ocr_result = result[0]
                lines = ocr_result.get('rec_texts', [])
                confidences = ocr_result.get('rec_scores', [])
                boxes = ocr_result.get('rec_boxes', [])
            else:
                # Legacy API
                result = self.paddle_ocr.ocr(image_path, cls=True)
                lines = []
                boxes = []
                confidences = []
                for detection in result or []:
                    for item in detection:
                        box, (text, conf) = item
                        lines.append(text)
                        boxes.append(box)
                        confidences.append(conf)

            avg_confidence = np.mean(confidences) if confidences else 0.0
            full_text = '\n'.join(lines)

            return {
                'text': full_text,
                'lines': lines,
                'confidence': float(avg_confidence),
                'backend': 'paddleocr',
                'boxes': boxes if isinstance(boxes, list) else [],
                'success': True
            }

        except Exception as e:
            print(f"PaddleOCR extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return self._extract_mock(image_path)
    
    def _extract_easyocr(self, image_path: str) -> Dict:
        """Extract using EasyOCR"""
        try:
            result = self.easy_reader.readtext(image_path)
            
            lines = []
            boxes = []
            confidences = []
            
            for detection in result:
                box, text, conf = detection
                lines.append(text)
                boxes.append(box)
                confidences.append(conf)
            
            avg_confidence = np.mean(confidences) if confidences else 0.0
            full_text = '\n'.join(lines)
            
            return {
                'text': full_text,
                'lines': lines,
                'confidence': float(avg_confidence),
                'backend': 'easyocr',
                'boxes': boxes,
                'success': True
            }
        
        except Exception as e:
            print(f"EasyOCR extraction failed: {e}")
            return self._extract_mock(image_path)
    
    def _extract_tesseract(self, image_path: str) -> Dict:
        """Extract using Tesseract"""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            
            # Get text
            text = pytesseract.image_to_string(img, lang='tha+eng')
            
            # Get detailed data
            data = pytesseract.image_to_data(img, lang='tha+eng', output_type=pytesseract.Output.DICT)
            
            lines = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:
                    text_item = data['text'][i]
                    if text_item.strip():
                        lines.append(text_item)
                        confidences.append(int(conf) / 100.0)
            
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return {
                'text': text,
                'lines': lines,
                'confidence': float(avg_confidence),
                'backend': 'tesseract',
                'boxes': [],
                'success': True
            }
        
        except Exception as e:
            print(f"Tesseract extraction failed: {e}")
            return self._extract_mock(image_path)

    def _prepare_image_for_typhoon(self, image_path: str) -> str:
        """
        Resize and enhance image before sending to Typhoon VLM.
        Typhoon ignores target_image_dim for JPEG images - must resize manually.
        Target: longest side 2400px (downscale only), enhance contrast.
        Returns path to processed image (temp file).
        """
        try:
            from PIL import Image as PILImage, ImageEnhance
            import tempfile

            img = PILImage.open(image_path).convert('RGB')
            w, h = img.size
            max_dim = max(w, h)
            target = 2400

            # Always scale to target (upscale small images too — VLM reads better at 2400px)
            if max_dim != target:
                scale = target / max_dim
                new_w, new_h = int(w * scale), int(h * scale)
                img = img.resize((new_w, new_h), PILImage.LANCZOS)
                print(f"📐 Scaled image: {w}×{h} → {new_w}×{new_h}")
            else:
                print(f"📐 Image already at target size: {w}×{h}")

            # Contrast enhancement via PIL
            img = ImageEnhance.Contrast(img).enhance(1.4)

            # Unsharp mask via cv2 — much sharper than PIL's basic filter
            import cv2 as _cv2
            import numpy as _np
            img_bgr = _cv2.cvtColor(_np.array(img), _cv2.COLOR_RGB2BGR)
            blurred = _cv2.GaussianBlur(img_bgr, (0, 0), 2)
            sharpened = _cv2.addWeighted(img_bgr, 1.8, blurred, -0.8, 0)
            img = PILImage.fromarray(_cv2.cvtColor(sharpened, _cv2.COLOR_BGR2RGB))

            # Save to temp file
            base, ext = os.path.splitext(image_path)
            ext = ext.lower() if ext.lower() in ('.jpg', '.jpeg', '.png') else '.jpg'
            processed_path = f"{base}_typhoon_ready{ext}"
            img.save(processed_path, format='JPEG', quality=95)
            print(f"✅ Saved enhanced image for Typhoon: {processed_path}")
            return processed_path
        except Exception as e:
            print(f"⚠️  Image preparation failed, using original: {e}")
            return image_path

    def _extract_address_from_crop(self, image_path: str, api_key: str) -> str:
        """
        Crop the address area of a Thai ID card and run a focused OCR pass.
        Thai ID card address is in the bottom ~55-85% of the card, full width.
        Returns raw address text (empty string if extraction fails).
        """
        try:
            from typhoon_ocr import ocr_document
            from PIL import Image as PILImage, ImageEnhance
            import cv2 as _cv2
            import numpy as _np

            img = PILImage.open(image_path).convert('RGB')
            w, h = img.size

            # Address region: rows 45-93% from top, columns 0-100% (full width)
            # Captures address + province/postal while avoiding issue/expiry date area
            x1, y1 = int(w * 0.01), int(h * 0.45)
            x2, y2 = int(w * 0.99), int(h * 0.93)
            crop = img.crop((x1, y1, x2, y2))
            cw, ch = crop.size
            print(f"✂️  Address crop: ({x1},{y1})-({x2},{y2}) → {cw}×{ch}")

            # Upscale crop to 2400px (makes small address text much larger)
            scale = 2400 / max(cw, ch)
            crop = crop.resize((int(cw * scale), int(ch * scale)), PILImage.LANCZOS)

            # Enhance for VLM — stronger than full-card pass (small text in crop)
            crop = ImageEnhance.Contrast(crop).enhance(1.6)
            img_bgr = _cv2.cvtColor(_np.array(crop), _cv2.COLOR_RGB2BGR)
            # Stronger unsharp mask for small Thai characters
            blurred = _cv2.GaussianBlur(img_bgr, (0, 0), 1.5)
            sharpened = _cv2.addWeighted(img_bgr, 2.0, blurred, -1.0, 0)
            crop = PILImage.fromarray(_cv2.cvtColor(sharpened, _cv2.COLOR_BGR2RGB))

            # Save crop
            base = os.path.splitext(image_path)[0]
            crop_path = f"{base}_addr_crop.jpg"
            crop.save(crop_path, format='JPEG', quality=95)

            # OCR the crop
            crop_md = (ocr_document(pdf_or_image_path=crop_path, api_key=api_key) or "").strip()
            print(f"✂️  Address crop OCR (full):\n{crop_md}")

            # Extract address lines from the crop output — preserve document ORDER
            addr_keywords = ['หมู่', 'ถนน', 'ตำบล', 'อำเภอ', 'จังหวัด', 'ต.', 'อ.', 'จ.', 'ซอย', 'แขวง', 'เขต']
            # Keywords that mark non-address content (skip these)
            skip_keywords = ['เกิดวันที่', 'Date of Birth', 'วันออกบัตร', 'Date of Issue',
                             'วันหมดอายุ', 'Date of Expiry', 'ชื่อ', 'เลขประจำตัว', 'Name']

            addr_lines_ordered = []
            for line in crop_md.splitlines():
                clean = line.strip().lstrip('-').lstrip('•').strip()
                if not clean or clean.startswith('#'):
                    continue
                # Skip known non-address sections
                if any(kw in clean for kw in skip_keywords):
                    continue
                score = sum(1 for kw in addr_keywords if kw in clean)
                if score > 0:
                    addr_lines_ordered.append(clean)

            if addr_lines_ordered:
                # Preserve original order (important for house/sub-dist/district/province)
                address = re.sub(r'\s+', ' ', ' '.join(addr_lines_ordered[:4])).strip()
                print(f"✂️  Address extracted from crop: {address}")
                return address

            # Fallback: any Thai/digit content line
            all_content_lines = []
            for line in crop_md.splitlines():
                clean = line.strip().lstrip('-').lstrip('•').strip()
                if clean and not clean.startswith('#') and not any(kw in clean for kw in skip_keywords):
                    if any(c.isdigit() for c in clean) or any('\u0e00' <= c <= '\u0e7f' for c in clean):
                        all_content_lines.append(clean)
            if all_content_lines:
                address = re.sub(r'\s+', ' ', ' '.join(all_content_lines[:3])).strip()
                print(f"✂️  Address extracted from crop (fallback): {address}")
                return address

        except Exception as e:
            print(f"⚠️  Address crop OCR failed: {e}")
        return ""

    def _extract_typhoon(self, image_path: str) -> Dict:
        """Extract using Typhoon OCR (API)"""
        try:
            from typhoon_ocr import ocr_document
            import os

            # Get API key from environment
            api_key = os.getenv('TYPHOON_OCR_API_KEY') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("TYPHOON_OCR_API_KEY or OPENAI_API_KEY environment variable not set")

            # Typhoon ignores target_image_dim for JPEG — resize manually first
            prepared_path = self._prepare_image_for_typhoon(image_path)

            markdown = ocr_document(
                pdf_or_image_path=prepared_path,
                api_key=api_key,
            )
            text = (markdown or "").strip()
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            # Log raw output for debugging hallucination issues
            print(f"📄 Typhoon OCR raw output ({len(text)} chars):\n{text[:1000]}")

            # Second pass: focused crop on address area for better accuracy
            crop_address = self._extract_address_from_crop(image_path, api_key)
            if crop_address:
                # Inject crop address into text so _extract_from_markdown can find it
                # Replace any existing ## ที่อยู่ section with the crop result
                addr_section = f"\n## ที่อยู่\n- {crop_address}\n"
                if '## ที่อยู่' in text:
                    text = re.sub(r'##\s*ที่อยู่[\s\S]*?(?=\n##|$)', addr_section, text)
                else:
                    text = text + addr_section
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                print(f"✅ Address replaced with crop result: {crop_address}")

            return {
                'text': text,
                'lines': lines,
                'confidence': 0.0,
                'backend': 'typhoon-ocr',
                'boxes': [],
                'success': True
            }
        except Exception as e:
            print(f"Typhoon OCR extraction failed: {e}")
            return self._extract_mock(image_path)
    
    def _extract_mock(self, image_path: str) -> Dict:
        """Mock extraction - returns empty result, not fake data"""
        print(f"⚠️  No OCR backend available for: {image_path}")
        return {
            'text': '',
            'lines': [],
            'confidence': 0.0,
            'backend': 'mock',
            'boxes': [],
            'success': False,
            'note': 'No OCR backend available. Install typhoon-ocr or PaddleOCR.'
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR.

        Steps:
        1. Convert to grayscale
        2. Denoise
        3. Adaptive threshold
        4. Deskew
        5. Enhance contrast
        """
        # Read image
        img = cv2.imread(image_path)

        # Check if image was loaded successfully
        if img is None:
            raise FileNotFoundError(f"Cannot read image file: {image_path}. Please provide a valid image file path or upload the image again.")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Deskew
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            (h, w) = thresh.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                thresh,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
        else:
            rotated = thresh
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(rotated)
        
        return enhanced
    
    def extract_thai_id_fields(self, ocr_result: Dict) -> Dict:
        """
        Extract specific fields from Thai ID card.
        Supports both markdown (Typhoon OCR) and plain text formats.

        Fields:
        - ID number (เลขบัตร)
        - Name Thai (ชื่อ-นามสกุล ภาษาไทย)
        - Name English (ชื่อ-นามสกุล ภาษาอังกฤษ)
        - Date of birth (วันเกิด)
        - Address (ที่อยู่)
        - Issue date (วันออกบัตร)
        - Expiry date (วันหมดอายุ)
        """
        text = ocr_result['text']
        lines = ocr_result['lines']
        backend = ocr_result.get('backend', '')

        fields = {}

        # Check if it's markdown format (from Typhoon OCR)
        is_markdown = '##' in text or backend == 'typhoon-ocr'

        if is_markdown:
            fields = self._extract_from_markdown(text)
        else:
            fields = self._extract_from_plain_text(text, lines)

        return fields

    def _extract_from_markdown(self, text: str) -> Dict:
        """Extract fields from Typhoon OCR markdown format"""
        fields = {}

        # Extract ID number — Typhoon sometimes appends extra trailing digit (e.g. "1 3580 22055 37 5 0")
        # Strategy: extract all digits near เลขประจำตัวประชาชน, try 13-digit slices, pick valid checksum
        id_section_match = re.search(r'เลขประจำตัวประชาชน[\s\S]*?\n[-\s]*([\d\s-]+)', text)
        if id_section_match:
            raw_digits = re.sub(r'[\s-]', '', id_section_match.group(1).split('\n')[0])
            # Try first 13 digits, then 14 digits sliced to 13
            for start in range(max(1, len(raw_digits) - 14), -1, -1):
                candidate = raw_digits[start:start+13]
                if len(candidate) == 13 and candidate.isdigit():
                    if self.validate_thai_id(candidate):
                        fields['id_number'] = candidate
                        fields['id_valid'] = True
                        break
            # Even if checksum fails, store the best 13-digit candidate (first 13)
            if 'id_number' not in fields and len(raw_digits) >= 13:
                fields['id_number'] = raw_digits[:13]
                fields['id_valid'] = False

        # Extract Thai name
        thai_name_pattern = r'(?:ชื่อตัวและชื่อสกุล|ชื่อ-นามสกุล)[\s\S]*?[-\s]*((?:นาย|นาง|นางสาว)\s+[ก-๙\s]+)'
        match = re.search(thai_name_pattern, text)
        if match:
            fields['name_th'] = re.sub(r'\s+', ' ', match.group(1).strip())

        # Extract English name - combine first and last name
        first_name = ''
        last_name = ''

        # Try to find first name
        first_pattern = r'(?:Name|First name)[\s\S]*?[-\s]*((?:Mr\.|Mrs\.|Miss)\s+[A-Z][a-z]+)'
        match = re.search(first_pattern, text)
        if match:
            first_name = match.group(1).strip()

        # Try to find last name
        last_pattern = r'(?:Last name|Surname)[\s\S]*?[-\s]*([A-Z][a-z]+)'
        match = re.search(last_pattern, text)
        if match:
            last_name = match.group(1).strip()

        if first_name and last_name:
            fields['name_en'] = f"{first_name} {last_name}"
        elif first_name:
            fields['name_en'] = first_name

        # Extract dates (Thai format)
        # Use [^#]* to stay within the current Markdown section (stop before next ##)
        THAI_MONTH = r'(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)'
        EN_MONTH   = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

        # Birth date — stop at next ## to avoid bleeding into issue-date section
        birth_patterns = [
            rf'เกิดวันที่[^#]*?[-\s]*(\d{{1,2}}\s+{THAI_MONTH}\s+\d{{4}})',   # Thai WITH year
            rf'เกิดวันที่[^#]*?Date of Birth[^#\n]*?(\d{{1,2}}\s+{EN_MONTH}\.?\s*\d{{4}})',  # English WITH year
            rf'เกิดวันที่[^#]*?[-\s]*(\d{{1,2}}\s+{THAI_MONTH})',               # Thai NO year
            rf'เกิดวันที่[^#]*?Date of Birth[^#\n]*?(\d{{1,2}}\s+{EN_MONTH}\.?)',# English NO year
        ]
        for pattern in birth_patterns:
            match = re.search(pattern, text)
            if match:
                fields['date_of_birth'] = match.group(1).strip()
                break

        # Issue date — scoped to วันออกบัตร section only
        issue_patterns = [
            rf'วันออกบัตร[^#]*?Date of Issue[^#\n]*?(\d{{1,2}}\s+{EN_MONTH}\.?\s*\d{{4}})',
            rf'วันออกบัตร[^#]*?[-\s]*(\d{{1,2}}\s+{THAI_MONTH}\s+\d{{4}})',
        ]
        for pattern in issue_patterns:
            match = re.search(pattern, text)
            if match:
                fields['issue_date'] = match.group(1).strip()
                break

        # Expiry date — scoped to วันหมดอายุ section only
        expiry_patterns = [
            rf'วันหมดอายุ[^#]*?Date of Expiry[^#\n]*?(\d{{1,2}}\s+{EN_MONTH}\.?\s*\d{{4}})',
            rf'วันหมดอายุ[^#]*?[-\s]*(\d{{1,2}}\s+{THAI_MONTH}\s+\d{{4}})',
        ]
        for pattern in expiry_patterns:
            match = re.search(pattern, text)
            if match:
                fields['expiry_date'] = match.group(1).strip()
                break

        # Extract address — capture the full ที่อยู่ section (may be multi-line)
        addr_section_match = re.search(r'##\s*ที่อยู่[^\n]*\n([\s\S]*?)(?=\n##|##|$)', text)
        if addr_section_match:
            addr_content = addr_section_match.group(1)
            addr_lines = []
            for line in addr_content.splitlines():
                line = line.strip().lstrip('-').lstrip('•').strip()
                if line and not line.startswith('#'):
                    addr_lines.append(line)
            if addr_lines:
                fields['address'] = re.sub(r'\s+', ' ', ' '.join(addr_lines)).strip()
        else:
            # Fallback: single-line pattern
            address_pattern = r'ที่อยู่[^#]*?[-\s]*(\d+/?\d*\s+[^#\n]+?)(?=\n##|\n\n|$)'
            match = re.search(address_pattern, text)
            if match:
                fields['address'] = re.sub(r'\s+', ' ', match.group(1).strip())

        return fields

    def _extract_from_plain_text(self, text: str, lines: List[str]) -> Dict:
        """Extract fields from plain text (PaddleOCR/EasyOCR format)"""
        fields = {}

        # Extract ID number (13 digits) - remove spaces
        all_digits = re.sub(r'\D', '', text)
        for i in range(len(all_digits) - 12):
            potential_id = all_digits[i:i+13]
            if self.validate_thai_id(potential_id):
                fields['id_number'] = potential_id
                fields['id_valid'] = True
                break

        # If no valid ID found, try pattern matching
        if 'id_number' not in fields:
            id_pattern = r'\d[\s-]?\d{4}[\s-]?\d{5}[\s-]?\d{2}[\s-]?\d'
            id_match = re.search(id_pattern, text)
            if id_match:
                id_number = re.sub(r'[\s-]', '', id_match.group(0))
                if len(id_number) == 13:
                    fields['id_number'] = id_number
                    fields['id_valid'] = self.validate_thai_id(id_number)

        # Extract Thai name
        thai_name_pattern = r'((?:นาย|นาง|นางสาว)\s+[ก-๙\s]+?)(?=\s*Mr\.|Mrs\.|Miss|\n|$)'
        thai_name_match = re.search(thai_name_pattern, text)
        if thai_name_match:
            fields['name_th'] = re.sub(r'\s+', ' ', thai_name_match.group(1).strip())

        # Extract English name
        eng_name_pattern = r'((?:Mr\.|Mrs\.|Miss)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        eng_name_match = re.search(eng_name_pattern, text)
        if eng_name_match:
            fields['name_en'] = eng_name_match.group(1).strip()

        # Extract dates
        date_pattern = r'\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s+\d{4}'
        dates = re.findall(date_pattern, text)

        if len(dates) >= 1:
            fields['date_of_birth'] = dates[0]
        if len(dates) >= 2:
            fields['issue_date'] = dates[1]
        if len(dates) >= 3:
            fields['expiry_date'] = dates[2]

        # Extract address
        for line in lines:
            if any(keyword in line for keyword in ['ตำบล', 'อำเภอ', 'จังหวัด', 'ต.', 'อ.', 'จ.', 'หมู่']):
                fields['address'] = line
                break

        return fields
    
    def validate_thai_id(self, id_number: str) -> bool:
        """
        Validate Thai ID number using checksum algorithm.
        
        Algorithm:
        1. Multiply each digit by (13 - position)
        2. Sum all results
        3. Modulo 11
        4. Subtract from 11
        5. Modulo 10
        6. Should equal last digit
        """
        if not id_number or len(id_number) != 13:
            return False
        
        try:
            digits = [int(d) for d in id_number]
            
            # Calculate checksum
            total = sum((13 - i) * digits[i] for i in range(12))
            check_digit = (11 - (total % 11)) % 10
            
            return check_digit == digits[12]
        except:
            return False
    
    def extract_thai_id_complete(self, image_path: str) -> Dict:
        """
        Complete Thai ID extraction pipeline.

        Returns complete structured data.
        """
        # Extract text
        ocr_result = self.extract_text(image_path, preprocess=True)

        # Extract fields
        fields = self.extract_thai_id_fields(ocr_result)

        # Calculate confidence based on extracted fields
        # For Typhoon OCR which doesn't provide confidence scores
        if ocr_result.get('backend') == 'typhoon-ocr' and ocr_result.get('confidence', 0) == 0.0:
            # Required fields
            required_fields = ['id_number', 'name_th', 'name_en']
            optional_fields = ['date_of_birth', 'address', 'issue_date', 'expiry_date']

            # Count successfully extracted fields
            required_count = sum(1 for f in required_fields if fields.get(f))
            optional_count = sum(1 for f in optional_fields if fields.get(f))

            # Calculate confidence: required fields are worth more
            required_score = (required_count / len(required_fields)) * 0.7
            optional_score = (optional_count / len(optional_fields)) * 0.3
            calculated_confidence = required_score + optional_score

            # Update confidence
            ocr_result['confidence'] = float(calculated_confidence)

        # Combine results
        return {
            **ocr_result,
            'fields': fields,
            'extracted_at': datetime.now().isoformat(),
            'valid_id': fields.get('id_valid', False)
        }


# Singleton
_ocr_service = None

def get_ocr_service(
    primary_backend: str = 'typhoon-ocr',
    lang: str = 'th',
    use_gpu: bool = False
):
    """Get singleton instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService(
            primary_backend=primary_backend,
            lang=lang,
            use_gpu=use_gpu
        )
    return _ocr_service
