import time
import json
import numpy as np
import sys

# Continuous data generation for TouchDesigner
def generate_numerical_data():
    """Generate numerical data for TouchDesigner visualization"""
    while True:
        # Generate various types of numerical data
        data = {
            "entanglement": np.random.rand(4).tolist(),  # four random values [0, 1]
        }
        
        # Output as JSON (Node.js will parse this)
        print(json.dumps(data), flush=True)
        
        # Wait before sending next batch (adjust for your needs)
        time.sleep(1)  # 1 times per second

if __name__ == "__main__":
    try:
        print(json.dumps({"status": "Python script started"}), flush=True, file=sys.stderr)
        generate_numerical_data()
    except KeyboardInterrupt:
        print(json.dumps({"status": "Python script stopped"}), flush=True, file=sys.stderr)
        sys.exit(0)