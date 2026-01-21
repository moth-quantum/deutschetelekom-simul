"""
Device Controller Script
Receives 3 values from TouchDesigner → Controls polarization device → Returns 4 coincidence peaks
Toggle between SIMULATION mode (four.py logic) and REAL HARDWARE mode
"""

import json
import sys
import time
import os
import math
import random

# ============================================
# MODE CONFIGURATION
# Mode is passed via USE_REAL_HARDWARE environment variable from Node.js
# Toggle mode via web interface - Python process restarts with new mode
# ============================================

def read_mode_from_env():
    """Read mode from environment variable set by Node.js"""
    use_hardware = os.environ.get('USE_REAL_HARDWARE', 'false').lower() == 'true'
    mode_name = 'HARDWARE' if use_hardware else 'SIMULATION'
    print(f"Device controller mode: {mode_name}", file=sys.stderr, flush=True)
    return use_hardware

USE_REAL_HARDWARE = read_mode_from_env()

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

    print("Hardware is connected.", file=sys.stderr, flush=True)
else:
    print("Hardware is not connected. Debug on RDP.", file=sys.stderr, flush=True)

def control_real_hardware(input_values):
    """
    Real hardware mode: Controls ThorLabs polarizers and reads TimeTagger
    
    Input: 3 values from TouchDesigner (e.g., [angle1, angle2, angle3])
           - Could be angles for paddles or other control parameters
    Output: 4 coincidence peak values from channel pairs (5,7), (6,8), (5,8), (6,7)
    """
    
    # Device configuration
    DEVICE_ID = "38469684"  # Your ThorLabs device ID
    DEFAULT_TIMEOUT_MS = 2000
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
        # The values between 0 and 160 will arrive, mapped from the midi values (0-127) from TD.
        
        # input_values = [number_1, number_2, number_3](expectation)
        
        angle1 = input_values[0]
        angle2 = input_values[1]
        angle3 = input_values[2]
        
        paddles = [PolarizerPaddles.Paddle1, PolarizerPaddles.Paddle2, PolarizerPaddles.Paddle3]
        positions = [Decimal(angle1), Decimal(angle2), Decimal(angle3)]
        
        # Move paddles
        for i in range(3):
            device_tel.MoveTo(positions[i], paddles[i], DEFAULT_TIMEOUT_MS)
        
        print(f"Moved paddles to: [{angle1}, {angle2}, {angle3}]", file=sys.stderr, flush=True)
        
        # ===== STEP 3: Read coincidence data from TimeTagger =====
        runtime = 3  # sec
        channel_pairs = [(5, 6), (8, 7), (5, 7), (8, 6)]
        
        try:
            # Get coincidence counts for all channel pairs
            results = get_coincidences(channel_pairs, runtime=runtime)
            
            # Extract peak values from each channel pair
            peaks = [results[pair][0] for pair in channel_pairs]
            print(f"Coincidence counts: {peaks}", file=sys.stderr, flush=True)
            
        except Exception as e:
            print(f"Error in coincidence counting: {e}", file=sys.stderr, flush=True)
            peaks = [0, 0, 0, 0]
        
        # ===== STEP 4: Cleanup =====
        # Return paddles to home position
        for i in range(3):
            device_tel.MoveTo(Decimal(0), paddles[i], DEFAULT_TIMEOUT_MS)
        
        device_tel.StopPolling()
        device_tel.Disconnect() # Always disconnect after usage to block any mischief
        
        # Convert numpy int32 to regular Python int for JSON serialization
        peaks = [int(p) for p in peaks] # Four values to be sent to server
        
        return peaks
        
    except Exception as e:
        import traceback
        print(f"Hardware Error: {e}", file=sys.stderr, flush=True)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr, flush=True)
        # Return zeros if hardware fails
        return [0, 0, 0, 0]


def get_coincidences(channel_pairs, runtime=3, binwidth_ps=10):
    """
    Measure coincidences from TimeTagger using the same method as Coincidence_counts.py
    
    Args:
        channel_pairs: List of tuples (ch1, ch2) for coincidence counting
        runtime: Measurement time in seconds
        binwidth_ps: Width of time bins in picoseconds (default: 10ps)
        
    Returns:
        dict: {(ch1, ch2): (max_counts, None)} for each channel pair
    """
    measurement_time_ps = int(runtime * 1e12)  # Convert seconds to picoseconds
    results = {}
    
    for ch1, ch2 in channel_pairs:
        try:
            # Create new TimeTagger instance for each measurement to match Coincidence_counts.py
            tagger = TimeTagger.createTimeTagger()
            tagger.setTriggerLevel(ch1, 0.5)
            tagger.setTriggerLevel(ch2, 0.5)
            
            # Create correlation with same parameters as Coincidence_counts.py
            corr = TimeTagger.Correlation(tagger, ch1, ch2, binwidth_ps, n_bins=10000)
            
            # Use startFor and waitUntilFinished instead of time.sleep()
            corr.startFor(measurement_time_ps, clear=True)
            corr.waitUntilFinished()
            time.sleep(0.5)  # Small delay to ensure data is ready
            
            # Get max counts from histogram
            hist = corr.getData()
            max_counts = int(np.max(hist))
            
            # Store result
            results[(ch1, ch2)] = (max_counts, None)
            
            # Clean up
            del corr
            TimeTagger.freeTimeTagger(tagger)
            
        except Exception as e:
            print(f"Error measuring coincidence for channels {ch1}-{ch2}: {e}", file=sys.stderr, flush=True)
            results[(ch1, ch2)] = (0, None)
            try:
                TimeTagger.freeTimeTagger(tagger)
            except Exception as e:
                print(f"Failed to free TimeTagger: {e}", file=sys.stderr, flush=True)
    
    return results


def simulate_device_interaction(input_values):
    """
    Simulation mode: Generate fake coincidence peaks.
    
    Input: 3 paddle angles from TouchDesigner (0-170 degrees)
    Output: 4 coincidence peak counts for channel pairs (5, 6), (8, 7), (5, 7), (8, 6)
    """
    angle1, angle2, angle3 = input_values[:3]
    
    target_angles = [61, 80, 101]
    # On the TouchDesigner side, the MIDI knob controller will show 48, 63, 80.

    if int(angle1) == target_angles[0] and int(angle2) == target_angles[1] and int(angle3) == target_angles[2]:
        # Randomly choose which pair to enhance
        who = int(random.uniform(1, 3))
        if who == 1:
            peak_56 = 788
            peak_87 = 700
            peak_57 = 35
            peak_86 = 20
        else:
            peak_56 = 35
            peak_87 = 20
            peak_57 = 788
            peak_86 = 700
    else:
        peak_56 = int(random.uniform(0, int(random.uniform(500, 100000))))
        peak_87 = int(random.uniform(0, int(random.uniform(500, 100000))))
        peak_57 = int(random.uniform(0, int(random.uniform(500, 100000))))
        peak_86 = int(random.uniform(0, int(random.uniform(500, 100000))))
    
    time.sleep(11.0) # To simulate the hardware delay as well
    return [peak_56, peak_87, peak_57, peak_86] # Return peaks in order: (5,6), (8,7), (5,7), (8,6)


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
        test_input = [45, 90, 135]
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
