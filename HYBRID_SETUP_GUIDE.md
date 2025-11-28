# Hybrid Architecture Setup Guide

## Overview: Your Network Setup

```
Your Mac (85.255.233.64 via VPN)
  ↓ RoyalTSX Remote Desktop
Windows Machine (172.20.118.125)
  ├─ ThorLabs Polarizers (USB)
  ├─ TimeTagger (USB)
  ├─ bridge.py (runs here)
  └─ device_controller.py (runs here)
  
  ↑ ngrok tunnel (makes it accessible to internet)
  ↑
Heroku Cloud (dt-moth.herokuapp.com)
  ├─ main.js (Socket.IO server)
  ├─ experiment.py (forwards to bridge if hardware mode)
  └─ Web UI (mode toggle)
  
  ↓ Socket.IO
TouchDesigner
```

## How It Works

1. **Simulation Mode:** Everything runs on Heroku (cloud)
2. **Hardware Mode:** Heroku forwards commands to Windows machine → Real hardware

---

## Step-by-Step Setup

### Part 1: Setup Windows Machine (172.20.118.125)

**1. Copy files to Windows machine**

Via RoyalTSX, copy these files to the Windows machine:
- `bridge.py`
- `device_controller.py`
- `config.json`
- `requirements-bridge.txt`

**2. Install Python dependencies on Windows**

```cmd
pip install -r requirements-bridge.txt
```

**3. Download and install ngrok**

- Download: https://ngrok.com/download
- Sign up for free account
- Install on Windows machine

**4. Start the bridge server**

Open Command Prompt on Windows machine:

```cmd
python bridge.py
```

You should see:
```
🔌 LOCAL HARDWARE BRIDGE - STARTING ON WINDOWS MACHINE
Bridge Port: 5000
Bridge URL: http://172.20.118.125:5000
```

**5. Open ngrok tunnel (in separate Command Prompt)**

```cmd
ngrok http 5000
```

You'll see output like:
```
Forwarding    https://abc123xyz.ngrok.io -> http://localhost:5000
```

**✅ Copy the ngrok URL (https://abc123xyz.ngrok.io)**

### Part 2: Configure Heroku

**1. Set the bridge URL on Heroku**

From your Mac terminal:

```bash
heroku config:set BRIDGE_URL=https://abc123xyz.ngrok.io -a dt-moth
```

**2. Deploy updated code to Heroku**

```bash
cd /Users/astrydpark/Documents/GitHub/deutschetelekom-simul
git add .
git commit -m "Add hybrid architecture with bridge support"
git push heroku main
```

**3. Verify Heroku config**

```bash
heroku config -a dt-moth
```

You should see:
```
BRIDGE_URL: https://abc123xyz.ngrok.io
```

### Part 3: Using the System

**1. Access the Web UI**

Go to: https://dt-moth.herokuapp.com

**2. Choose Mode:**

- **🔄 Simulation Mode:** Uses random data (no Windows machine needed)
- **🔌 Hardware Mode:** Forwards to Windows machine → Real hardware

**3. Test the connection:**

When you switch to Hardware Mode, check:
- Windows Command Prompt (bridge.py) should show incoming requests
- Heroku logs: `heroku logs --tail -a dt-moth`

---

## Data Flow Diagrams

### Simulation Mode (No Bridge)
```
TouchDesigner
  ↓ (sends knob values)
Heroku (experiment.py)
  ↓ (calls local device_controller.py)
Heroku (simulation: random data)
  ↓ (returns 4 values)
TouchDesigner
```

### Hardware Mode (With Bridge)
```
TouchDesigner
  ↓ (sends knob values)
Heroku (experiment.py)
  ↓ (HTTP POST to BRIDGE_URL)
ngrok tunnel
  ↓
Windows Machine (172.20.118.125)
  ├─ bridge.py receives request
  ├─ calls device_controller.py
  ├─ moves polarizers
  ├─ reads TimeTagger
  └─ returns 4 coincidence values
  ↓
ngrok tunnel
  ↓
Heroku (experiment.py)
  ↓ (forwards to TouchDesigner)
TouchDesigner
```

---

## Troubleshooting

### Bridge not receiving requests

**Check 1: Is bridge.py running on Windows?**
```cmd
# On Windows
python bridge.py
```

**Check 2: Is ngrok running?**
```cmd
# On Windows (separate terminal)
ngrok http 5000
```

**Check 3: Is BRIDGE_URL set on Heroku?**
```bash
# On Mac
heroku config -a dt-moth
```

**Check 4: Test bridge directly**

From your Mac:
```bash
curl https://your-ngrok-url.ngrok.io/
```

Should return:
```json
{"status": "online", "service": "Local Hardware Bridge", ...}
```

### Hardware mode not working

**Check 1: Is mode set to Hardware in web UI?**
- Go to https://dt-moth.herokuapp.com
- Click "🔌 Hardware Mode"

**Check 2: Check config.json on Windows**
```json
{
  "useRealHardware": true
}
```

**Check 3: Check Heroku logs**
```bash
heroku logs --tail -a dt-moth
```

Look for: `Python: Hardware mode + Bridge detected. Forwarding to: ...`

### Ngrok URL changes

⚠️ **Important:** Free ngrok URLs change every time you restart ngrok!

If you restart ngrok, you need to:
1. Copy new ngrok URL
2. Update Heroku: `heroku config:set BRIDGE_URL=https://new-url.ngrok.io -a dt-moth`

**Solution:** Upgrade to ngrok paid plan for static URLs

---

## Quick Reference Commands

### On Windows Machine (via RoyalTSX)

```cmd
# Start bridge
python bridge.py

# Start ngrok (separate terminal)
ngrok http 5000

# Check if device_controller.py works
echo {"knob_values": [45, 90, 1]} | python device_controller.py
```

### On Your Mac

```bash
# Deploy to Heroku
git push heroku main

# Set bridge URL
heroku config:set BRIDGE_URL=https://your-ngrok-url.ngrok.io -a dt-moth

# View logs
heroku logs --tail -a dt-moth

# Check config
heroku config -a dt-moth

# Test bridge
curl https://your-ngrok-url.ngrok.io/
```

---

## Security Notes

- ngrok tunnels are HTTPS by default (secure)
- No authentication on bridge (assumes trusted network)
- If needed, add API key authentication to bridge.py
- VPN provides additional security layer

---

## Cost & Alternatives

### ngrok Free Tier
- ✅ HTTPS tunnels
- ✅ Unlimited requests
- ❌ URL changes on restart
- ❌ Limited concurrent tunnels

### ngrok Paid ($8-10/month)
- ✅ Static URLs (no need to update Heroku)
- ✅ Custom domains
- ✅ More tunnels

### Alternative: SSH Tunnel
If you have SSH access to Windows machine:
```bash
ssh -R 5000:localhost:5000 user@windows-machine
```

But ngrok is simpler for your setup.

---

## Testing Checklist

- [ ] bridge.py running on Windows (172.20.118.125)
- [ ] ngrok tunnel active
- [ ] BRIDGE_URL set on Heroku
- [ ] Code deployed to Heroku
- [ ] Web UI shows correct mode
- [ ] TouchDesigner can connect to Heroku
- [ ] Test simulation mode (should work without bridge)
- [ ] Test hardware mode (should forward to bridge)
- [ ] Check Heroku logs for "Bridge success"
- [ ] Check Windows terminal for "[BRIDGE] Received from Heroku"
