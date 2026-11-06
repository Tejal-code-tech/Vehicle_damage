"""
Create new file: ml_model/predict_yolo.py
This file handles YOLOv8 inference and prediction
"""

from ultralytics import YOLO
import numpy as np
from PIL import Image
import os
import cv2
from ml_model.config import (
    MODEL_PATH, 
    IMG_SIZE, 
    CONFIDENCE_THRESHOLD, 
    IOU_THRESHOLD,
    YOLO_CLASS_NAMES,
    CLASS_TO_PART_MAPPING,
    PART_COSTS,
    SEVERITY_MULTIPLIERS,
    LABOR_COST_PERCENTAGE
)

# Global variable to store loaded model (loaded once for efficiency)
_model = None

def load_model():
    """
    Load YOLOv8 model from best.pt
    Model is loaded once and cached for subsequent predictions
    """
    global _model
    
    if _model is not None:
        return _model
    
    if not os.path.exists(MODEL_PATH):
        print(f"⚠️  ERROR: Model file not found at: {MODEL_PATH}")
        print(f"Please place your trained 'best.pt' file in the 'ml_model/model_weights/' folder")
        print(f"and rename it to 'best.pt' or update MODEL_PATH in config.py")
        return None
    
    try:
        print(f"Loading YOLOv8 model from: {MODEL_PATH}")
        _model = YOLO(MODEL_PATH)
        print(f"✅ Model loaded successfully!")
        print(f"Model classes: {_model.names}")
        return _model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None


def estimate_severity(detections):
    """
    Estimate damage severity based on number of detections and confidence
    
    Args:
        detections: List of detection dictionaries
        
    Returns:
        tuple: (severity_level, multiplier)
    """
    num_detections = len(detections)
    avg_confidence = np.mean([d['confidence'] for d in detections]) if detections else 0
    
    # Severity logic
    if num_detections == 0:
        return 'none', 0
    elif num_detections <= 2 and avg_confidence < 0.6:
        return 'minor', SEVERITY_MULTIPLIERS['minor']
    elif num_detections <= 4 or avg_confidence < 0.75:
        return 'moderate', SEVERITY_MULTIPLIERS['moderate']
    else:
        return 'severe', SEVERITY_MULTIPLIERS['severe']


def predict_damage(image_path):
    """
    Main prediction function using YOLOv8 model
    
    Args:
        image_path: Path to the damaged car image
        
    Returns:
        dict: Prediction results in format expected by frontend
    """
    
    # Load model
    model = load_model()
    
    if model is None:
        # Fallback: Return dummy data if model not loaded
        print("⚠️  Model not available. Using dummy predictions.")
        return {
            'is_damaged': True,
            'confidence': 0.85,
            'damaged_parts': ['bumper', 'headlight'],
            'part_costs': {'bumper': 8000, 'headlight': 4500},
            'parts_total': 12500,
            'labor_cost': 2500,
            'total_cost': 15000,
            'severity': 'moderate',
            'severity_multiplier': 1.5,
            'message': 'Model not loaded. Using dummy predictions for testing.',
            'detections': []
        }
    
    try:
        # Run inference
        print(f"\n{'='*60}")
        print(f"Running YOLOv8 inference on: {image_path}")
        print(f"{'='*60}")
        
        results = model(
            image_path,
            imgsz=IMG_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
            verbose=False  # Suppress YOLO output
        )
        
        # Extract detections
        detections = []
        result = results[0]  # First image result
        
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                # Extract box information
                class_id = int(box.cls.cpu().numpy()[0])
                confidence = float(box.conf.cpu().numpy()[0])
                bbox = box.xyxy.cpu().numpy()[0]  # [x1, y1, x2, y2]
                
                # Get class name from model or config
                if hasattr(model, 'names'):
                    class_name = model.names[class_id]
                else:
                    class_name = YOLO_CLASS_NAMES.get(class_id, f'class_{class_id}')
                
                detection = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox.tolist()
                }
                detections.append(detection)
                
                print(f"✅ Detected: {class_name} (confidence: {confidence:.2%})")
        else:
            print("ℹ️  No damage detected")
        
        print(f"{'='*60}\n")
        
        # Check if any damage detected
        if len(detections) == 0:
            return {
                'is_damaged': False,
                'confidence': 0.95,
                'damaged_parts': [],
                'part_costs': {},
                'parts_total': 0,
                'labor_cost': 0,
                'total_cost': 0,
                'severity': 'none',
                'severity_multiplier': 0,
                'message': 'No damage detected. Car appears to be in good condition!',
                'detections': []
            }
        
        # Process detections to extract damaged parts
        damaged_parts_set = set()
        detection_confidences = {}
        
        for detection in detections:
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # Map YOLO class to part name
            part_name = CLASS_TO_PART_MAPPING.get(class_name, class_name)
            
            # Skip if mapped to None (e.g., 'whole' class)
            if part_name is None:
                continue
            
            damaged_parts_set.add(part_name)
            
            # Keep highest confidence for each part
            if part_name not in detection_confidences or confidence > detection_confidences[part_name]:
                detection_confidences[part_name] = confidence
        
        # Convert to list
        damaged_parts = list(damaged_parts_set)
        
        if len(damaged_parts) == 0:
            # Detected something but couldn't map to parts
            return {
                'is_damaged': True,
                'confidence': detections[0]['confidence'],
                'damaged_parts': [],
                'part_costs': {},
                'parts_total': 0,
                'labor_cost': 0,
                'total_cost': 0,
                'severity': 'unknown',
                'severity_multiplier': 1.0,
                'message': 'Damage detected but unable to identify specific parts.',
                'detections': detections
            }
        
        # Estimate severity
        severity, severity_mult = estimate_severity(detections)
        
        # Calculate costs with severity multiplier
        part_costs = {}
        for part in damaged_parts:
            base_cost = PART_COSTS.get(part, 5000)
            adjusted_cost = int(base_cost * severity_mult)
            part_costs[part] = adjusted_cost
        
        parts_total = sum(part_costs.values())
        labor_cost = int(parts_total * LABOR_COST_PERCENTAGE)
        total_cost = parts_total + labor_cost
        
        # Calculate average confidence
        avg_confidence = np.mean([detection_confidences[part] for part in damaged_parts])
        
        print(f"📊 FINAL RESULTS:")
        print(f"   Damaged Parts: {', '.join(damaged_parts)}")
        print(f"   Severity: {severity.upper()}")
        print(f"   Total Cost: ₹{total_cost:,}")
        print(f"   Average Confidence: {avg_confidence:.2%}\n")
        
        return {
            'is_damaged': True,
            'confidence': float(avg_confidence),
            'damaged_parts': damaged_parts,
            'part_costs': part_costs,
            'parts_total': parts_total,
            'labor_cost': labor_cost,
            'total_cost': total_cost,
            'severity': severity,
            'severity_multiplier': severity_mult,
            'message': f'Detected {len(damaged_parts)} damaged part(s) with {severity} severity.',
            'detections': detections,
            'detection_confidences': detection_confidences
        }
        
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return {
            'is_damaged': False,
            'confidence': 0.0,
            'damaged_parts': [],
            'part_costs': {},
            'parts_total': 0,
            'labor_cost': 0,
            'total_cost': 0,
            'severity': 'error',
            'severity_multiplier': 0,
            'message': f'Error during prediction: {str(e)}',
            'detections': []
        }


def save_annotated_image(image_path, detections, output_path=None):
    """
    Optional: Save image with bounding boxes drawn
    Useful for debugging and visualization
    
    Args:
        image_path: Input image path
        detections: List of detections from predict_damage
        output_path: Where to save annotated image (optional)
        
    Returns:
        str: Path to saved annotated image
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Draw bounding boxes
        for detection in detections:
            bbox = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw rectangle
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(img, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save annotated image
        if output_path is None:
            output_path = image_path.replace('.', '_annotated.')
        
        cv2.imwrite(output_path, img)
        print(f"💾 Annotated image saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"Error saving annotated image: {e}")
        return None


# ============================================================================
# Testing function (for standalone testing)
# ============================================================================
if __name__ == '__main__':
    import sys
    
    print("="*70)
    print("YOLOv8 CAR DAMAGE DETECTION - STANDALONE TEST")
    print("="*70)
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        test_image = '../dataset/validation/00-damage/0001.JPEG'
        print(f"No image provided. Using default: {test_image}")
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found: {test_image}")
        print("Usage: python predict_yolo.py <path_to_image>")
    else:
        print(f"\n🚗 Testing with: {test_image}\n")
        
        # Run prediction
        result = predict_damage(test_image)
        
        # Print results
        print("\n" + "="*70)
        print("PREDICTION RESULTS")
        print("="*70)
        print(f"Is Damaged: {result['is_damaged']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Damaged Parts: {', '.join(result['damaged_parts'])}")
        print(f"Severity: {result['severity'].upper()}")
        print(f"Total Cost: ₹{result['total_cost']:,}")
        print(f"Message: {result['message']}")
        print("="*70)
        
        # Save annotated image
        if result.get('detections'):
            save_annotated_image(test_image, result['detections'])