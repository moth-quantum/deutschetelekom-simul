# Network Setup: TCP Server → TouchDesigner

## Architecture
```
[This PC via RDP]          [Remote PC with TouchDesigner]
     server.py        →         TCP/IP DAT (Client mode)
   Port 10443                Connects to VPN_IP:10443
```

## Step 1: Open Windows Firewall (on this PC)

Run in PowerShell as Administrator:
```powershell
New-NetFirewallRule -DisplayName "TouchDesigner Data Server" -Direction Inbound -Protocol TCP -LocalPort 10443 -Action Allow
```

Or manually: Windows Defender Firewall → Inbound Rules → New Rule → Port → TCP 10443 → Allow

## Step 2: Find Your VPN IP (on this PC)

Run:
```powershell
ipconfig
```

Look for your VPN adapter (e.g., "TAP-Windows", "Tailscale", "WireGuard") and note the IPv4 address.

## Step 3: Run the Server

```bash
python server.py
```

It will display all available IPs. Share the **VPN IP** with the remote user.

## Step 4: TouchDesigner Setup (on remote PC)

1. Add a **TCP/IP DAT** operator
2. Set:
   - **Protocol**: TCP
   - **Mode**: Client
   - **Address**: `<VPN_IP_FROM_STEP_2>`
   - **Port**: `10443`
   - **Row/Callback Format**: One Per Line
3. Toggle **Active** ON

## Testing

Before TouchDesigner, test with the Python client:
```bash
# Edit test_client.py, set SERVER_IP to the VPN IP
python test_client.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check firewall, verify server is running |
| Timeout | Verify VPN connectivity, ping the IP first |
| Port 443 needed | Change PORT in server.py, requires admin rights |
