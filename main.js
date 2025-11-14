const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
const readline = require('readline'); // <-- ADDED

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*", // Allow TouchDesigner to connect
    methods: ["GET", "POST"]
  }
});

const PORT = process.env.PORT || 3000;

// Basic health check endpoint
app.get('/', (req, res) => {
  res.send('Socket.IO server running for TouchDesigner');
});

// Store active Python process
let pythonProcess = null;

// Function to start Python script and stream data
// REMOVED 'socket' parameter
function startPythonStream() {
  if (pythonProcess) {
    console.log('Python process already running');
    return;
  }

  console.log('Starting Python script...');
  const args = ['experiment.py'];
  // CHANGED to 'python' for Heroku
  pythonProcess = spawn('python', args);

  // --- FIXED: Use readline to handle stream buffering ---
  const rl = readline.createInterface({ input: pythonProcess.stdout });

  rl.on('line', (line) => {
    try {
      const parsed = JSON.parse(line);
      console.log('Emitting data:', parsed);
      // Emit to all connected clients (TouchDesigner)
      io.emit('numerical_data', parsed);
    } catch (e) {
      console.warn('Python script produced non-JSON line:', line);
    }
  });
  // --- End of readline fix ---

  pythonProcess.stderr.on('data', (data) => {
    // FIXED: Convert buffer to string
    const errorMsg = data.toString();
    console.error(`Python stderr: ${errorMsg}`);
    io.emit('error', { message: errorMsg });
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Python script exited with code ${code}`);
    pythonProcess = null;
    
    // FIXED: Only restart if clients are still connected
    if (io.engine.clientsCount > 0) {
      console.log('Clients still connected, restarting script in 2s...');
      setTimeout(startPythonStream, 2000); // No 'socket' passed
    }
  });
}

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('TouchDesigner client connected:', socket.id);
  
  // Start Python data stream if it's not already running
  if (!pythonProcess) {
    startPythonStream(); // No 'socket' passed
  }

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    
    // Stop Python process when no clients are connected
    if (io.engine.clientsCount === 0 && pythonProcess) {
      console.log('Last client disconnected, stopping Python process.');
      pythonProcess.kill();
      pythonProcess = null;
    }
  });

  // Sending data from a MIDI knob controller values to the server
  socket.on('knobs', (data) => {
    // 'data' is passed as-is to experiment.py (ensure TouchDesigner sends { "knobs": [...] })
    
    if (pythonProcess && pythonProcess.stdin) {
      try {
        // Convert the JSON object back to a string
        const dataString = JSON.stringify(data);
        
        // Write it to the Python script's standard input
        // The '\n' is CRITICAL - it tells Python it's a new line
        pythonProcess.stdin.write(dataString + '\n');
        
        // Optional: log it
        console.log('Sent to Python:', dataString);
        
      } catch (e) {
        console.error('Failed to send data to Python:', e);
      }
    }
  });

  // Allow TouchDesigner to request data
  socket.on('request_data', () => {
    console.log('Data requested by client');
    if (!pythonProcess) {
      startPythonStream(); // No 'socket' passed
    }
  });
});

httpServer.listen(PORT, () => {
  console.log(`Socket.IO server running on port ${PORT}`);
  // Simplified this log, as the Heroku URL is just the app's URL
  console.log(`Connect TouchDesigner to your Heroku app's https://... URL`);
});