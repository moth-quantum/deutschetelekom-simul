import time
import json
import random  # We'll use this instead of numpy
import sys

# One-shot data generation for TouchDesigner
def generate_numerical_data():
    """
    Generate numerical data where the first pair is correlated
    (val1, val2 = 1.0 - val1) and val1 is capped.
    """
    
    # --- Your new logic ---
    
    # 1. Define the maximum value for the first number
    max_cap = 0.78
    
    # 2. Generate the first pair
    val1 = random.uniform(0.0, max_cap)
    val2 = 1.0 - val1
    
    # 3. Generate the second pair (e.g., just random)
    val3 = random.random()  # random.random() gives a float [0.0, 1.0)
    val4 = random.random()
    
    # --- End of new logic ---
    
    # Format the data
    data = {
        "entanglement": [val1, val2, val3, val4],
    }
    
    # Output as JSON (Node.js will parse this)
    print(json.dumps(data), flush=True)

if __name__ == "__main__":
    generate_numerical_data()