"""
Local Bridge Service for Windows Machine (172.20.118.125)
Run this ON THE WINDOWS MACHINE via RoyalTSX
Exposes hardware control via HTTP API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import sys
import os

app = Flask(__name__)
CORS(app)  # Allow requests from Heroku

# Configuration
PORT = 5000
DEVICE_CONTROLLER_PATH = 'device_controller.py'

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
    Receives commands from Heroku → Executes device_controller.py → Returns results
    
    POST body: { "knob_values": [val1, val2, val3] }
    Returns: { "success": true, "data": { "entanglement": [...] } }
    """
    try:
        data = request.get_json()
        
        if not data or 'knob_values' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing knob_values in request'
            }), 400
        
        knob_values = data['knob_values']
        print(f"[BRIDGE] Received from Heroku: {knob_values}", flush=True)
        
        # Prepare input for device_controller.py
        device_input = json.dumps({'knob_values': knob_values})
        
        # Execute device_controller.py
        result = subprocess.run(
            ['python', DEVICE_CONTROLLER_PATH],
            input=device_input,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for hardware operations
        )
        
        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr or 'Unknown error'
            print(f"[BRIDGE] Device controller error: {error_msg}", flush=True)
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
        # Parse output
        if not result.stdout.strip():
            return jsonify({
                'success': False,
                'error': 'Device controller produced no output'
            }), 500
        
        try:
            output_data = json.loads(result.stdout)
            print(f"[BRIDGE] Success! Returning to Heroku: {output_data}", flush=True)
            
            return jsonify({
                'success': True,
                'data': output_data
            })
            
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid JSON from device: {str(e)}'
            }), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Hardware operation timeout (>120s)'
        }), 504
    
    except Exception as e:
        print(f"[BRIDGE] Error: {str(e)}", flush=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Check if hardware is ready"""
    try:
        # Check if config.json exists
        config_exists = os.path.exists('config.json')
        
        mode = 'unknown'
        if config_exists:
            with open('config.json', 'r') as f:
                config = json.load(f)
                mode = 'hardware' if config.get('useRealHardware', False) else 'simulation'
        
        return jsonify({
            'bridge_running': True,
            'config_exists': config_exists,
            'current_mode': mode,
            'location': '172.20.118.125'
        })
    except Exception as e:
        return jsonify({
            'bridge_running': True,
            'error': str(e)
        })

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
