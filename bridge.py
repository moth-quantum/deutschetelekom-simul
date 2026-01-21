"""
Local Bridge Service for Windows Machine (172.20.118.125)
Run this ON THE WINDOWS MACHINE via RoyalTSX
Exposes hardware control via HTTP API

OPTIMIZED: Persistent hardware connection - no subprocess overhead
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os
import traceback

app = Flask(__name__)
CORS(app)  # Allow requests from Heroku

# Configuration
PORT = 5000

# Import hardware control directly (no subprocess)
os.environ['USE_REAL_HARDWARE'] = 'true'
try:
    from device_controller import control_real_hardware
    HARDWARE_AVAILABLE = True
    print("[BRIDGE] Hardware control module loaded successfully", flush=True)
except ImportError as e:
    HARDWARE_AVAILABLE = False
    print(f"[BRIDGE] WARNING: Could not load hardware module: {e}", flush=True)
    print("[BRIDGE] Running in degraded mode - hardware calls will fail", flush=True)

@app.route('/', methods=['GET'])
def health_check():
    """Health check - confirms bridge is running"""
    return jsonify({
        'status': 'online',
        'service': 'Local Hardware Bridge',
        'location': 'Windows Machine (172.20.118.125)',
        'message': 'Ready to control hardware'
    })

@app.route('/api/hardware/execute', methods=['POST'])
def execute_hardware():
    """
    OPTIMIZED: Direct function call instead of subprocess
    
    Receives commands from Heroku → Calls control_real_hardware() → Returns results
    
    POST body: { "knob_values": [val1, val2, val3] }
    Returns: { "success": true, "data": { "entanglement": [...] } }
    """
    try:
        # Check if hardware is available
        if not HARDWARE_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Hardware module not loaded - check bridge startup logs'
            }), 503
        
        data = request.get_json()
        
        if not data or 'knob_values' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing knob_values in request'
            }), 400
        
        knob_values = data['knob_values']
        print(f"[BRIDGE] Received from Heroku: {knob_values}", flush=True)
        
        # Call hardware control function directly (no subprocess overhead)
        peaks = control_real_hardware(knob_values)
        
        # Format output to match expected structure
        output_data = {
            'entanglement': peaks
        }
        
        print(f"[BRIDGE] Success! Returning to Heroku: {output_data}", flush=True)
        
        return jsonify({
            'success': True,
            'data': output_data
        })
    
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[BRIDGE] Error: {error_msg}", flush=True)
        print(f"[BRIDGE] Traceback:\n{traceback.format_exc()}", flush=True)
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Check if hardware is ready - actually tests ThorLabs connection"""
    result = {
        'bridge_online': True,
        'location': '172.20.118.125',
        'hardware_connected': False,
        'device_id': None,
        'error': None
    }
    
    try:
        # Actually try to detect ThorLabs hardware
        import clr
        KINESIS_PATH = r"C:\Program Files\Thorlabs\Kinesis"
        clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
        from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
        
        # Build device list and check for polarizer
        DeviceManagerCLI.BuildDeviceList()
        device_list = DeviceManagerCLI.GetDeviceList()
        
        DEVICE_ID = "38469684"  # Your ThorLabs device ID
        
        if device_list.Contains(DEVICE_ID):
            result['hardware_connected'] = True
            result['device_id'] = DEVICE_ID
        else:
            result['error'] = f'Device {DEVICE_ID} not found in device list'
            result['available_devices'] = list(device_list)
            
    except ImportError as e:
        result['error'] = f'ThorLabs SDK not installed: {str(e)}'
    except Exception as e:
        result['error'] = f'Hardware check failed: {str(e)}'
    
    return jsonify(result)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔌 LOCAL HARDWARE BRIDGE - STARTING ON WINDOWS MACHINE")
    print("="*70)
    print(f"Local IP: 172.20.118.125")
    print(f"Bridge Port: {PORT}")
    print(f"Bridge URL: http://172.20.118.125:{PORT}")
    print("")
    print("📋 SETUP STEPS:")
    print("")
    print("1. Install ngrok on this Windows machine:")
    print("   Download from: https://ngrok.com/download")
    print("")
    print("2. In another terminal/command prompt, run:")
    print(f"   ngrok http {PORT}")
    print("")
    print("3. Copy the ngrok 'Forwarding' URL (e.g., https://abc123.ngrok.io)")
    print("")
    print("4. Set it on Heroku:")
    print("   heroku config:set BRIDGE_URL=https://abc123.ngrok.io")
    print("")
    print("5. Toggle hardware mode ON via the web interface")
    print("")
    print("="*70)
    print("Waiting for requests from Heroku...")
    print("="*70 + "\n")
    
    # Run Flask server
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=PORT,
        debug=False
    )
