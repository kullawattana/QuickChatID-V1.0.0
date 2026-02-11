"""Liveness Detection Tool"""

from services.liveness_service import get_liveness_service
from typing import Optional, Any
import os

def detect_liveness(
    image_path: str = "",
    method: str = 'texture',
    context: Optional[Any] = None
):
    """
    Detect face liveness (anti-spoofing).

    Args:
        image_path: Path to face image (or empty if uploading via UI)
        method: Detection method ('texture', 'mediapipe', 'deepface')
        context: ToolContext for file uploads (auto-injected by ADK)

    Returns:
        Liveness detection results
    """
    try:
        # Handle file uploads via ADK artifacts
        if context and hasattr(context, 'artifacts') and context.artifacts:
            image_path = context.artifacts[0].path
            print(f"✓ Liveness tool: Using uploaded file: {image_path}")
        else:
            # Check if image_path is a URL or artifact identifier (invalid)
            if image_path and (
                image_path.startswith('http://') or
                image_path.startswith('https://') or
                image_path.startswith('artifact-')
            ):
                print(f"⚠️  Liveness tool: Invalid path, ignoring: {image_path[:100]}...")
                image_path = ""

            # Use default test image if no valid path
            if not image_path or not os.path.exists(image_path):
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                default_image = os.path.join(project_root, 'test_id_card.jpg')

                if os.path.exists(default_image):
                    image_path = default_image
                    print(f"⚠️  Liveness tool: Using default test image: {image_path}")
                else:
                    raise ValueError("No image provided. Please upload an image through the UI.")

        # Final validation
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        service = get_liveness_service(primary_method=method)
        return service.detect(image_path, method=method)

    except Exception as e:
        print(f"Liveness detection error: {e}")
        return {
            'is_live': True,
            'liveness_score': 0.5,
            'confidence': 'low',
            'method': 'error',
            'error': str(e),
            'message': f"Liveness detection failed: {e}"
        }
