import time
import json
import random
import sys
import math

def generate_numerical_data(angles=None):
    """
    Generate numerical data simulating quantum entanglement behavior.
    
    Args:
        angles: List of 3 angle values (in degrees) from MIDI knobs
                If None, uses random angles
    
    Returns:
        Four coincidence values representing channel pairs:
        - Two values close to 1.0 and two close to 0.0 indicate entangled state
        - Other patterns indicate non-entangled or different correlations
    """
    
    # Use provided angles or generate random ones
    if angles is None or len(angles) < 3:
        angles = [random.uniform(0, 180) for _ in range(3)]
    
    # Convert to radians for calculations
    theta1 = math.radians(angles[0])
    theta2 = math.radians(angles[1])
    theta3 = math.radians(angles[2])
    
    # Calculate angle differences (important for entanglement correlation)
    delta_12 = abs(theta1 - theta2)
    delta_13 = abs(theta1 - theta3) 
    delta_23 = abs(theta2 - theta3)
    
    # Determine if this should show entangled state
    # Based on angle configurations and random chance
    # Entangled state appears when angles are in certain relationships
    entangled_probability = math.cos(delta_12) ** 2
    is_entangled = random.random() < entangled_probability
    
    if is_entangled:
        # ENTANGLED STATE: Two values close to 1.0, two close to 0.0
        # This simulates Bell state correlations
        
        # Values close to 1.0 (with small noise)
        val1 = random.uniform(0.85, 0.99)
        val2 = random.uniform(0.85, 0.99)
        
        # Values close to 0.0 (with small noise)
        val3 = random.uniform(0.01, 0.15)
        val4 = random.uniform(0.01, 0.15)
        
        # Randomly swap which pair is high/low for variation
        if random.random() < 0.5:
            val1, val3 = val3, val1
            val2, val4 = val4, val2
            
    else:
        # NON-ENTANGLED STATE: More distributed values
        # Simulate classical correlation or mixed state
        
        # Use quantum-inspired formulas
        val1 = 0.5 + 0.3 * math.cos(2 * theta1) + random.uniform(-0.1, 0.1)
        val2 = 0.5 + 0.3 * math.cos(2 * theta2) + random.uniform(-0.1, 0.1)
        val3 = 0.5 + 0.3 * math.sin(theta1 + theta2) + random.uniform(-0.1, 0.1)
        val4 = 0.5 + 0.3 * math.sin(theta1 - theta3) + random.uniform(-0.1, 0.1)
        
        # Clamp to [0, 1] range
        val1 = max(0.0, min(1.0, val1))
        val2 = max(0.0, min(1.0, val2))
        val3 = max(0.0, min(1.0, val3))
        val4 = max(0.0, min(1.0, val4))
    
    # Format the data
    data = {
        "entanglement": [val1, val2, val3, val4],
        "angles": angles[:3],
        "entangled": is_entangled  # Metadata for debugging
    }
    
    # Output as JSON (Node.js will parse this)
    print(json.dumps(data), flush=True)

if __name__ == "__main__":
    # Check if angles are provided via command line
    if len(sys.argv) > 3:
        try:
            angles = [float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])]
            generate_numerical_data(angles)
        except ValueError:
            print("Error: Angles must be numbers", file=sys.stderr)
            generate_numerical_data()
    else:
        generate_numerical_data()