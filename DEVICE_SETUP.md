# Device Controller Setup Guide

## Overview

The system now supports **two modes**:
1. **SIMULATION MODE** (default) - Uses `four.py` logic for testing
2. **REAL HARDWARE MODE** - Controls ThorLabs polarizers and reads TimeTagger data

## Quick Start: Toggle Between Modes

Open `device_controller.py` and change this line:

```python
# Line 13
USE_REAL_HARDWARE = False  # Set to True for real hardware
```

### Simulation Mode (No Hardware Required)
```python
USE_REAL_HARDWARE = False
```
- Works on any computer (Mac, Windows, Linux)
- Uses random data generation (same as `four.py`)
- Perfect for testing the Heroku ↔ TouchDesigner flow

### Real Hardware Mode (Windows + ThorLabs + TimeTagger)
```python
USE_REAL_HARDWARE = True
```
- **Requirements:**
  - Windows OS
  - ThorLabs Kinesis installed at `C:\Program Files\Thorlabs\Kinesis`
  - TimeTagger SDK installed
  - Polarization controller connected (Device ID: `38308514`)
  - TimeTagger hardware connected

## Data Flow

```
TouchDesigner
  ↓ (sends 3 values via Socket.IO)
Heroku Server (main.js)
  ↓
experiment.py
  ↓ (subprocess call)
device_controller.py
  ├─ SIMULATION: Uses random data
  └─ REAL HARDWARE: Controls polarizers → Reads coincidences
  ↓ (returns 4 values)
experiment.py
  ↓
Heroku Server
  ↓ (Socket.IO)
TouchDesigner (receives 4 values)
```

## Input/Output Mapping

### Input (3 values from TouchDesigner)
- `input_values[0]` → Paddle 1 angle (0-170 degrees)
- `input_values[1]` → Paddle 2 angle (0-170 degrees)
- `input_values[2]` → Currently unused (could be runtime, velocity, etc.)

### Output (4 values to TouchDesigner)

**Simulation Mode:**
- Random values based on `four.py` logic

**Real Hardware Mode:**
- Peak coincidence counts from 4 channel pairs:
  1. Channels (5, 7)
  2. Channels (6, 8)
  3. Channels (5, 8)
  4. Channels (6, 7)

## Testing Locally

### Test Simulation Mode
```bash
cd /Users/astrydpark/Documents/GitHub/deutschetelekom-simul
python device_controller.py
```

Expected output:
```json
{"entanglement": [0.345, 0.655, 0.789, 0.234]}
```

### Test with Custom Input
```bash
echo '{"knob_values": [45, 90, 1]}' | python device_controller.py
```

## Deployment Notes

- The simulation mode can be deployed to Heroku as-is
- For real hardware mode:
  - The device controller must run **locally on Windows**
  - You'll need to modify the architecture to send data from local → Heroku
  - Consider using HTTP POST or WebSocket from local machine to Heroku

## Customizing the Hardware Logic

Edit the `control_real_hardware()` function in `device_controller.py`:

```python
# Example: Use input_values[2] to control runtime
runtime = input_values[2] if len(input_values) > 2 else 1

# Example: Different angle mapping
angle1 = input_values[0] * 1.7  # Scale 0-100 to 0-170
```

## Troubleshooting

**"Module not found" errors in hardware mode:**
- Ensure ThorLabs Kinesis is installed
- Ensure TimeTagger SDK is installed
- Run on Windows only

**No output from device_controller.py:**
- Check that `experiment.py` is passing input correctly
- Look at Heroku logs: `heroku logs --tail`

**Device connection issues:**
- Reconnect USB cable
- Open Kinesis software, connect, then close
- Check Device ID matches your hardware
