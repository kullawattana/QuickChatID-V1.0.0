"""AWS Rekognition Face Matching Service"""

import os
import boto3
from typing import Dict, Optional
from botocore.exceptions import ClientError


class AWSRekognitionService:
    """AWS Rekognition service for face comparison"""

    def __init__(self):
        """Initialize AWS Rekognition client"""
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')

        self._client = None
        self._available = None

    @property
    def is_available(self) -> bool:
        """Check if AWS Rekognition is available"""
        if self._available is None:
            try:
                # Check credentials
                if not self.aws_access_key or not self.aws_secret_key:
                    print("⚠️  AWS credentials not found in environment")
                    self._available = False
                    return False

                # Try to create client
                self._client = boto3.client(
                    'rekognition',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )

                # Test connection by listing collections (lightweight operation)
                self._client.list_collections(MaxResults=1)
                self._available = True
                print(f"✓ AWS Rekognition connected (region: {self.aws_region})")

            except ClientError as e:
                print(f"⚠️  AWS Rekognition error: {e}")
                self._available = False
            except Exception as e:
                print(f"⚠️  AWS Rekognition unavailable: {e}")
                self._available = False

        return self._available

    def compare_faces(
        self,
        source_image_path: str,
        target_image_path: str,
        similarity_threshold: float = 80.0
    ) -> Dict:
        """
        Compare two faces using AWS Rekognition.

        Args:
            source_image_path: Path to source image (e.g., ID card)
            target_image_path: Path to target image (e.g., selfie)
            similarity_threshold: Minimum similarity threshold (0-100)

        Returns:
            {
                'verified': bool,
                'similarity': float (0-1),
                'confidence': float (0-100),
                'backend_used': str,
                'face_matches': list,
                'details': dict
            }
        """
        if not self.is_available:
            raise RuntimeError("AWS Rekognition is not available. Check credentials.")

        try:
            # Read images as bytes
            with open(source_image_path, 'rb') as source_file:
                source_bytes = source_file.read()

            with open(target_image_path, 'rb') as target_file:
                target_bytes = target_file.read()

            # Call AWS Rekognition CompareFaces API
            response = self._client.compare_faces(
                SourceImage={'Bytes': source_bytes},
                TargetImage={'Bytes': target_bytes},
                SimilarityThreshold=similarity_threshold
            )

            # Process results
            face_matches = response.get('FaceMatches', [])

            if face_matches:
                # Get highest similarity match
                best_match = max(face_matches, key=lambda x: x['Similarity'])
                similarity = best_match['Similarity']  # 0-100
                confidence = best_match['Face']['Confidence']  # 0-100

                return {
                    'verified': True,
                    'similarity': similarity / 100.0,  # Convert to 0-1
                    'confidence': confidence,
                    'backend_used': 'aws_rekognition',
                    'face_matches': len(face_matches),
                    'details': {
                        'similarity_percent': similarity,
                        'threshold': similarity_threshold,
                        'bounding_box': best_match['Face']['BoundingBox'],
                        'pose': best_match['Face'].get('Pose', {}),
                        'quality': best_match['Face'].get('Quality', {})
                    }
                }
            else:
                # No match found
                return {
                    'verified': False,
                    'similarity': 0.0,
                    'confidence': 0.0,
                    'backend_used': 'aws_rekognition',
                    'face_matches': 0,
                    'details': {
                        'message': 'No face match found',
                        'unmatched_faces': len(response.get('UnmatchedFaces', []))
                    }
                }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']

            return {
                'verified': False,
                'similarity': 0.0,
                'confidence': 0.0,
                'backend_used': 'aws_rekognition',
                'error': f"{error_code}: {error_message}",
                'details': {}
            }

        except FileNotFoundError as e:
            return {
                'verified': False,
                'similarity': 0.0,
                'confidence': 0.0,
                'backend_used': 'aws_rekognition',
                'error': f"Image file not found: {e}",
                'details': {}
            }

        except Exception as e:
            return {
                'verified': False,
                'similarity': 0.0,
                'confidence': 0.0,
                'backend_used': 'aws_rekognition',
                'error': str(e),
                'details': {}
            }

    def detect_faces(self, image_path: str) -> Dict:
        """
        Detect faces in an image using AWS Rekognition.

        Args:
            image_path: Path to image file

        Returns:
            {
                'face_count': int,
                'faces': list of face details
            }
        """
        if not self.is_available:
            raise RuntimeError("AWS Rekognition is not available. Check credentials.")

        try:
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()

            response = self._client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )

            faces = response.get('FaceDetails', [])

            return {
                'face_count': len(faces),
                'faces': [
                    {
                        'confidence': face['Confidence'],
                        'bounding_box': face['BoundingBox'],
                        'age_range': face.get('AgeRange', {}),
                        'gender': face.get('Gender', {}),
                        'emotions': face.get('Emotions', []),
                        'quality': face.get('Quality', {})
                    }
                    for face in faces
                ]
            }

        except Exception as e:
            return {
                'face_count': 0,
                'faces': [],
                'error': str(e)
            }


# Global instance (lazy initialization)
_rekognition_service: Optional[AWSRekognitionService] = None


def get_rekognition_service() -> AWSRekognitionService:
    """Get or create AWS Rekognition service instance"""
    global _rekognition_service
    if _rekognition_service is None:
        _rekognition_service = AWSRekognitionService()
    return _rekognition_service
