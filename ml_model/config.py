
import os

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Path to your trained YOLOv8 model
MODEL_PATH = 'ml_model/model_weights/best.pt'

# Image size for inference (should match training size)
IMG_SIZE = 640  # YOLOv8 default, change if you trained with different size

# Confidence threshold for detections
CONFIDENCE_THRESHOLD = 0.25  # Detections below this will be ignored

# IoU threshold for Non-Maximum Suppression
IOU_THRESHOLD = 0.45

# ============================================================================
# CLASS NAMES MAPPING
# ============================================================================
# IMPORTANT: Update this based on YOUR trained model's classes
# These should match the class names you used during training in data.yaml

# Example 1: If you trained on specific damage types
YOLO_CLASS_NAMES = {
    0: 'bumper_damage',
    1: 'door_damage',
    2: 'headlight_damage',
    3: 'hood_damage',
    4: 'fender_damage'
}

# Example 2: If you trained on binary (damaged/whole) or other classes
# Uncomment and modify as needed:
# YOLO_CLASS_NAMES = {
#     0: 'damage',
#     1: 'whole'
# }

# Map YOLO detected classes to part names for cost calculation
# If YOLO detects "bumper_damage", we map it to "bumper" for pricing
CLASS_TO_PART_MAPPING = {
    'bumper_damage': 'bumper',
    'door_damage': 'door',
    'fender_damage': 'fender',
    'headlight_damage': 'headlight',
    'hood_damage': 'hood',
    'mirror_damage': 'mirror',
    'windshield_damage': 'windshield',
    'trunk_damage': 'trunk',
    'grille_damage': 'grille',
    'taillight_damage': 'taillight',
    # If you have binary classification:
    'damage': 'general_damage',
    'whole': None  # No damage
}

# ============================================================================
# COST ESTIMATION (Same as before, but can be customized)
# ============================================================================

PART_COSTS = {
    'bumper': 800,
    'door': 12000,
    'headlight': 4500,
    'hood': 10000,
    'windshield': 7000,
    'mirror': 3000,
    'fender': 6000,
    'taillight': 3500,
    'grille': 4000,
    'trunk': 8500,
    'roof': 15000,
    'quarter_panel': 9000,
    'general_damage': 5000  # Default for unspecified damage
}

# Severity multipliers based on number of detections and confidence
SEVERITY_MULTIPLIERS = {
    'minor': 1.0,      # 1-2 detections, low confidence
    'moderate': 1.5,   # 2-4 detections, medium confidence
    'severe': 2.0      # 5+ detections, high confidence
}

# Labor cost percentage
LABOR_COST_PERCENTAGE = 0.20  # 20% of parts cost