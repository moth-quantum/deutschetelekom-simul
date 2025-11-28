# Hybrid Architecture Setup Guide

## Overview: Your Network Setup

```
My Mac (85.255.233.64 via VPN)
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

1. **Simulation Mode:** Everything runs on simulation (which is deployed on Heroku)
2. **Hardware Mode:** Heroku app forwards commands to Windows machine → Real hardware