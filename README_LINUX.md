# Iran Conduit Firewall - Linux Edition + VPN Monitoring Dashboard

Complete solution for running Psiphon Conduit on Linux with Iran-only firewall and real-time connection monitoring.

## 📦 What's Included

This project contains two main components:

### 1. Iran-Only Firewall ([iran_firewall_linux.py](iran_firewall_linux.py))
Block non-Iranian connections to your VPN server using iptables and ipset.

### 2. VPN Monitoring Dashboard ([dashboard/](dashboard/))
Real-time web-based dashboard showing live connections, geographic data, and statistics.

---

## 🚀 Quick Start

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    iptables ipset conntrack geoipupdate iproute2
```

### Option A: Firewall Only

```bash
# Make script executable
chmod +x iran_firewall_linux.py

# Run firewall configuration
sudo python3 iran_firewall_linux.py

# Follow menu to:
# 1. Enable Iran-only mode
# 2. Configure VPN interface (tun0, wg0, etc.)
```

### Option B: Dashboard Only

```bash
# Navigate to dashboard directory
cd dashboard

# Run automated deployment
chmod +x deploy.sh
sudo ./deploy.sh

# Access dashboard at http://YOUR_IP:8080
# Login: admin / admin123 (change this!)
```

### Option C: Both (Recommended)

```bash
# 1. Set up firewall
sudo python3 iran_firewall_linux.py
# Enable Iran-only mode

# 2. Deploy dashboard
cd dashboard
sudo ./deploy.sh

# 3. Monitor connections in real-time!
# Open browser to http://YOUR_IP:8080
```

---

## 📖 Documentation

### Firewall Documentation

See main [README.md](README.md) for:
- How the firewall works
- IP source configuration
- Troubleshooting
- Making rules persistent

Key features:
- Uses iptables + ipset for efficient filtering
- Downloads Iran IP ranges from multiple sources
- Whitelist DNS servers
- Only affects VPN traffic, not your server

### Dashboard Documentation

See [dashboard/README.md](dashboard/README.md) for:
- Complete API reference
- WebSocket events
- Security configuration
- Production deployment with Nginx
- Troubleshooting guide

See [DASHBOARD_ARCHITECTURE.md](DASHBOARD_ARCHITECTURE.md) for:
- Architecture diagrams (minimal vs production)
- Data collection methods (ss, conntrack, eBPF)
- GeoIP integration
- Scaling considerations

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Linux Server (Ubuntu)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │        iran_firewall_linux.py                  │         │
│  │        iptables + ipset rules                  │         │
│  │        Block non-Iran IPs                      │         │
│  └────────────────┬───────────────────────────────┘         │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │         VPN Application (Psiphon)              │         │
│  │         Only accepts Iran connections          │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │      Connection Tracking (conntrack/ss)        │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │      Dashboard Collector (collector.py)        │         │
│  │      • Polls every 5 seconds                   │         │
│  │      • GeoIP lookup                            │         │
│  │      • SQLite storage                          │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │      Web Dashboard (app.py)                    │         │
│  │      • Flask + WebSocket                       │         │
│  │      • Real-time updates                       │         │
│  │      • REST API                                │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │ Port 8080                                │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │   Web Browser    │
          │   • Live map     │
          │   • Statistics   │
          │   • Charts       │
          └──────────────────┘
```

---

## 🎯 Use Cases

### 1. Maximize Bandwidth for Iranian Users
Use the firewall to block non-Iran IPs, ensuring your VPN bandwidth goes only to Iranian users who need it most.

```bash
sudo python3 iran_firewall_linux.py
# Select: Enable Iran-only mode
```

### 2. Monitor Connection Quality
Use the dashboard to see:
- How many users are connected
- Where they're connecting from
- Bandwidth usage patterns
- Connection stability over time

```bash
cd dashboard
sudo ./deploy.sh
# Access http://YOUR_IP:8080
```

### 3. Detect and Investigate Issues
- See sudden drops in connections
- Identify geographic patterns
- Monitor bandwidth usage
- Track connection sources

### 4. Production VPN Server Management
- Real-time monitoring of your Psiphon Conduit server
- Geographic insights into your user base
- Historical data for capacity planning
- API integration with other tools

---

## 🔒 Security Best Practices

### 1. Change Default Credentials

```bash
# Set environment variables
export ADMIN_USERNAME='your_secure_username'
export ADMIN_PASSWORD='your_secure_password_here'

# Restart dashboard
sudo systemctl restart vpn-dashboard
```

### 2. Use Firewall to Restrict Dashboard Access

```bash
# Allow only your IP
sudo ufw allow from YOUR_IP_ADDRESS to any port 8080

# Or use Nginx with authentication
# See dashboard/README.md for Nginx setup
```

### 3. Enable HTTPS

Use Nginx as reverse proxy with Let's Encrypt SSL:

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 4. Keep Software Updated

```bash
# Update system
sudo apt update && sudo apt upgrade

# Update GeoIP databases
sudo geoipupdate

# Update Python dependencies
cd /opt/vpn-monitor
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

---

## 📊 Dashboard Features

### Real-time Statistics
- Active connection count
- Bandwidth in/out
- Countries connected
- Connection timeline

### Interactive Map
- Accurate geographic visualization using Leaflet.js
- Shows exact connection locations (city-level)
- Marker size indicates connection count
- Click markers for details

### Historical Charts
- Connection trends over time
- Bandwidth usage patterns
- Country distribution
- Customizable time ranges

### Live Updates
- WebSocket-based real-time data
- Updates every 2 seconds
- No page refresh needed
- Minimal latency

---

## 🛠️ Advanced Configuration

### Custom VPN Interface

```bash
# For WireGuard
sudo python3 iran_firewall_linux.py
# Configure interface: wg0

# For OpenVPN
# Configure interface: tun0

# For custom interface
# Configure interface: your-interface-name
```

### Custom Collection Interval

```bash
# Collect every 10 seconds (lower load)
sudo python3 dashboard/collector.py --interval 10

# Collect every 2 seconds (higher resolution)
sudo python3 dashboard/collector.py --interval 2
```

### Database Location

```bash
# Use custom database path
export DB_PATH='/var/lib/vpn-monitor/connections.db'

# Restart services
sudo systemctl restart vpn-collector vpn-dashboard
```

### Data Retention

Edit `dashboard/collector.py`:

```python
# Change from 7 days to 30 days
def cleanup_old_data(self, days=30):
```

---

## 🐛 Troubleshooting

### Firewall Issues

```bash
# Check iptables rules
sudo iptables -L IRAN_CONDUIT -n -v

# Check ipset
sudo ipset list IRAN_CONDUIT_IRAN

# View firewall logs
sudo journalctl -k | grep IRAN-BLOCK

# Disable if needed
sudo python3 iran_firewall_linux.py
# Select: Disable Iran-only mode
```

### Dashboard Issues

```bash
# Check services
sudo systemctl status vpn-collector
sudo systemctl status vpn-dashboard

# View logs
sudo journalctl -u vpn-collector -f
sudo journalctl -u vpn-dashboard -f

# Test collector manually
sudo python3 dashboard/collector.py --interface tun0

# Test web server manually
python3 dashboard/app.py --debug
```

### Connection Detection Issues

```bash
# Verify interface exists
ip link show tun0

# Check active connections manually
ss -tunap | grep tun0

# Test conntrack
sudo conntrack -L -p udp

# Run collector with debug
sudo python3 dashboard/collector.py --interface tun0 -t 5
```

### GeoIP Issues

```bash
# Check database
ls -lh /usr/share/GeoIP/GeoLite2-City.mmdb

# Update database
sudo geoipupdate

# Test GeoIP
python3 -c "
import geoip2.database
reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-City.mmdb')
print(reader.city('8.8.8.8').country.name)
"
```

---

## 📦 File Structure

```
iran-conduit-firewall-Linux/
├── iran_firewall_linux.py      # Linux firewall script
├── iran_firewall.py             # Original Windows script
├── README.md                    # Main project README
├── README_LINUX.md              # This file
├── DASHBOARD_ARCHITECTURE.md    # Architecture guide
├── LICENSE
└── dashboard/
    ├── collector.py             # Data collection daemon
    ├── app.py                   # Flask web server
    ├── requirements.txt         # Python dependencies
    ├── deploy.sh                # Automated deployment
    ├── README.md                # Dashboard documentation
    └── templates/
        ├── login.html           # Login page
        └── dashboard.html       # Main dashboard
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

### Firewall Component
- IP Lists: ipdeny.com, herrbischoff/country-ip-blocks
- Inspired by the need to support Iranian users during shutdowns

### Dashboard Component
- **Leaflet.js**: Map visualization
- **Chart.js**: Data charts
- **Flask**: Web framework
- **Socket.IO**: Real-time updates
- **MaxMind GeoLite2**: Geographic data

---

## 🆘 Support

### Documentation
- [Firewall README](README.md)
- [Dashboard README](dashboard/README.md)
- [Architecture Guide](DASHBOARD_ARCHITECTURE.md)

### Getting Help
1. Check troubleshooting sections in documentation
2. Review logs: `sudo journalctl -u vpn-collector -f`
3. Open an issue on GitHub with:
   - Your OS and version
   - Error messages
   - Relevant logs

---

## 🚀 What's Next?

Planned features:
- [ ] Email alerts for connection issues
- [ ] Telegram bot integration
- [ ] Mobile-responsive dashboard improvements
- [ ] Export data to CSV/JSON
- [ ] Multi-server monitoring
- [ ] Advanced analytics and predictions
- [ ] Docker containerization
- [ ] Kubernetes deployment configs

---

**Made with ❤️ for the Iranian people**

*Help them stay connected during internet shutdowns by sharing this tool!*
