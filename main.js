const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');

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
function startPythonStream(socket) {
  if (pythonProcess) {
    console.log('Python process already running');
    return;
  }

  const args = ['four.py'];
  pythonProcess = spawn('python3', args);
  
  pythonProcess.stdout.setEncoding('utf8');
  pythonProcess.stdout.on('data', (data) => {
    try {
      // Try to parse as JSON (if Python sends JSON)
      const parsed = JSON.parse(data.trim());
      console.log('Emitting data:', parsed);
      // Emit to all connected clients (TouchDesigner)
      io.emit('numerical_data', parsed);
    } catch (e) {
      // If not JSON, send as raw data
      console.log('Raw data:', data);
      io.emit('numerical_data', { raw: data.trim() });
    }
  });

  pythonProcess.stderr.setEncoding('utf8');
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python error: ${data}`);
    io.emit('error', { message: data });
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Python script exited with code ${code}`);
    pythonProcess = null;
    // Restart after a delay
    setTimeout(() => startPythonStream(socket), 2000);
  });
}

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('TouchDesigner client connected:', socket.id);
  
  // Start Python data stream when first client connects
  if (io.engine.clientsCount === 1) {
    startPythonStream(socket);
  }

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
    
    // Stop Python process when no clients connected
    if (io.engine.clientsCount === 0 && pythonProcess) {
      pythonProcess.kill();
      pythonProcess = null;
    }
  });

  // Allow TouchDesigner to request data
  socket.on('request_data', () => {
    console.log('Data requested by client');
    if (!pythonProcess) {
      startPythonStream(socket);
    }
  });
});

httpServer.listen(PORT, () => {
  console.log(`Socket.IO server running on port ${PORT}`);
  console.log(`Connect TouchDesigner to: ${process.env.HEROKU_APP_NAME ? 'https://' + process.env.HEROKU_APP_NAME + '.herokuapp.com' : 'http://localhost:' + PORT}`);
});