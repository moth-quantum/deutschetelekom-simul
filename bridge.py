"""
Local Bridge Service for Windows Machine
Run this ON THE WINDOWS MACHINE via RoyalTSX.
Exposes hardware control via HTTP API.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('bridge')

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('BRIDGE_PORT', '5000'))
DEVICE_ID = os.environ.get('DEVICE_ID', '38469684')
KINESIS_PATH = os.environ.get('KINESIS_PATH', r'C:\Program Files\Thorlabs\Kinesis')
LOCAL_IP = os.environ.get('LOCAL_IP', '172.20.118.125')

os.environ['USE_REAL_HARDWARE'] = 'true'
try:
    from device_controller import control_real_hardware
    HARDWARE_AVAILABLE = True
    logger.info("Hardware control module loaded successfully")
except ImportError as e:
    HARDWARE_AVAILABLE = False
    logger.warning("Could not load hardware module: %s", e)
    logger.warning("Running in degraded mode - hardware calls will fail")


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'online',
        'service': 'Local Hardware Bridge',
        'location': f'Windows Machine ({LOCAL_IP})',
        'message': 'Ready to control hardware'
    })


@app.route('/api/hardware/execute', methods=['POST'])
def execute_hardware():
    """
    Receives commands from Heroku, calls control_real_hardware(), returns results.

    POST body: { "knob_values": [val1, val2, val3] }
    Returns: { "success": true, "data": { "entanglement": [...] } }
    """
    try:
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
        logger.info("Received from Heroku: %s", knob_values)

        import time as _time
        t_bridge = _time.time()
        peaks = control_real_hardware(knob_values)
        output_data = {'entanglement': peaks}

        logger.info("[TIMING] Bridge total (receive → respond): %.3fs", _time.time() - t_bridge)
        logger.info("Returning to Heroku: %s", output_data)

        return jsonify({
            'success': True,
            'data': output_data
        })

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.exception("Hardware execution error")

        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Check if hardware is ready by testing ThorLabs connection."""
    result = {
        'bridge_online': True,
        'location': LOCAL_IP,
        'hardware_connected': False,
        'device_id': None,
        'error': None
    }

    try:
        import clr
        clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
        from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI

        DeviceManagerCLI.BuildDeviceList()
        device_list = DeviceManagerCLI.GetDeviceList()

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
    logger.info("=" * 50)
    logger.info("LOCAL HARDWARE BRIDGE")
    logger.info("Local IP: %s | Port: %d", LOCAL_IP, PORT)
    logger.info("Setup: ngrok http %d -> set BRIDGE_URL on Heroku -> toggle hardware mode", PORT)
    logger.info("=" * 50)

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )
