"""
Test client to verify Socket.IO server before connecting TouchDesigner
Run this on any machine that can reach the server
pip install python-socketio[client] websocket-client
"""
import socketio

# Configuration - change this to test from different machines
SERVER_IP = "85.255.233.64"
SERVER_PORT = 443
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

sio = socketio.Client()

@sio.event
def connect():
    print("CONNECTED!")

@sio.event
def disconnect():
    print("DISCONNECTED")

@sio.on('numerical_data')
def on_numerical_data(data):
    print(f"Received numerical_data: {data}")
    if 'entanglement' in data:
        print(f"  Entanglement values: {data['entanglement']}")

@sio.on('*')
def catch_all(event, data):
    print(f"Event: {event}, Data: {data}")

def test_connection():
    try:
        print(f"Connecting to {SERVER_URL}...")
        sio.connect(SERVER_URL)
        sio.wait()  # Keep listening
    except Exception as e:
        print(f"ERROR: {e}")
        print("Check: firewall, server running, correct IP/port")

if __name__ == "__main__":
    test_connection()
