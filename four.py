import time
import json
import numpy as np
import sys

# One-shot data generation for TouchDesigner
def generate_numerical_data():
    """Generate numerical data for TouchDesigner visualization"""
    # Generate various types of numerical data
    data = {
        "entanglement": np.random.rand(4).tolist(),  # four random values [0, 1]
    }
    
    # Output as JSON (Node.js will parse this)
    print(json.dumps(data), flush=True)

if __name__ == "__main__":
    generate_numerical_data()