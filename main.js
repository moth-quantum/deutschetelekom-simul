const { spawn } = require('child_process');

let args = ['four.py'];
args.push('--hello', 'Hello World');

const childProcess = spawn('python', args); // or 'python3'
// Spawn the subprocess that runs the Python script.

childProcess.stdout.setEncoding('utf8');
childProcess.stdout.on('data', (data) => {
  console.log(`Node output: ${data}`);
});

childProcess.stderr.setEncoding('utf8');
childProcess.stderr.on('data', (data) => {
  console.error(`error: ${data}`);
});

childProcess.on('exit', () => {
    console.log('The python script has exited');
})

  