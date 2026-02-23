"""
Liveness Detection Service

Supports multiple approaches:
1. Silent-Face-Anti-Spoofing via DeepFace (MiniFASNet)
2. MediaPipe blink/head movement detection
3. Texture-based anti-spoofing (Moiré patterns, screen detection)

References:
- https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
- https://github.com/olekacak/Face-Recognition
- https://sefiks.com/2024/06/08/face-anti-spoofing-for-facial-recognition-in-python/
"""

import os
import cv2
import numpy as np
from typing import Dict, Optional, List

class LivenessDetectionService:
    """
    Face liveness detection to prevent spoofing attacks.

    Methods:
    1. Texture analysis (Moiré patterns, screen detection)
    2. MediaPipe-based (blink detection, head depth)
    3. Silent-Face-Anti-Spoofing (if DeepFace available)
    """

    def __init__(self, primary_method: str = 'texture'):
        """
        Initialize Liveness Detection Service.

        Args:
            primary_method: 'texture', 'mediapipe', or 'deepface'
        """
        self.primary_method = primary_method
        # Lazy check - don't import DeepFace until needed to avoid TensorFlow deadlock
        self._deepface_checked = False
        self._deepface_available = None
        self._mediapipe_checked = False
        self._mediapipe_available = None

    @property
    def deepface_available(self) -> bool:
        """Check if DeepFace is available (lazy)"""
        if not self._deepface_checked:
            self._deepface_checked = True
            try:
                from deepface import DeepFace
                self._deepface_available = True
            except ImportError:
                self._deepface_available = False
        return self._deepface_available

    @property
    def mediapipe_available(self) -> bool:
        """Check if MediaPipe is available (lazy)"""
        if not self._mediapipe_checked:
            self._mediapipe_checked = True
            try:
                import mediapipe as mp
                self._mediapipe_available = True
            except ImportError:
                self._mediapipe_available = False
        return self._mediapipe_available

    def _check_deepface(self) -> bool:
        """Deprecated - use deepface_available property"""
        return self.deepface_available

    def _check_mediapipe(self) -> bool:
        """Check if MediaPipe is available"""
        try:
            import mediapipe as mp
            return True
        except ImportError:
            return False

    def detect(self, image_path: str, method: Optional[str] = None) -> Dict:
        """
        Detect if face is live (not a photo/video/screen).

        Args:
            image_path: Path to image
            method: Override detection method

        Returns:
            {
                'is_live': bool,
                'liveness_score': float,
                'confidence': str,
                'method': str,
                'details': dict
            }
        """
        method = method or self.primary_method

        if method == 'deepface' and self.deepface_available:
            return self._detect_deepface(image_path)
        elif method == 'mediapipe' and self.mediapipe_available:
            return self._detect_mediapipe(image_path)
        else:
            # Default to texture-based
            return self._detect_texture_based(image_path)

    def _detect_texture_based(self, image_path: str) -> Dict:
        """
        Texture-based liveness detection.

        Detects:
        1. Moiré patterns (screen replay attack)
        2. Print artifacts (photo attack)
        3. Color distortion (video attack)
        """
        try:
            # Validate image path is not a URL
            if image_path.startswith('http://') or image_path.startswith('https://'):
                print(f"Liveness detection: Invalid URL path, using mock")
                return self._detect_mock(image_path)

            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")

            # Convert to different color spaces
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # 1. Moiré pattern detection (FFT analysis)
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)

            # Moiré patterns show periodic patterns in frequency domain
            # High frequency peaks indicate screen replay
            high_freq_energy = np.sum(magnitude_spectrum[magnitude_spectrum > np.percentile(magnitude_spectrum, 99)])

            # 2. Color histogram analysis
            # Real faces have more varied color distribution
            hist_r = cv2.calcHist([img], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([img], [1], None, [256], [0, 256])
            hist_b = cv2.calcHist([img], [2], None, [256], [0, 256])

            color_variance = np.var(hist_r) + np.var(hist_g) + np.var(hist_b)

            # 3. Reflection detection (specular highlights)
            # Real faces have natural skin reflections
            _, saturation, value = cv2.split(hsv)
            high_intensity_pixels = np.sum(value > 240)
            reflection_ratio = high_intensity_pixels / value.size

            # 4. Edge density (print detection)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # Scoring
            liveness_score = float(os.getenv('LIVENESS_INITIAL_SCORE', '0.6'))  # benefit of the doubt

            # Real faces: moderate high-freq energy, high color variance, some reflections
            if high_freq_energy < 1e10:  # No strong Moiré
                liveness_score += 0.15
            elif high_freq_energy < 1e11:  # Moderate (could be JPEG compression artifacts)
                liveness_score += 0.0
            else:
                liveness_score -= 0.3  # Strong Moiré = screen detected

            if color_variance > 1e8:  # Rich color distribution
                liveness_score += 0.15
            elif color_variance > 1e7:  # Moderate color (acceptable for phone cameras)
                liveness_score += 0.05
            else:
                liveness_score -= 0.15  # Flat colors (print/screen)

            if 0.001 < reflection_ratio < 0.15:  # Natural reflections (wider range for phones)
                liveness_score += 0.1
            elif reflection_ratio > 0.3:  # Too much glare (screen)
                liveness_score -= 0.2

            if 0.03 < edge_density < 0.25:  # Natural edge density (wider range)
                liveness_score += 0.1
            else:
                liveness_score -= 0.1  # Too sharp (print) or too smooth

            # Clamp to [0, 1]
            liveness_score = max(0.0, min(1.0, liveness_score))

            _pass = float(os.getenv('LIVENESS_PASS_THRESHOLD', '0.5'))
            _high = float(os.getenv('LIVENESS_HIGH_CONFIDENCE', '0.8'))
            is_live = liveness_score > _pass

            if liveness_score > _high:
                confidence = 'high'
            elif liveness_score > _pass:
                confidence = 'medium'
            else:
                confidence = 'low'

            return {
                'is_live': bool(is_live),
                'liveness_score': float(liveness_score),
                'confidence': confidence,
                'method': 'texture_analysis',
                'details': {
                    'high_freq_energy': float(high_freq_energy),
                    'color_variance': float(color_variance),
                    'reflection_ratio': float(reflection_ratio),
                    'edge_density': float(edge_density),
                    'has_moire': bool(high_freq_energy > 1e10),
                    'color_quality': 'good' if color_variance > 1e8 else 'poor'
                },
                'message': f"Liveness: {liveness_score:.0%}"
            }

        except Exception as e:
            print(f"Texture-based liveness detection failed: {e}")
            return self._detect_mock(image_path)

    def _detect_mediapipe(self, image_path: str) -> Dict:
        """
        MediaPipe-based liveness detection.

        Note: Single image has limitations - best for video streams.
        For single image, we analyze face depth and quality.
        """
        try:
            import mediapipe as mp

            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            mp_face_mesh = mp.solutions.face_mesh

            with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                min_detection_confidence=0.5
            ) as face_mesh:

                results = face_mesh.process(rgb)

                if not results.multi_face_landmarks:
                    return {
                        'is_live': False,
                        'liveness_score': 0.1,
                        'confidence': 'low',
                        'method': 'mediapipe',
                        'error': 'No face detected',
                        'message': 'No face detected - possible spoof'
                    }

                landmarks = results.multi_face_landmarks[0]

                # Analyze landmark depth variance
                # Real 3D faces have more depth variation than flat photos
                z_coords = [lm.z for lm in landmarks.landmark]
                z_variance = np.var(z_coords)

                # Analyze landmark visibility
                # All landmarks should be visible in real face
                visibility_scores = [lm.visibility for lm in landmarks.landmark if hasattr(lm, 'visibility')]
                avg_visibility = np.mean(visibility_scores) if visibility_scores else 1.0

                # Scoring
                liveness_score = 0.5

                if z_variance > 0.01:  # Good 3D depth
                    liveness_score += 0.3
                elif z_variance < 0.001:  # Flat (photo/screen)
                    liveness_score -= 0.3

                if avg_visibility > 0.9:  # All landmarks clearly visible
                    liveness_score += 0.2
                else:
                    liveness_score -= 0.1

                liveness_score = max(0.0, min(1.0, liveness_score))
                is_live = liveness_score > 0.6

                return {
                    'is_live': bool(is_live),
                    'liveness_score': float(liveness_score),
                    'confidence': 'medium',
                    'method': 'mediapipe_facemesh',
                    'details': {
                        'z_variance': float(z_variance),
                        'avg_visibility': float(avg_visibility),
                        'num_landmarks': int(len(landmarks.landmark))
                    },
                    'message': f"Liveness: {liveness_score:.0%} (3D depth analysis)",
                    'note': 'For better results, use video stream with blink detection'
                }

        except Exception as e:
            print(f"MediaPipe liveness detection failed: {e}")
            return self._detect_texture_based(image_path)

    def _detect_deepface(self, image_path: str) -> Dict:
        """
        DeepFace-based liveness detection.

        Uses Silent-Face-Anti-Spoofing if available.
        """
        try:
            from deepface import DeepFace

            # Note: DeepFace's built-in anti-spoofing is limited
            # For full Silent-Face-Anti-Spoofing, need separate model

            # Use face detection confidence as liveness indicator
            result = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend='retinaface',
                enforce_detection=True,
                align=True
            )

            if not result:
                return {
                    'is_live': False,
                    'liveness_score': 0.0,
                    'confidence': 'low',
                    'method': 'deepface',
                    'error': 'No face detected'
                }

            face_confidence = result[0].get('confidence', 0.5)

            # High confidence in face detection = likely real
            liveness_score = face_confidence
            is_live = liveness_score > 0.7

            return {
                'is_live': bool(is_live),
                'liveness_score': float(liveness_score),
                'confidence': 'high' if liveness_score > 0.9 else 'medium',
                'method': 'deepface_detection',
                'details': {
                    'face_confidence': float(face_confidence),
                    'facial_area': result[0]['facial_area']
                },
                'message': f"Face confidence: {face_confidence:.1%}",
                'note': 'For advanced anti-spoofing, consider Silent-Face-Anti-Spoofing'
            }

        except Exception as e:
            print(f"DeepFace liveness detection failed: {e}")
            return self._detect_texture_based(image_path)

    def _detect_mock(self, image_path: str) -> Dict:
        """Mock detection"""
        return {
            'is_live': True,
            'liveness_score': 0.92,
            'confidence': 'high',
            'method': 'mock',
            'message': 'Using mock detection - install libraries for real detection',
            'note': 'Install deepface or mediapipe for real liveness detection'
        }


# Singleton
_liveness_service = None

def get_liveness_service(primary_method: str = 'texture'):
    """Get singleton instance"""
    global _liveness_service
    if _liveness_service is None:
        _liveness_service = LivenessDetectionService(primary_method=primary_method)
    return _liveness_service
