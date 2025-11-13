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
            "timestamp": time.time(),
            "random_values": np.random.rand(10).tolist(),  # 10 random values 0-1
            "sine_wave": [float(np.sin(i * 0.1 + time.time())) for i in range(20)],
            "single_value": float(np.random.uniform(0, 100)),
            "quantum_simulation": {
                "amplitude": float(np.random.rand()),
                "phase": float(np.random.uniform(0, 2 * np.pi)),
                "frequency": float(np.random.uniform(1, 10))
            }
        }
        
        # Output as JSON (Node.js will parse this)
        print(json.dumps(data), flush=True)
        
        # Wait before sending next batch (adjust for your needs)
        time.sleep(0.1)  # 10 times per second

if __name__ == "__main__":
    try:
        print(json.dumps({"status": "Python script started"}), flush=True, file=sys.stderr)
        generate_numerical_data()
    except KeyboardInterrupt:
        print(json.dumps({"status": "Python script stopped"}), flush=True, file=sys.stderr)
        sys.exit(0)