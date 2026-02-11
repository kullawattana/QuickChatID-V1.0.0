#!/usr/bin/env python3
"""
Test if files can be saved and persist in uploads/web_sessions
"""
from pathlib import Path
from PIL import Image
import io
import time

# Create test image
def create_test_image():
    img = Image.new('RGB', (800, 600), (100, 150, 200))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()

# Test save
upload_dir = Path(__file__).parent / 'uploads' / 'web_sessions'
upload_dir.mkdir(parents=True, exist_ok=True)

test_file = upload_dir / 'test_image.jpg'

print(f"📂 Upload directory: {upload_dir}")
print(f"   Exists: {upload_dir.exists()}")
print(f"   Writable: {upload_dir.stat().st_mode & 0o200}")

print(f"\n📝 Saving test image to: {test_file}")
image_data = create_test_image()

with open(test_file, 'wb') as f:
    f.write(image_data)

print(f"   ✓ File saved")
print(f"   ✓ File exists: {test_file.exists()}")
print(f"   ✓ File size: {test_file.stat().st_size} bytes")

# Wait and check again
print(f"\n⏳ Waiting 2 seconds...")
time.sleep(2)

print(f"   ✓ File still exists: {test_file.exists()}")
if test_file.exists():
    print(f"   ✓ File size: {test_file.stat().st_size} bytes")
else:
    print(f"   ❌ File disappeared!")

# List all files
print(f"\n📋 Files in uploads directory:")
for f in upload_dir.glob('*'):
    print(f"   - {f.name} ({f.stat().st_size} bytes)")
