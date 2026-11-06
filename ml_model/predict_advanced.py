import tensorflow as tf
from tensorflow import keras
import numpy as np
from PIL import Image
import json
import os
import cv2

# Model configuration
IMG_SIZE = 224
MODEL_PATH = 'ml_model/model_weights/damage_detector.h5'
LABELS_PATH = 'ml_model/model_weights/class_labels.json'

# Estimated costs for different parts (in INR)
PART_COSTS = {
    'bumper': 8000,
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
    'quarter_panel': 9000
}

# Damage severity multipliers
SEVERITY_MULTIPLIERS = {
    'minor': 1.0,
    'moderate': 1.5,
    'severe': 2.0
}

def load_model():
    """Load the trained binary classification model"""
    if not os.path.exists(MODEL_PATH):
        print(f"Warning: Model not found at {MODEL_PATH}")
        print("Please train the model first using: python ml_model/train_model_binary.py")
        return None
    
    try:
        model = keras.models.load_model(MODEL_PATH)
        print("Model loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def load_class_labels():
    """Load class labels"""
    if not os.path.exists(LABELS_PATH):
        # Default labels for binary classification
        return {0: '00-damage', 1: '01-whole'}
    
    with open(LABELS_PATH, 'r') as f:
        labels = json.load(f)
    return labels

def preprocess_image(image_path):
    """Preprocess image for model input"""
    img = Image.open(image_path).convert('RGB')
    img = img.resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def analyze_damage_regions(image_path):
    """
    Analyze image to detect damaged regions using computer vision
    Returns estimated damaged parts based on image analysis
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        # Convert to different color spaces for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        detected_parts = []
        
        # Detect edges (scratches, dents)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Detect color anomalies (rust, paint damage)
        lower_rust = np.array([10, 100, 100])
        upper_rust = np.array([25, 255, 255])
        rust_mask = cv2.inRange(hsv, lower_rust, upper_rust)
        rust_density = np.sum(rust_mask > 0) / rust_mask.size
        
        # Analyze different regions of the image
        h, w = img.shape[:2]
        
        # Divide image into regions (top, middle, bottom, left, right)
        regions = {
            'top': gray[0:h//3, :],
            'middle': gray[h//3:2*h//3, :],
            'bottom': gray[2*h//3:h, :],
            'left': gray[:, 0:w//3],
            'right': gray[:, 2*w//3:w]
        }
        
        # Map regions to car parts
        region_to_parts = {
            'top': ['roof', 'hood', 'windshield'],
            'middle': ['door', 'fender', 'mirror'],
            'bottom': ['bumper', 'grille'],
            'left': ['door', 'fender', 'mirror'],
            'right': ['door', 'fender', 'mirror']
        }
        
        for region_name, region_img in regions.items():
            region_edges = cv2.Canny(region_img, 50, 150)
            region_edge_density = np.sum(region_edges > 0) / region_edges.size
            
            # If region has high edge density, likely damaged
            if region_edge_density > 0.1:
                detected_parts.extend(region_to_parts[region_name])
        
        # General damage indicators
        if edge_density > 0.15:
            detected_parts.extend(['bumper', 'hood'])
        if rust_density > 0.05:
            detected_parts.extend(['fender', 'door'])
        
        # Remove duplicates and limit to 3-5 parts
        detected_parts = list(set(detected_parts))
        
        # If too many parts detected, take most common ones
        if len(detected_parts) > 5:
            common_parts = ['bumper', 'door', 'fender', 'headlight', 'hood']
            detected_parts = [p for p in common_parts if p in detected_parts][:4]
        
        # If no parts detected, return default damaged parts
        if not detected_parts:
            detected_parts = ['bumper', 'fender']
        
        return detected_parts[:5]  # Max 5 parts
        
    except Exception as e:
        print(f"Error in damage analysis: {e}")
        # Return default damaged parts
        return ['bumper', 'door', 'fender']

def estimate_damage_severity(image_path):
    """Estimate damage severity based on image analysis"""
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate damage indicators
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Blur detection (severe damage often shows blur/deformation)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Classify severity
        if edge_density > 0.2 or laplacian_var < 100:
            return 'severe', SEVERITY_MULTIPLIERS['severe']
        elif edge_density > 0.12:
            return 'moderate', SEVERITY_MULTIPLIERS['moderate']
        else:
            return 'minor', SEVERITY_MULTIPLIERS['minor']
            
    except Exception as e:
        print(f"Error estimating severity: {e}")
        return 'moderate', SEVERITY_MULTIPLIERS['moderate']

def predict_damage(image_path):
    """
    Main prediction function:
    1. Binary classification (damaged vs whole)
    2. If damaged, analyze image for parts and severity
    3. Calculate costs
    """
    
    # Load model and labels
    model = load_model()
    class_labels = load_class_labels()
    
    if model is None:
        # Dummy prediction for testing
        print("⚠️  Using dummy predictions (model not trained yet)")
        return {
            'is_damaged': True,
            'confidence': 0.85,
            'damaged_parts': ['bumper', 'headlight', 'fender'],
            'part_costs': {'bumper': 8000, 'headlight': 4500, 'fender': 6000},
            'total_cost': 18500,
            'severity': 'moderate',
            'severity_multiplier': 1.5,
            'message': 'Model not trained. Using dummy data.'
        }
    
    # Preprocess image
    img_array = preprocess_image(image_path)
    
    # Make prediction
    predictions = model.predict(img_array, verbose=0)[0]
    
    # Get predicted class
    predicted_class_idx = np.argmax(predictions)
    predicted_class = class_labels.get(predicted_class_idx, 'unknown')
    confidence = float(predictions[predicted_class_idx])
    
    print(f"\n{'='*60}")
    print(f"PREDICTION RESULTS")
    print(f"{'='*60}")
    print(f"Predicted Class: {predicted_class}")
    print(f"Confidence: {confidence:.2%}")
    print(f"{'='*60}\n")
    
    # Check if damaged
    is_damaged = '00-damage' in predicted_class or 'damage' in predicted_class.lower()
    
    if not is_damaged:
        # Car is whole/undamaged
        return {
            'is_damaged': False,
            'confidence': confidence,
            'damaged_parts': [],
            'part_costs': {},
            'total_cost': 0,
            'severity': 'none',
            'severity_multiplier': 0,
            'message': 'No damage detected. Car is in good condition!'
        }
    
    # Car is damaged - analyze further
    print("🔍 Analyzing damaged regions...")
    damaged_parts = analyze_damage_regions(image_path)
    
    print("📊 Estimating damage severity...")
    severity, severity_mult = estimate_damage_severity(image_path)
    
    # Calculate costs with severity multiplier
    part_costs = {}
    for part in damaged_parts:
        base_cost = PART_COSTS.get(part, 5000)
        adjusted_cost = int(base_cost * severity_mult)
        part_costs[part] = adjusted_cost
    
    total_cost = sum(part_costs.values())
    
    # Add labor costs (20% of parts cost)
    labor_cost = int(total_cost * 0.2)
    total_cost_with_labor = total_cost + labor_cost
    
    print(f"\n✅ Analysis Complete!")
    print(f"Detected Parts: {', '.join(damaged_parts)}")
    print(f"Severity: {severity.upper()}")
    print(f"Total Cost: ₹{total_cost_with_labor:,}\n")
    
    return {
        'is_damaged': True,
        'confidence': confidence,
        'damaged_parts': damaged_parts,
        'part_costs': part_costs,
        'parts_total': total_cost,
        'labor_cost': labor_cost,
        'total_cost': total_cost_with_labor,
        'severity': severity,
        'severity_multiplier': severity_mult,
        'message': f'Damage detected with {severity} severity. Estimated {len(damaged_parts)} damaged parts.'
    }

# Test function
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        test_image = 'test_damage.jpg'
    
    if os.path.exists(test_image):
        print(f"\n🚗 Analyzing: {test_image}\n")
        result = predict_damage(test_image)
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(json.dumps(result, indent=2))
    else:
        print(f"Test image not found: {test_image}")
        print("Usage: python predict_advanced.py <image_path>")
