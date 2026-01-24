# Iran-Only Firewall for Psiphon Conduit - Linux Edition

Block non-Iranian connections to your VPN server and maximize bandwidth for Iranian users during internet shutdowns.

## Features

- ✅ **Iran-only filtering** - Block all non-Iranian IPs from connecting to your VPN
- ✅ **Admin IP whitelisting** - Always allow your admin IP to access web services
- ✅ **Efficient ipset matching** - Handle 1000s of IP ranges with minimal performance impact
- ✅ **Auto IP updates** - Download latest Iran IP ranges from multiple sources
- ✅ **DNS whitelisting** - Ensure DNS servers can always connect
- ✅ **VPN-only filtering** - Your server and other services work normally
- ✅ **Easy management** - Simple menu-driven interface
- ✅ **Persistent rules** - Survive reboots with iptables-persistent

## Quick Start

### Prerequisites

Ubuntu 20.04+ or Debian 11+ server with:
```bash
sudo apt update
sudo apt install -y python3 iptables ipset iproute2
```

### Installation

```bash
# Make script executable
chmod +x iran_firewall_linux.py

# Run the firewall
sudo python3 iran_firewall_linux.py
```

### First Time Setup

1. **Configure VPN Interface**: The script will auto-detect your VPN interface (tun0, wg0, etc.)
2. **Add Admin IP**: Enter your IP address to whitelist for web services access
3. **Enable Iran-only mode**: Select option 1 from the menu
4. **Done!** Only Iranian IPs can now connect to your VPN

## How It Works

The firewall uses Linux iptables and ipset to efficiently block connections:

1. **Downloads Iran IP ranges** from multiple sources (ipdeny.com, GitHub)
2. **Creates ipset** for fast IP matching (handles 1000s of IPs efficiently)
3. **Applies iptables rules**:
   - ✅ Allow your admin IP (highest priority)
   - ✅ Allow DNS servers
   - ✅ Allow Iran IP ranges
   - ❌ Block everything else
4. **Only affects VPN traffic** - Your server's SSH, web services, etc. work normally

```
┌─────────────────────────────────────────────┐
│           Linux Server (Ubuntu)              │
├─────────────────────────────────────────────┤
│                                              │
│  Admin IP (Your IP)                         │
│  └─> ✅ ALWAYS ALLOWED (High Priority)      │
│                                              │
│  Iran IPs (1.2.3.4)                         │
│  └─> VPN Port ──> ✅ ALLOWED                │
│                                              │
│  Non-Iran IPs (5.6.7.8)                     │
│  └─> VPN Port ──> ❌ BLOCKED                │
│                                              │
│  All IPs (Any Country)                      │
│  └─> SSH/Web/Other Services ──> ✅ ALLOWED  │
│                                              │
└─────────────────────────────────────────────┘
```

## Menu Options

When you run the script, you'll see:

```
╔═══════════════════════════════════════════════════════════════════╗
║       🇮🇷 IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT v1.0.0-linux    ║
╠═══════════════════════════════════════════════════════════════════╣
║  Maximize bandwidth for Iranian users during internet shutdowns  ║
╚═══════════════════════════════════════════════════════════════════╝

  MAIN MENU
─────────────────────────────────────────────
  1. 🟢 Enable Iran-only mode
  2. 🔴 Disable Iran-only mode
  3. 📊 Check status
  4. ⚙️  Configure VPN interface/port
  5. 🔐 Manage admin IP whitelist
  6. ❓ Help
  0. 🚪 Exit
─────────────────────────────────────────────
```

### Option 1: Enable Iran-only Mode
- Auto-detects your VPN interface
- Prompts for your admin IP address
- Downloads latest Iran IP ranges (1000+ ranges)
- Creates firewall rules
- Shows summary of what was configured

### Option 2: Disable Iran-only Mode
- Removes all firewall rules
- VPN accepts connections from all countries again

### Option 3: Check Status
- Shows if Iran-only mode is active
- Displays number of active rules
- Shows VPN interface status
- Displays admin IP whitelist

### Option 4: Configure VPN Interface/Port
- Change VPN interface (tun0, wg0, etc.)
- Set VPN port (optional)
- Settings are saved for next time

### Option 5: Manage Admin IP Whitelist
- Add/remove admin IPs
- View current whitelist
- IPs get highest priority access

## Admin IP Whitelisting

**Important**: When enabling Iran-only mode, you'll be asked to enter your admin IP address. This ensures you can always access your server's web services (control panels, SSH, etc.) even when the VPN firewall is active.

### Why Admin IP Whitelisting?

Without admin IP whitelisting, if you're not in Iran:
- ❌ You might get blocked from accessing your server
- ❌ Can't access web control panels
- ❌ Can't manage your server remotely

With admin IP whitelisting:
- ✅ Your IP always has full access (highest priority)
- ✅ Access web services, SSH, everything
- ✅ VPN firewall only blocks VPN connections, not admin traffic

### How to Find Your IP

```bash
# Method 1: Check from your local machine
curl ifconfig.me

# Method 2: Check what IP is connecting to server
# (Look at SSH connection logs)
```

### Adding Multiple Admin IPs

You can add multiple admin IPs (office, home, VPN, etc.):

```bash
# Run the script
sudo python3 iran_firewall_linux.py

# Select: 5. Manage admin IP whitelist
# Choose: Add admin IP
# Enter: Your IP address
```

## Making Rules Persistent

To keep firewall rules after server reboot:

```bash
# Install iptables-persistent
sudo apt install iptables-persistent

# Save current rules
sudo netfilter-persistent save

# Rules will now survive reboots
```

To update rules:
```bash
# Make changes using the script
sudo python3 iran_firewall_linux.py

# Save again
sudo netfilter-persistent save
```

## Configuration

Settings are saved in `config.json` in the same directory:

```json
{
  "vpn_interface": "tun0",
  "vpn_port": "443",
  "admin_ips": [
    "203.0.113.10",
    "198.51.100.25"
  ]
}
```

You can edit this file directly if needed.

## Troubleshooting

### Firewall Not Working

```bash
# Check iptables rules
sudo iptables -L IRAN_CONDUIT -n -v

# Check ipset
sudo ipset list IRAN_CONDUIT_IRAN

# View firewall logs
sudo journalctl -k | grep IRAN-BLOCK
```

### VPN Interface Not Found

```bash
# List all interfaces
ip link show

# Check if VPN is running
sudo systemctl status openvpn
# or
sudo systemctl status wg-quick@wg0
# or
ps aux | grep conduit
```

### Can't Access Server After Enabling

```bash
# Disable firewall immediately
sudo python3 iran_firewall_linux.py
# Select: 2. Disable Iran-only mode

# Or manually remove rules
sudo iptables -F IRAN_CONDUIT
sudo iptables -X IRAN_CONDUIT
sudo ipset destroy IRAN_CONDUIT_IRAN
```

### Download Failed

If Iran IP download fails:
```bash
# Check internet connection
ping -c 3 8.8.8.8

# Check if sources are accessible
curl -I https://www.ipdeny.com/ipblocks/data/countries/ir.zone

# Try again - the script uses multiple sources
```

## Advanced Usage

### Manual IP Range Management

```bash
# View current Iran IPs
sudo ipset list IRAN_CONDUIT_IRAN

# Add custom IP range
sudo ipset add IRAN_CONDUIT_IRAN 1.2.3.0/24

# Remove IP range
sudo ipset del IRAN_CONDUIT_IRAN 1.2.3.0/24
```

### Custom DNS Servers

Edit the script to add your DNS servers:

```python
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4",           # Google DNS
    "1.1.1.1", "1.0.0.1",           # Cloudflare DNS
    "YOUR_DNS_IP_HERE",             # Your custom DNS
]
```

### Port-Specific Filtering

```bash
# Run script
sudo python3 iran_firewall_linux.py

# Select: 4. Configure VPN interface/port
# Enter your VPN port (e.g., 443)

# Rules will only apply to that specific port
```

## Security Best Practices

1. **Always set admin IP** - Don't lock yourself out!
2. **Test before production** - Try on a test server first
3. **Keep backups** - Save your config.json
4. **Monitor logs** - Check for blocked legitimate traffic
5. **Update IP ranges** - Re-enable monthly to get latest Iran IPs
6. **Use with caution** - Understand firewall rules before deploying

## IP Sources

Iran IP ranges are downloaded from:
- [ipdeny.com](https://www.ipdeny.com/ipblocks/) - Updated daily
- [herrbischoff/country-ip-blocks](https://github.com/herrbischoff/country-ip-blocks) - GitHub backup source

## Requirements

- Ubuntu 20.04+ or Debian 11+ (or compatible)
- Python 3.6+
- Root/sudo access
- iptables and ipset
- Active VPN service

## Uninstall

```bash
# Disable Iran-only mode
sudo python3 iran_firewall_linux.py
# Select: 2. Disable Iran-only mode

# Remove installed packages (optional)
sudo apt remove ipset

# Delete script and config
rm iran_firewall_linux.py config.json
```

## FAQ

**Q: Will this affect my SSH access?**
A: No, the firewall only affects your VPN traffic. SSH and other services work normally. Plus, your admin IP is whitelisted.

**Q: Can I use this with OpenVPN/WireGuard/etc?**
A: Yes! It works with any VPN that creates a network interface (tun0, wg0, tap0, etc.)

**Q: How often should I update Iran IP ranges?**
A: Monthly is recommended. Just disable and re-enable Iran-only mode.

**Q: What if my IP changes?**
A: Use option 5 to update your admin IP, or add multiple IPs if you have dynamic IP.

**Q: Does this work on Raspberry Pi?**
A: Yes! Works on any Linux system with iptables and ipset.

**Q: Can I block specific countries instead of allowing only Iran?**
A: The script is designed for Iran-only, but you can modify it or use similar logic for other countries.

## License

MIT License - See LICENSE file for details

## Credits

- IP Lists: ipdeny.com, herrbischoff/country-ip-blocks
- Inspired by the need to support Iranian users during internet shutdowns

## Support

For issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `sudo iptables -L IRAN_CONDUIT -n -v`
3. Open an issue on GitHub

---

**Made with ❤️ for the Iranian people**

*Share this tool to help more people support Iranian users during shutdowns!*
