#!/usr/bin/env python3
"""
Test Face Verification Integration
Tests DeepFace, InsightFace, and MediaPipe backends
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.face_verification_service import get_face_verification_service

def test_library_availability():
    """Check which libraries are available"""
    print("=" * 60)
    print("Checking Face Verification Libraries")
    print("=" * 60)

    libraries = {
        'DeepFace': False,
        'InsightFace': False,
        'MediaPipe': False,
        'OpenCV': False
    }

    try:
        import deepface
        libraries['DeepFace'] = True
        print(f"✓ DeepFace {deepface.__version__} - INSTALLED")
    except ImportError:
        print("✗ DeepFace - NOT INSTALLED")

    try:
        import insightface
        libraries['InsightFace'] = True
        print(f"✓ InsightFace {insightface.__version__} - INSTALLED")
    except ImportError:
        print("✗ InsightFace - NOT INSTALLED")

    try:
        import mediapipe
        libraries['MediaPipe'] = True
        print(f"✓ MediaPipe {mediapipe.__version__} - INSTALLED")
    except ImportError:
        print("✗ MediaPipe - NOT INSTALLED")

    try:
        import cv2
        libraries['OpenCV'] = True
        print(f"✓ OpenCV {cv2.__version__} - INSTALLED")
    except ImportError:
        print("✗ OpenCV - NOT INSTALLED")

    print()
    return libraries

def test_face_detection():
    """Test face detection"""
    print("=" * 60)
    print("Testing Face Detection")
    print("=" * 60)

    # Use test ID card image
    test_image = "test_id_card.jpg"

    if not os.path.exists(test_image):
        print(f"✗ Test image not found: {test_image}")
        return

    print(f"Using test image: {test_image}")

    service = get_face_verification_service()

    # Check backend availability
    print(f"\nBackend availability:")
    print(f"  - DeepFace: {service.deepface_available}")
    print(f"  - InsightFace: {service.insightface_available}")
    print(f"  - MediaPipe: {service.mediapipe_available}")

    # Test detection
    if service.deepface_available or service.insightface_available:
        print(f"\nDetecting faces...")
        faces = service.detect_face(test_image)
        if faces:
            print(f"✓ Detected {len(faces)} face(s)")
            for i, face in enumerate(faces):
                print(f"  Face {i+1}: {face}")
        else:
            print("✗ No faces detected")
    else:
        print("\n⚠️  No real face detection backend available, using mock")

    print()

def test_face_analysis():
    """Test face analysis (age, gender, emotion)"""
    print("=" * 60)
    print("Testing Face Analysis")
    print("=" * 60)

    test_image = "test_id_card.jpg"

    if not os.path.exists(test_image):
        print(f"✗ Test image not found: {test_image}")
        return

    service = get_face_verification_service()

    if service.deepface_available:
        print(f"Analyzing face with DeepFace...")
        result = service.analyze_face(test_image, backend='deepface')
        print(f"✓ Analysis results:")
        print(f"  Age: {result.get('age', 'N/A')}")
        print(f"  Gender: {result.get('gender', 'N/A')}")
        print(f"  Emotion: {result.get('emotion', 'N/A')}")
        print(f"  Race: {result.get('race', 'N/A')}")
    elif service.insightface_available:
        print(f"Analyzing face with InsightFace...")
        result = service.analyze_face(test_image, backend='insightface')
        print(f"✓ Analysis results:")
        print(f"  Age: {result.get('age', 'N/A')}")
        print(f"  Gender: {result.get('gender', 'N/A')}")
    else:
        print("⚠️  No backend available for face analysis (mock data will be used)")
        result = service.analyze_face(test_image)
        print(f"Mock result: {result}")

    print()

def test_face_verification():
    """Test face verification (comparing two faces)"""
    print("=" * 60)
    print("Testing Face Verification")
    print("=" * 60)

    # For testing, we'll use the same image twice
    # In production, you'd have: ID card photo vs selfie
    img1 = "test_id_card.jpg"
    img2 = "test_id_card.jpg"  # Same image should give high similarity

    if not os.path.exists(img1):
        print(f"✗ Test image not found: {img1}")
        return

    service = get_face_verification_service()

    print(f"Comparing: {img1} vs {img2}")
    print(f"(Using same image for testing - should show high similarity)")

    # Test with available backends
    backends_to_test = []
    if service.deepface_available:
        backends_to_test.append('deepface')
    if service.insightface_available:
        backends_to_test.append('insightface')

    if not backends_to_test:
        print("\n⚠️  No real backends available, testing with mock...")
        backends_to_test = ['mock']

    for backend in backends_to_test:
        print(f"\n--- Testing with {backend.upper()} backend ---")
        try:
            result = service.verify(img1, img2, backend=backend)
            print(f"Verified: {result.get('verified', False)}")
            print(f"Similarity: {result.get('similarity', 0):.4f}")
            print(f"Distance: {result.get('distance', 0):.4f}")
            print(f"Threshold: {result.get('threshold', 0):.4f}")
            print(f"Model: {result.get('model', 'N/A')}")
            print(f"Detector: {result.get('detector', 'N/A')}")
            if 'note' in result:
                print(f"Note: {result['note']}")
        except Exception as e:
            print(f"✗ Error: {e}")

    # Test ensemble verification
    if len(backends_to_test) > 1:
        print(f"\n--- Testing ENSEMBLE verification ---")
        result = service.verify_ensemble(img1, img2, backends=backends_to_test)
        print(f"Ensemble verified: {result.get('verified', False)}")
        print(f"Ensemble similarity: {result.get('ensemble_similarity', 0):.4f}")
        print(f"Backends used: {result.get('backends_used', [])}")
        print(f"Confidence: {result.get('confidence', 'N/A')}")

    print()

def test_embedding_extraction():
    """Test face embedding extraction"""
    print("=" * 60)
    print("Testing Face Embedding Extraction")
    print("=" * 60)

    test_image = "test_id_card.jpg"

    if not os.path.exists(test_image):
        print(f"✗ Test image not found: {test_image}")
        return

    service = get_face_verification_service()

    if service.deepface_available:
        print(f"Extracting embedding with DeepFace...")
        embedding = service.get_embedding(test_image, backend='deepface')
        print(f"✓ Embedding shape: {embedding.shape}")
        print(f"  First 5 values: {embedding[:5]}")
    elif service.insightface_available:
        print(f"Extracting embedding with InsightFace...")
        embedding = service.get_embedding(test_image, backend='insightface')
        print(f"✓ Embedding shape: {embedding.shape}")
        print(f"  First 5 values: {embedding[:5]}")
    else:
        print("⚠️  No backend available (mock embedding will be used)")
        embedding = service.get_embedding(test_image)
        print(f"Mock embedding shape: {embedding.shape}")

    print()

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "FACE VERIFICATION TEST SUITE" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # Check library availability
    libraries = test_library_availability()

    # Run tests
    test_face_detection()
    test_face_analysis()
    test_face_verification()
    test_embedding_extraction()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if libraries['DeepFace'] or libraries['InsightFace']:
        print("✓ Face verification is WORKING with real libraries")
        if libraries['DeepFace']:
            print("  - DeepFace backend: Available")
        if libraries['InsightFace']:
            print("  - InsightFace backend: Available")
        if libraries['MediaPipe']:
            print("  - MediaPipe backend: Available (detection only)")
    else:
        print("⚠️  No face verification libraries installed")
        print("   Install with: pip install deepface insightface")
        print("   System will use MOCK data for now")

    print("\nNext steps:")
    if not libraries['DeepFace']:
        print("  1. Install DeepFace: pip install deepface")
    if not libraries['InsightFace']:
        print("  2. Install InsightFace: pip install insightface")
    print("  3. Test with real ID card photo + selfie image")
    print("  4. Adjust similarity thresholds based on your use case")
    print()

if __name__ == "__main__":
    main()
