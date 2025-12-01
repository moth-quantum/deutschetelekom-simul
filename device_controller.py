"""
Device Controller Script
Receives 3 values from TouchDesigner → Controls polarization device → Returns 4 coincidence peaks
Toggle between SIMULATION mode (four.py logic) and REAL HARDWARE mode
"""

import json
import sys
import time
import os

# ============================================
# MODE CONFIGURATION
# Now controlled via web interface at your Heroku URL
# Or manually edit config.json: { "useRealHardware": true/false }
# ============================================

def read_mode_from_config():
    """Read mode from config.json file"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('useRealHardware', False)
    except Exception as e:
        print(f"Warning: Could not read config.json, defaulting to SIMULATION mode. Error: {e}", file=sys.stderr, flush=True)
        return False

USE_REAL_HARDWARE = read_mode_from_config()

if USE_REAL_HARDWARE:
    # Real hardware imports (only load on Windows with hardware)
    import clr
    from System import Decimal
    import numpy as np
    
    # ThorLabs Kinesis DLLs
    KINESIS_PATH = r"C:\Program Files\Thorlabs\Kinesis"
    clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
    clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.GenericMotorCLI.dll"))
    clr.AddReference(os.path.join(KINESIS_PATH, "ThorLabs.MotionControl.PolarizerCLI.dll"))
    
    from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
    from Thorlabs.MotionControl.PolarizerCLI import Polarizer, PolarizerPaddles
    
    # TimeTagger
    import TimeTagger
else:
    # Simulation mode - just use random
    import random


def simulate_device_interaction(input_values):
    """
    Simulation mode: Uses improved quantum entanglement simulation
    Takes 3 input values (angles), returns 4 output values
    """
    import math
    
    # Use the input angles to generate quantum-inspired entanglement simulation
    angles = input_values[:3] if len(input_values) >= 3 else [0, 0, 0]
    
    # Convert to radians for calculations
    theta1 = math.radians(angles[0])
    theta2 = math.radians(angles[1])
    theta3 = math.radians(angles[2])
    
    # Calculate angle differences (important for entanglement correlation)
    delta_12 = abs(theta1 - theta2)
    
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
    
    return [val1, val2, val3, val4]


def control_real_hardware(input_values):
    """
    Real hardware mode: Controls ThorLabs polarizers and reads TimeTagger
    
    Input: 3 values from TouchDesigner (e.g., [angle1, angle2, angle3])
           - Could be angles for paddles or other control parameters
    Output: 4 coincidence peak values from channel pairs (5,7), (6,8), (5,8), (6,7)
    """
    
    # Device configuration
    DEVICE_ID = "38308514"  # Your ThorLabs device ID
    DEFAULT_TIMEOUT_MS = 30000
    VELOCITY = 50  # percentage
    
    try:
        # ===== STEP 1: Connect to polarization controller =====
        DeviceManagerCLI.BuildDeviceList()
        device_tel = Polarizer.CreatePolarizer(DEVICE_ID)
        device_tel.Connect(DEVICE_ID)
        device_tel.WaitForSettingsInitialized(DEFAULT_TIMEOUT_MS)
        device_tel.StartPolling(DEFAULT_TIMEOUT_MS)
        time.sleep(0.5)
        
        # Set velocity
        vel_params = device_tel.GetPolParams()
        vel_params.Velocity = VELOCITY
        device_tel.SetPolParams(vel_params)
        
        # ===== STEP 2: Move polarizers based on input values =====
        # Assuming input_values = [angle1, angle2, ...] for the two paddles
        # You can modify this logic based on how TouchDesigner sends the values
        
        # Map 3 input values to 2 paddle angles (example mapping)
        # You might use input_values[0] and input_values[1] for paddle angles
        # and input_values[2] for something else (velocity, runtime, etc.)
        
        angle1 = min(max(input_values[0], 0), 170)  # Clamp to 0-170 degrees
        angle2 = min(max(input_values[1], 0), 170)
        
        paddles = [PolarizerPaddles.Paddle1, PolarizerPaddles.Paddle2]
        positions = [Decimal(angle1), Decimal(angle2)]
        
        # Move paddles
        for i in range(2):
            device_tel.MoveTo(positions[i], paddles[i], DEFAULT_TIMEOUT_MS)
        
        print(f"Moved paddles to: [{angle1}, {angle2}]", file=sys.stderr, flush=True)
        
        # ===== STEP 3: Read coincidence data from TimeTagger =====
        runtime = 1  # seconds - could be influenced by input_values[2] if needed
        channel_pairs = [(5, 7), (6, 8), (5, 8), (6, 7)]
        
        results = get_coincidences(channel_pairs, runtime=runtime)
        
        # Extract peak values from each channel pair
        peaks = [max(results[pair][0]) for pair in channel_pairs]
        
        # ===== STEP 4: Cleanup =====
        # Return paddles to home position
        for i in range(2):
            device_tel.MoveTo(Decimal(0), paddles[i], DEFAULT_TIMEOUT_MS)
        
        device_tel.StopPolling()
        device_tel.Disconnect()
        
        # Convert numpy int32 to regular Python int for JSON serialization
        peaks = [int(p) for p in peaks]
        
        return peaks
        
    except Exception as e:
        print(f"Hardware Error: {e}", file=sys.stderr, flush=True)
        # Return zeros if hardware fails
        return [0, 0, 0, 0]


def get_coincidences(channel_pairs, runtime=1, binwidth=100, n_bins=10000):
    """
    Measure coincidences from TimeTagger
    Returns: dict {(ch1,ch2): (hist_data, hist_bins)}
    """
    tagger = TimeTagger.createTimeTagger()
    
    # Set trigger levels
    all_channels = set(ch for pair in channel_pairs for ch in pair)
    for ch in all_channels:
        tagger.setTriggerLevel(ch, 0.5)
    
    # Create histogram modules
    hists = {}
    for ch1, ch2 in channel_pairs:
        hists[(ch1, ch2)] = TimeTagger.Correlation(
            tagger, channel_1=ch1, channel_2=ch2,
            binwidth=binwidth, n_bins=n_bins
        )
    
    # Wait for measurement
    time.sleep(runtime)
    
    # Collect results
    results = {}
    for pair, hist in hists.items():
        hist_data = hist.getData()
        hist_bins = hist.getIndex()
        results[pair] = (hist_data, hist_bins)
    
    TimeTagger.freeTimeTagger(tagger)
    
    return results


def process_input(input_values):
    """
    Main processing function
    Input: 3 values from TouchDesigner
    Output: 4 values (coincidence peaks or simulation)
    """
    
    if USE_REAL_HARDWARE:
        print(f"REAL HARDWARE MODE: Processing {input_values}", file=sys.stderr, flush=True)
        output_values = control_real_hardware(input_values)
    else:
        print(f"SIMULATION MODE: Processing {input_values}", file=sys.stderr, flush=True)
        output_values = simulate_device_interaction(input_values)
    
    return output_values


if __name__ == "__main__":
    """
    Can be called in two ways:
    1. As a standalone script (for testing): python device_controller.py
    2. From experiment.py via subprocess (receives single JSON input via stdin)
    """
    
    # For testing: Use default values if no input
    if sys.stdin.isatty():
        # Running interactively - use test values
        test_input = [45, 90, 1]  # Example: two angles and a runtime
        result = process_input(test_input)
        print(json.dumps({"entanglement": result}), flush=True)
    else:
        # Running from subprocess - read single input from stdin
        try:
            input_line = sys.stdin.read().strip()
            
            if input_line:
                data = json.loads(input_line)
                input_values = data.get('knob_values', [0, 0, 0])
                
                if len(input_values) >= 3:
                    output_values = process_input(input_values[:3])
                    
                    # Output in the same format as four.py
                    output_data = {"entanglement": output_values}
                    print(json.dumps(output_data), flush=True)
                else:
                    print(f"Error: Expected 3 input values, got {len(input_values)}", file=sys.stderr, flush=True)
                    
        except Exception as e:
            print(f"Error processing input: {e}", file=sys.stderr, flush=True)
