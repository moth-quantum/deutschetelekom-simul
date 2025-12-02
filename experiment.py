import sys
import json
import time
import atexit
import subprocess
import os
import requests

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
                
                # Check if we should use bridge (remote Windows machine)
                bridge_url = os.environ.get('BRIDGE_URL', '').strip()
                
                # Get current mode from environment variable set by Node.js
                use_hardware = os.environ.get('USE_REAL_HARDWARE', 'false').lower() == 'true'
                
                # HYBRID MODE: Forward to bridge if URL is set and hardware mode is ON
                if bridge_url and use_hardware:
                    print(f"Python: Hardware mode + Bridge detected. Forwarding to: {bridge_url}", file=sys.stderr, flush=True)
                    
                    try:
                        response = requests.post(
                            f"{bridge_url}/api/hardware/execute",
                            json={'knob_values': input_values},
                            timeout=130  # 130 second timeout
                        )
                        
                        if response.status_code == 200:
                            result_data = response.json()
                            if result_data.get('success'):
                                print("Python: Bridge success. Sending data back to Node.", file=sys.stderr, flush=True)
                                print(json.dumps(result_data['data']), flush=True)
                            else:
                                print(f"Python: Bridge error: {result_data.get('error')}", file=sys.stderr, flush=True)
                        else:
                            print(f"Python: Bridge HTTP error: {response.status_code}", file=sys.stderr, flush=True)
                    
                    except requests.exceptions.Timeout:
                        print("Python: Bridge timeout (>130s)", file=sys.stderr, flush=True)
                    except Exception as e:
                        print(f"Python: Bridge connection error: {e}", file=sys.stderr, flush=True)
                
                # LOCAL MODE: Run device_controller.py locally (simulation or if no bridge)
                else:
                    if bridge_url and not use_hardware:
                        print("Python: Bridge URL set but in SIMULATION mode. Running locally.", file=sys.stderr, flush=True)
                    elif not bridge_url and use_hardware:
                        print("Python: Hardware mode ON but no BRIDGE_URL. Running locally (will use simulation).", file=sys.stderr, flush=True)
                    else:
                        print("Python: Calling local device_controller.py...", file=sys.stderr, flush=True)
                    
                    device_input = json.dumps({'knob_values': input_values})
                    
                    result = subprocess.run(['python', 'device_controller.py'], 
                                           input=device_input, 
                                           capture_output=True, 
                                           text=True)
                    
                    if result.stderr:
                        print(f"Python (device_controller.py) Log: {result.stderr}", file=sys.stderr, flush=True)
                    
                    if not result.stdout:
                        print("Python (device_controller.py) Warning: No output.", file=sys.stderr, flush=True)
                    else:
                        print("Python: Subprocess success. Sending data back to Node.", file=sys.stderr, flush=True)
                        print(result.stdout, end='', flush=True)
                
                # --- END DEVICE CONTROLLER BLOCK ---
                
    except Exception as e:
        print(f"Python Error: {e}", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()