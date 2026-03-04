require('dotenv').config(); // for local testing only

const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
const readline = require('readline');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const PORT = process.env.PORT || 3000;

app.use(express.static('public'));
app.use(express.json());

let currentMode = { useRealHardware: false };

app.get('/api/mode', (req, res) => {
  res.json(currentMode);
});

app.get('/api/hardware-status', async (req, res) => {
  const bridgeUrl = process.env.BRIDGE_URL;

  if (!bridgeUrl) {
    return res.json({
      bridge_online: false,
      hardware_connected: false,
      error: 'BRIDGE_URL not configured on Heroku'
    });
  }

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${bridgeUrl}/api/status`, {
      signal: controller.signal
    });
    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Bridge returned ${response.status}`);
    }

    const data = await response.json();
    res.json(data);

  } catch (error) {
    res.json({
      bridge_online: false,
      hardware_connected: false,
      error: error.name === 'AbortError'
        ? 'Bridge timeout - is ngrok running?'
        : `Bridge unreachable: ${error.message}`
    });
  }
});

app.post('/api/mode', (req, res) => {
  const { useRealHardware } = req.body;

  if (typeof useRealHardware !== 'boolean') {
    return res.status(400).json({ success: false, error: 'useRealHardware must be a boolean' });
  }

  currentMode = { useRealHardware };
  console.log(`Mode changed to: ${useRealHardware ? 'HARDWARE' : 'SIMULATION'}`);

  if (pythonProcess && io.engine.clientsCount > 0) {
    console.log('Restarting Python process with new mode...');
    const proc = pythonProcess;
    pythonProcess = null;
    if (restartTimeout) {
      clearTimeout(restartTimeout);
      restartTimeout = null;
    }
    proc.kill();
  }

  io.emit('mode_changed', currentMode);
  res.json({ success: true, useRealHardware });
});

let pythonProcess = null;
let restartTimeout = null;

function startPythonStream() {
  if (pythonProcess) {
    console.log('Python process already running');
    return;
  }

  console.log('Starting Python script...');

  const pythonEnv = {
    ...process.env,
    USE_REAL_HARDWARE: currentMode.useRealHardware.toString()
  };

  pythonProcess = spawn('python', ['device_controller.py'], { env: pythonEnv });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process:', err);
    pythonProcess = null;
  });

  const rl = readline.createInterface({ input: pythonProcess.stdout });

  rl.on('line', (line) => {
    try {
      const parsed = JSON.parse(line);
      console.log('Emitting data:', parsed);
      io.emit('numerical_data', parsed);
    } catch (e) {
      console.warn('Non-JSON output from Python:', line);
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    const errorMsg = data.toString();
    console.error(`Python stderr: ${errorMsg}`);
    io.emit('error', { message: errorMsg });
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Python script exited with code ${code}`);
    const wasIntentional = (pythonProcess === null);
    pythonProcess = null;

    if (!wasIntentional && io.engine.clientsCount > 0) {
      console.log('Unexpected exit, restarting in 2s...');
      if (restartTimeout) clearTimeout(restartTimeout);
      restartTimeout = setTimeout(() => {
        restartTimeout = null;
        startPythonStream();
      }, 2000);
    }
  });
}

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  if (!pythonProcess) {
    startPythonStream();
  }

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);

    if (io.engine.clientsCount === 0 && pythonProcess) {
      console.log('Last client disconnected, stopping Python process.');
      const proc = pythonProcess;
      pythonProcess = null;
      if (restartTimeout) {
        clearTimeout(restartTimeout);
        restartTimeout = null;
      }
      proc.kill();
    }
  });

  // TouchDesigner sends { "knob_values": [v1, v2, v3] }
  socket.on('knobs', (data) => {
    if (pythonProcess && pythonProcess.stdin) {
      try {
        // Newline delimiter is required for Python's stdin line reader
        pythonProcess.stdin.write(JSON.stringify(data) + '\n');
        console.log('Sent to Python:', JSON.stringify(data));
      } catch (e) {
        console.error('Failed to send data to Python:', e);
      }
    }
  });

  socket.on('request_data', () => {
    console.log('Data requested by client');
    if (!pythonProcess) {
      startPythonStream();
    }
  });
});

httpServer.listen(PORT, () => {
  console.log(`Socket.IO server running on port ${PORT}`);
});
