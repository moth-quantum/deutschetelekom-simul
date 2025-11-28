"""
Socket.IO Server for sending numerical data to TouchDesigner's SocketIO DAT
Run this on the computer you're RDP'ing into
"""
import socketio
import eventlet
import eventlet.wsgi
import socket

# Configuration
PORT = 443
HOST = "0.0.0.0"  # Accept connections from any IP (required for remote access)

# Create Socket.IO server
sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
app = socketio.WSGIApp(sio)

def get_local_ips():
    """Show available IPs for the remote TouchDesigner to connect to"""
    hostname = socket.gethostname()
    try:
        ips = socket.getaddrinfo(hostname, None, socket.AF_INET)
        unique_ips = set(ip[4][0] for ip in ips)
        return list(unique_ips)
    except:
        return [socket.gethostbyname(hostname)]

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send test data immediately on connect
    send_test_data(sid)

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
def request_data(sid, data):
    """Handle request_data event from TouchDesigner"""
    print(f"Received request_data from {sid}: {data}")
    send_test_data(sid)

def send_test_data(sid):
    """Send numerical test data to TouchDesigner"""
    # Match the format your TD code expects: eventName with 'entanglement' key
    test_values = [0.1, 0.2, 0.3]
    
    sio.emit('numerical_data', {
        'entanglement': test_values
    }, room=sid)
    
    print(f"Sent numerical_data to {sid}: {test_values}")

def background_sender():
    """Continuously send data every 2 seconds"""
    counter = 0.0
    while True:
        sio.sleep(2)
        # Generate changing values
        values = [round(counter + i * 0.1, 2) for i in range(10)]
        counter = (counter + 0.1) % 10
        
        # Emit to all connected clients
        sio.emit('numerical_data', {
            'entanglement': values
        })
        print(f"Broadcast: {values}")

if __name__ == "__main__":
    print("=" * 50)
    print(f"Socket.IO Server starting on port {PORT}")
    print("TouchDesigner SocketIO DAT connection URLs:")
    for ip in get_local_ips():
        print(f"  -> http://{ip}:{PORT}")
    print("=" * 50)
    
    # Start background sender
    sio.start_background_task(background_sender)
    
    # Run server
    eventlet.wsgi.server(eventlet.listen((HOST, PORT)), app)
