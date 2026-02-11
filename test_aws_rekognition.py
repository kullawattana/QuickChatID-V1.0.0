"""Test AWS Rekognition Integration"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.aws_rekognition_service import get_rekognition_service

def test_aws_rekognition():
    """Test AWS Rekognition service availability and functionality"""

    print("=" * 60)
    print("AWS Rekognition Integration Test")
    print("=" * 60)

    # Check environment variables
    print("\n1. Checking environment variables:")
    print(f"   AWS_ACCESS_KEY_ID: {'✓ Set' if os.getenv('AWS_ACCESS_KEY_ID') else '✗ Not set'}")
    print(f"   AWS_SECRET_ACCESS_KEY: {'✓ Set' if os.getenv('AWS_SECRET_ACCESS_KEY') else '✗ Not set'}")
    print(f"   AWS_REGION: {os.getenv('AWS_REGION', 'us-east-1 (default)')}")

    # Initialize service
    print("\n2. Initializing AWS Rekognition service:")
    rekognition = get_rekognition_service()

    # Check availability
    print("\n3. Checking service availability:")
    is_available = rekognition.is_available

    if is_available:
        print("   ✓ AWS Rekognition is available and ready!")

        # Test with sample images (if they exist)
        test_image = Path(__file__).parent / 'test_id_card.jpg'
        if test_image.exists():
            print(f"\n4. Testing face detection with: {test_image}")
            result = rekognition.detect_faces(str(test_image))
            print(f"   Face count: {result['face_count']}")

            if result['face_count'] > 0:
                print("   ✓ Face detection working!")
            else:
                print("   ⚠️  No faces detected in test image")
        else:
            print(f"\n4. Test image not found: {test_image}")
    else:
        print("   ✗ AWS Rekognition is NOT available")
        print("\n   To enable AWS Rekognition:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your AWS credentials:")
        print("      AWS_ACCESS_KEY_ID=your_access_key")
        print("      AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("      AWS_REGION=us-east-1")
        print("   3. Restart the ADK server")
        print("\n   Without AWS credentials, the system will use MOCK data for face matching")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_aws_rekognition()
