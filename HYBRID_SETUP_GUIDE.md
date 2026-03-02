# Hybrid Architecture Setup Guide

## This is the workflow between TD and remote server & H/W.

```text
VPN-connected remote connection
  | RoyalTSX
Windows Machine (T-Labs)
  |- ThorLabs Polarizers
  |- TimeTagger
  |- bridge.py (connect)
  +- device_controller.py (control)

  ^ ngrok tunnel (makes H/W accessible)
  ^
Heroku Cloud
  |- main.js (Socket.IO server)
  |- device_controller.py (directly calls the control operations)
  +- Website

  | Socket.IO
TouchDesigner
```

## How It Works

1. **Simulation Mode:** Everything runs through Heroku
2. **Hardware Mode:** Heroku app forwards commands to T-Labs machine via bridge.py
