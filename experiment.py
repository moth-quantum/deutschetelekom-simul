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
                
                # This part is working
                rotate(input_values)
                
                # --- START DEVICE CONTROLLER BLOCK ---
                print("Python: Calling device_controller.py subprocess...", file=sys.stderr, flush=True)
                
                # Prepare input data for device_controller.py
                device_input = json.dumps({'knob_values': input_values})
                
                # Call device_controller.py (has toggle for simulation/real hardware)
                result = subprocess.run(['python', 'device_controller.py'], 
                                       input=device_input, 
                                       capture_output=True, 
                                       text=True)
                
                # Check if the subprocess had an error
                if result.stderr:
                    print(f"Python (device_controller.py) Log: {result.stderr}", file=sys.stderr, flush=True)
                
                # Check if the subprocess ran but printed nothing
                if not result.stdout:
                    print("Python (device_controller.py) Warning: Subprocess ran but produced no output (stdout).", file=sys.stderr, flush=True)
                    
                else:
                    # SUCCESS: Send the data back to Node.js
                    print("Python: Subprocess success. Sending data back to Node.", file=sys.stderr, flush=True)
                    print(result.stdout, end='', flush=True)
                # --- END DEVICE CONTROLLER BLOCK ---
                
    except Exception as e:
        print(f"Python Error: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()