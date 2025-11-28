// Run this on your LAPTOP
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: { origin: "*", methods: ["GET", "POST"] }
});

const PORT = 443;

// Store latest data from RDP machine
let latestData = { entanglement: [0, 0, 0] };

app.get('/', (req, res) => {
  res.send('Relay server running - TD connects here');
});

io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // When RDP machine sends data, broadcast to all (including TD)
  socket.on('push_data', (data) => {
    console.log('Received from RDP:', data);
    latestData = data;
    io.emit('numerical_data', data);  // Forward to TouchDesigner
  });

  // Send latest data on connect
  socket.emit('numerical_data', latestData);

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

httpServer.listen(PORT, '0.0.0.0', () => {
  console.log(`Relay server on http://localhost:${PORT}`);
  console.log('TouchDesigner: http://localhost:8080');
  console.log('Waiting for RDP machine to push data...');
});
