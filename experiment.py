import sys
import json
import time # So we can simulate a long experiment
import atexit
import subprocess

# === HARDWARE SETUP ===
# (Remote) The motor polarisers will go into the setup process.
# Attach the hardware, import the necessary libraries, etc...

# Takes three values from TouchDesigner
def rotate(knob_data):
    """
    Takes 3 values, calls the experiment script within the same home structure of the Node.js app, calls the script which calculates 4 values.
    """
    # Log to Heroku that we started
    print(f"Python: Received values {knob_data}", file=sys.stderr, flush=True)
    
    # === EXPERIMENT === Here it will call the Python script which rotates the motorpols. 
    print("Python: Changing the angles...", file=sys.stderr, flush=True)
    
    # === EXPERIMENT === Here, it might call the script which runs the experiment, OR it could just be included right here.

# Wrapper function: This loop listens for data from Node.js
def main():
    try:
        for line in sys.stdin: # Reads data piped from Node.js
            if not line:
                continue
            
            user_input = json.loads(line)
            input_values = user_input.get('knob_values', [])
            
            if len(input_values) == 3:
                
                # rotate the knobs
                rotate(input_values)
                
                # Call the four.py script to generate the 4 values
                result = subprocess.run(['python', 'four.py'], capture_output=True, text=True)
                
                # This print() sends the JSON string to Node.js's stdout
                print(result.stdout, end='', flush=True)
                
    except Exception as e:
        print(f"Python Error: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()