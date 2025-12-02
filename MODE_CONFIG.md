# Mode Configuration - Simple Approach

## How It Works

**In-Memory State** - Mode is stored in Node.js memory, not in files.

### Real-Time Updates

1. **Click button** on web UI → Sends POST to `/api/mode`
2. **Node.js updates** in-memory `currentMode` variable
3. **Socket.IO broadcasts** `mode_changed` event to all connected clients
4. **Web UI updates instantly** via event listener
5. **Python queries mode** via HTTP GET to `/api/mode` when processing data

### Event Listener Flow

```javascript
// Web UI connects to Socket.IO
const socket = io();

// Listens for mode changes
socket.on('mode_changed', (data) => {
    updateUI(data.useRealHardware);
});
```

### Benefits

✅ **Simple** - No file writing, no config vars  
✅ **Real-time** - All clients update instantly  
✅ **Works on Heroku** - No filesystem issues  
✅ **Event-driven** - Uses Socket.IO's built-in pub/sub

### Trade-offs

⚠️ **Not persistent** - Mode resets to default (SIMULATION) when:
- Server restarts
- Heroku dyno cycles (every 24h)
- New deployment

This is acceptable for a live control interface where you toggle the mode at the start of each session.

## Changing the Mode

### Via Web UI

Just click the button - changes take effect immediately.

### Via Code

To change the default on startup, edit `main.js`:

```javascript
let currentMode = { useRealHardware: false }; // Change this line
```

## Architecture

```
Web UI (index.html)
    ↓ Socket.IO connection
    ↓ Listens: 'mode_changed'
    ↓
Node.js (main.js)
    ↓ In-memory: currentMode = {...}
    ↓ Broadcasts: io.emit('mode_changed', mode)
    ↓ HTTP API: GET /api/mode
    ↓
Python (experiment.py / device_controller.py)
    ↓ Queries: GET http://localhost:3000/api/mode
    ↓ Uses mode to route hardware vs simulation
```

Simple and effective! 🎯
