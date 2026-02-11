"""Simple Face Verification Examples"""

from services.face_verification_service import get_face_verification_service
from tools.face_model_comparison import FaceModelComparison

# Show all available models
print("Available Models:")
FaceModelComparison.print_comparison_table()

# Get recommendations
print("\nRecommendations:")
print("Best Accuracy:", FaceModelComparison.recommend_model('accuracy'))
print("Fastest:", FaceModelComparison.recommend_model('speed'))
