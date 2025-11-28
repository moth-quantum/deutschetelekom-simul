const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const PORT = process.env.PORT || 443;  // Try 8080, often less restricted

// Health check
app.get('/', (req, res) => {
  res.send('Socket.IO server running for TouchDesigner');
});

// Broadcast test data every 2 seconds
let counter = 0;
setInterval(() => {
  const values = [];
  for (let i = 0; i < 3; i++) {
    values.push(parseFloat((counter + i * 0.1).toFixed(2)));
  }
  counter = (counter + 0.1) % 10;

  io.emit('numerical_data', { entanglement: values });
  console.log('Broadcast:', values);
}, 2000);

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Send initial data on connect
  socket.emit('numerical_data', { entanglement: [0.1, 0.2, 0.3] });

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });

  socket.on('request_data', () => {
    console.log('Data requested by:', socket.id);
    socket.emit('numerical_data', { entanglement: [0.1, 0.2, 0.3] });
  });
});

httpServer.listen(PORT, '0.0.0.0', () => {
  console.log('='.repeat(50));
  console.log(`Socket.IO server running on port ${PORT}`);
  console.log(`TouchDesigner: 172.20.118.125:${PORT}`);
  console.log('='.repeat(50));
});
