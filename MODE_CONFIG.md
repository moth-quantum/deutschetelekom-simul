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
    ↓ Click button → POST /api/mode
    ↓ Listens: 'mode_changed' event
    ↓
Node.js (main.js)
    ↓ Updates: currentMode = {...}
    ↓ Kills Python process
    ↓ Restarts with new USE_REAL_HARDWARE env var
    ↓ Broadcasts: io.emit('mode_changed', mode)
    ↓
Python (experiment.py / device_controller.py)
    ↓ Reads: os.environ.get('USE_REAL_HARDWARE')
    ↓ Routes: hardware vs simulation
```

## How Mode Changes Work

1. **Click button** on web UI
2. **Node.js updates** `currentMode` in memory
3. **Node.js kills** current Python process
4. **Node.js restarts** Python with new `USE_REAL_HARDWARE` env var
5. **Socket.IO broadcasts** to update all web clients
6. **Python reads** mode from environment variable

The Python process restart ensures the new mode takes effect immediately! 🎯
