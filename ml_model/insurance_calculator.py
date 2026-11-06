"""
Create new file: ml_model/insurance_calculator.py
This handles all insurance-related calculations
"""

import numpy as np

# ============================================================================
# INSURANCE POLICY TYPES
# ============================================================================

INSURANCE_POLICIES = {
    'comprehensive': {
        'name': 'Comprehensive Insurance',
        'coverage_percentage': 90,  # Covers 90% of cost
        'deductible': 2000,  # Fixed deductible
        'max_claim': 500000,  # Max claim amount
        'description': 'Covers collision, theft, fire, and natural disasters'
    },
    'third_party': {
        'name': 'Third Party Insurance',
        'coverage_percentage': 0,  # Does not cover own vehicle damage
        'deductible': 0,
        'max_claim': 0,
        'description': 'Only covers damage to third-party vehicles/property'
    },
    'collision': {
        'name': 'Collision Coverage',
        'coverage_percentage': 80,  # Covers 80% of cost
        'deductible': 5000,  # Higher deductible
        'max_claim': 300000,
        'description': 'Covers damage from collisions with vehicles or objects'
    },
    'own_damage': {
        'name': 'Own Damage Cover',
        'coverage_percentage': 85,  # Covers 85% of cost
        'deductible': 3000,
        'max_claim': 400000,
        'description': 'Covers damage to your own vehicle only'
    }
}


# ============================================================================
# INSURANCE CALCULATION
# ============================================================================

def calculate_insurance_claim(total_cost, policy_type, severity, num_damaged_parts):
    """
    Calculate insurance claim breakdown
    
    Args:
        total_cost: Total repair cost
        policy_type: Type of insurance policy
        severity: Damage severity (minor/moderate/severe)
        num_damaged_parts: Number of damaged parts
        
    Returns:
        dict: Insurance calculation breakdown
    """
    
    # Get policy details
    if policy_type not in INSURANCE_POLICIES:
        policy_type = 'comprehensive'  # Default
    
    policy = INSURANCE_POLICIES[policy_type]
    
    # Calculate base insurance coverage
    coverage_percentage = policy['coverage_percentage']
    deductible = policy['deductible']
    max_claim = policy['max_claim']
    
    # Calculate covered amount
    covered_before_deductible = (total_cost * coverage_percentage) / 100
    
    # Apply deductible
    if covered_before_deductible > deductible:
        insurance_payable = covered_before_deductible - deductible
    else:
        insurance_payable = 0
    
    # Apply max claim limit
    if insurance_payable > max_claim:
        insurance_payable = max_claim
    
    # Calculate user payable (out of pocket)
    user_payable = total_cost - insurance_payable
    
    # Ensure non-negative values
    insurance_payable = max(0, insurance_payable)
    user_payable = max(0, user_payable)
    
    return {
        'total_cost': int(total_cost),
        'insurance_payable': int(insurance_payable),
        'user_payable': int(user_payable),
        'policy_name': policy['name'],
        'policy_type': policy_type,
        'coverage_percentage': coverage_percentage,
        'deductible': deductible,
        'max_claim': max_claim
    }


# ============================================================================
# CLAIM APPROVAL PROBABILITY
# ============================================================================

def calculate_claim_probability(severity, num_damaged_parts, total_cost, policy_type):
    """
    Calculate probability of insurance claim approval using AI-based logic
    
    Factors considered:
    - Damage severity
    - Number of damaged parts
    - Total repair cost
    - Policy type
    
    Returns:
        dict: Probability details
    """
    
    # Base probability
    base_probability = 70  # Start at 70%
    
    # Factor 1: Severity impact
    severity_impact = {
        'minor': 15,      # +15% for minor damage
        'moderate': 0,    # No change for moderate
        'severe': -20,    # -20% for severe damage
        'none': 20        # +20% if no damage
    }
    base_probability += severity_impact.get(severity, 0)
    
    # Factor 2: Number of damaged parts
    if num_damaged_parts == 0:
        parts_impact = 20
    elif num_damaged_parts <= 2:
        parts_impact = 10
    elif num_damaged_parts <= 4:
        parts_impact = 0
    else:
        parts_impact = -15
    base_probability += parts_impact
    
    # Factor 3: Cost vs policy max claim
    policy = INSURANCE_POLICIES.get(policy_type, INSURANCE_POLICIES['comprehensive'])
    max_claim = policy['max_claim']
    
    if max_claim > 0:
        cost_ratio = total_cost / max_claim
        if cost_ratio < 0.3:
            cost_impact = 10  # Low cost claim - good
        elif cost_ratio < 0.7:
            cost_impact = 0   # Medium cost - neutral
        else:
            cost_impact = -15  # High cost claim - reduces probability
        base_probability += cost_impact
    
    # Factor 4: Policy type impact
    policy_impact = {
        'comprehensive': 10,   # Best coverage
        'own_damage': 5,
        'collision': 0,
        'third_party': -30     # Doesn't cover own damage
    }
    base_probability += policy_impact.get(policy_type, 0)
    
    # Ensure probability is between 0-100
    final_probability = max(0, min(100, base_probability))
    
    # Determine claim strength
    if final_probability >= 80:
        strength = 'Strong'
        color = 'success'
        recommendation = 'High chance of approval. Proceed with claim.'
    elif final_probability >= 60:
        strength = 'Moderate'
        color = 'warning'
        recommendation = 'Good chance of approval. Ensure all documents are ready.'
    elif final_probability >= 40:
        strength = 'Weak'
        color = 'warning'
        recommendation = 'Moderate risk. Consider reviewing policy terms.'
    else:
        strength = 'Very Weak'
        color = 'danger'
        recommendation = 'Low chance of approval. May want to avoid claim or upgrade policy.'
    
    return {
        'probability': int(final_probability),
        'strength': strength,
        'color': color,
        'recommendation': recommendation,
        'factors': {
            'severity': severity,
            'num_parts': num_damaged_parts,
            'cost': total_cost,
            'policy': policy_type
        }
    }


# ============================================================================
# GENERATE INSURANCE REPORT DATA
# ============================================================================

def generate_insurance_report_data(prediction_result, insurance_calc, claim_probability, user_info, vehicle_info):
    """
    Prepare all data needed for PDF report generation
    
    Args:
        prediction_result: YOLO prediction output
        insurance_calc: Insurance calculation result
        claim_probability: Claim probability result
        user_info: User details (name, email, etc.)
        vehicle_info: Vehicle details (model, registration, etc.)
        
    Returns:
        dict: Complete report data
    """
    
    from datetime import datetime
    
    report_data = {
        # Report metadata
        'report_id': f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'generated_on': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        # User information
        'user_name': user_info.get('name', 'N/A'),
        'user_email': user_info.get('email', 'N/A'),
        'user_phone': user_info.get('phone', 'N/A'),
        
        # Vehicle information
        'vehicle_model': vehicle_info.get('model', 'N/A'),
        'vehicle_registration': vehicle_info.get('registration', 'N/A'),
        'vehicle_year': vehicle_info.get('year', 'N/A'),
        
        # Damage details
        'is_damaged': prediction_result['is_damaged'],
        'damaged_parts': prediction_result['damaged_parts'],
        'severity': prediction_result['severity'].upper(),
        'confidence': prediction_result['confidence'],
        
        # Cost breakdown
        'part_costs': prediction_result['part_costs'],
        'parts_total': prediction_result['parts_total'],
        'labor_cost': prediction_result['labor_cost'],
        'total_cost': prediction_result['total_cost'],
        
        # Insurance details
        'policy_name': insurance_calc['policy_name'],
        'coverage_percentage': insurance_calc['coverage_percentage'],
        'deductible': insurance_calc['deductible'],
        'insurance_payable': insurance_calc['insurance_payable'],
        'user_payable': insurance_calc['user_payable'],
        
        # Claim probability
        'claim_probability': claim_probability['probability'],
        'claim_strength': claim_probability['strength'],
        'claim_recommendation': claim_probability['recommendation'],
        
        # Image path (for embedding in PDF)
        'damage_image_path': prediction_result.get('image_path', None)
    }
    
    return report_data
