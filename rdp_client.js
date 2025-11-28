// Run this on the RDP machine - pushes data OUT to your laptop
const { io } = require('socket.io-client');

// YOUR LAPTOP'S VPN IP - change this!
const LAPTOP_IP = '85.255.233.64';
const PORT = 8080;

const socket = io(`http://${LAPTOP_IP}:${PORT}`);

socket.on('connect', () => {
  console.log('Connected to laptop server!');
  
  // Start pushing data
  let counter = 0;
  setInterval(() => {
    const values = [];
    for (let i = 0; i < 3; i++) {
      values.push(parseFloat((counter + i * 0.1).toFixed(2)));
    }
    counter = (counter + 0.1) % 10;

    socket.emit('push_data', { entanglement: values });
    console.log('Pushed:', values);
  }, 2000);
});

socket.on('connect_error', (err) => {
  console.log('Connection failed:', err.message);
});

socket.on('disconnect', () => {
  console.log('Disconnected from laptop');
});
