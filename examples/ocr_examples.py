"""
OCR Examples for Thai ID Cards
Demonstrates PaddleOCR, EasyOCR, Tesseract
"""

from tools.ocr_tool import extract_thai_id, validate_thai_id_number, preprocess_id_card_image
from tools.ocr_comparison import OCRComparison

def example_1_basic_extraction():
    """Example 1: Basic Thai ID extraction"""
    print("\n" + "="*80)
    print("Example 1: Basic Extraction with PaddleOCR")
    print("="*80)
    
    # Extract using PaddleOCR (best for Thai)
    result = extract_thai_id('path/to/id_card.jpg')
    
    print(f"\nExtracted Data:")
    print(f"  ID Number: {result['id_number']}")
    print(f"  ID Valid: {result['id_valid']}")
    print(f"  Name (Thai): {result['name_th']}")
    print(f"  Name (English): {result['name_en']}")
    print(f"  Date of Birth: {result['date_of_birth']}")
    print(f"  Confidence: {result['confidence_score']:.2%}")
    print(f"  Backend: {result['backend']}")


def example_2_compare_engines():
    """Example 2: Compare OCR engines"""
    print("\n" + "="*80)
    print("Example 2: Compare OCR Engines")
    print("="*80)
    
    image_path = 'path/to/id_card.jpg'
    
    for backend in ['paddleocr', 'easyocr', 'tesseract']:
        print(f"\n{backend.upper()}:")
        result = extract_thai_id(image_path, backend=backend)
        print(f"  Confidence: {result['confidence_score']:.2%}")
        print(f"  ID Number: {result['id_number']}")
        print(f"  Success: {result['success']}")


def example_3_with_preprocessing():
    """Example 3: Extract with preprocessing"""
    print("\n" + "="*80)
    print("Example 3: With Image Preprocessing")
    print("="*80)
    
    # Preprocess first
    preprocessed_path = preprocess_id_card_image('path/to/id_card.jpg')
    print(f"Preprocessed image saved to: {preprocessed_path}")
    
    # Then extract
    result = extract_thai_id(preprocessed_path, preprocess=False)
    print(f"\nConfidence: {result['confidence_score']:.2%}")
    print(f"ID Number: {result['id_number']}")


def example_4_validate_id():
    """Example 4: Validate ID number"""
    print("\n" + "="*80)
    print("Example 4: Validate ID Number Checksum")
    print("="*80)
    
    test_ids = [
        '1234567890123',  # Invalid
        '1234567890125',  # Invalid
        '1100400112344',  # Valid (example)
    ]
    
    for id_num in test_ids:
        valid = validate_thai_id_number(id_num)
        print(f"{id_num}: {'✅ Valid' if valid else '❌ Invalid'}")


def example_5_benchmarking():
    """Example 5: Benchmark OCR engines"""
    print("\n" + "="*80)
    print("Example 5: Benchmark OCR Engines")
    print("="*80)
    
    results_df = OCRComparison.benchmark(
        image_path='path/to/id_card.jpg',
        engines=['paddleocr', 'easyocr', 'tesseract']
    )
    
    print("\n" + results_df.to_string(index=False))


def example_6_recommendations():
    """Example 6: Get OCR recommendations"""
    print("\n" + "="*80)
    print("Example 6: OCR Recommendations")
    print("="*80)
    
    # Best for Thai
    best_thai = OCRComparison.recommend_engine('accuracy')
    print(f"\nBest for Thai ID Cards:")
    print(f"  Engine: {best_thai['engine']}")
    print(f"  Accuracy: {best_thai['accuracy']:.2%}")
    print(f"  Reason: {best_thai['reason']}")
    
    # Fastest
    fastest = OCRComparison.recommend_engine('speed')
    print(f"\nFastest:")
    print(f"  Engine: {fastest['engine']}")
    print(f"  Reason: {fastest['reason']}")


def example_7_production_pipeline():
    """Example 7: Complete production pipeline"""
    print("\n" + "="*80)
    print("Example 7: Production Pipeline")
    print("="*80)
    
    image_path = 'path/to/id_card.jpg'
    
    # Step 1: Preprocess
    print("\n1. Preprocessing image...")
    preprocessed = preprocess_id_card_image(image_path)
    print(f"   ✓ Saved to: {preprocessed}")
    
    # Step 2: Extract with PaddleOCR
    print("\n2. Extracting with PaddleOCR...")
    result = extract_thai_id(preprocessed, backend='paddleocr')
    print(f"   ✓ Confidence: {result['confidence_score']:.2%}")
    
    # Step 3: Validate ID
    print("\n3. Validating ID number...")
    if result['id_number']:
        valid = validate_thai_id_number(result['id_number'])
        print(f"   ✓ ID {result['id_number']}: {'Valid' if valid else 'Invalid'}")
    
    # Step 4: Check required fields
    print("\n4. Checking required fields...")
    required = ['id_number', 'name_th', 'date_of_birth']
    missing = [f for f in required if not result.get(f)]
    
    if missing:
        print(f"   ⚠️  Missing: {', '.join(missing)}")
    else:
        print(f"   ✓ All required fields present")
    
    # Step 5: Quality check
    print("\n5. Quality check...")
    if result['confidence_score'] < 0.6:
        print(f"   ⚠️  Low confidence - may need manual review")
    else:
        print(f"   ✓ Good quality")
    
    # Final decision
    print("\n6. Final Decision:")
    passed = (
        result['success'] and
        result.get('id_valid', False) and
        result['confidence_score'] >= 0.6 and
        not missing
    )
    print(f"   Result: {'✅ PASSED' if passed else '❌ FAILED'}")


def show_all_engines():
    """Show comparison of all OCR engines"""
    OCRComparison.print_comparison_table()


if __name__ == "__main__":
    print("\n🚀 OCR Examples for Thai ID Cards")
    print("="*80)
    print("\nAvailable examples:")
    print("  1. Basic extraction")
    print("  2. Compare engines")
    print("  3. With preprocessing")
    print("  4. Validate ID number")
    print("  5. Benchmarking")
    print("  6. Recommendations")
    print("  7. Production pipeline")
    print("  8. Show all engines")
    print("\nNote: Update image paths before running")
    
    # Show engine comparison
    show_all_engines()
