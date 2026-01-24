# VPN Monitoring Dashboard

A real-time web-based dashboard for monitoring VPN connections without relying on VPN application logs. Works at the OS/network layer using Linux socket state and connection tracking.

## Features

- **Real-time Connection Monitoring**: Live view of active VPN connections
- **Geographic Visualization**: Interactive world map showing connection sources
- **Live Statistics**: Connection counts, bandwidth usage, country distribution
- **Historical Data**: Charts showing connection trends over time
- **Modern UI**: Dark-themed, futuristic interface with real-time updates
- **Secure**: Login authentication with session management

## Screenshots

*(Dashboard with map, charts, and live statistics)*

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Linux Server (Ubuntu)               │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐         ┌──────────────┐     │
│  │   VPN App    │────────▶│  conntrack/  │     │
│  │  (Psiphon)   │         │     ss       │     │
│  └──────────────┘         └──────┬───────┘     │
│                                   │              │
│                                   ▼              │
│  ┌────────────────────────────────────────┐    │
│  │  collector.py - Data Collector         │    │
│  │  • Polls ss/conntrack every 5 sec      │    │
│  │  • GeoIP lookup (MaxMind)              │    │
│  │  • Stores in SQLite                    │    │
│  └──────────────┬─────────────────────────┘    │
│                 │                                │
│                 ▼                                │
│  ┌────────────────────────────────────────┐    │
│  │   app.py - Flask Web Server            │    │
│  │   • REST API for data                  │    │
│  │   • WebSocket for live updates         │    │
│  │   • Authentication                     │    │
│  └──────────────┬─────────────────────────┘    │
│                 │ Port 8080                     │
└─────────────────┼─────────────────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │   Web Browser   │
        │  (Dashboard)    │
        └─────────────────┘
```

## Requirements

### System Requirements
- Ubuntu 20.04+ or Debian 11+ (or compatible Linux)
- Python 3.8+
- Root access (sudo)
- Active VPN service (Psiphon, OpenVPN, WireGuard, etc.)

### Dependencies
```bash
# System packages
sudo apt install python3 python3-pip python3-venv \
    iptables ipset conntrack geoipupdate

# Python packages (installed via requirements.txt)
Flask, flask-socketio, geoip2, eventlet
```

## Quick Start

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Make deploy script executable
chmod +x deploy.sh

# 2. Run deployment (requires sudo)
sudo ./deploy.sh

# 3. Access dashboard
# Open browser to http://YOUR_SERVER_IP:8080
# Login: admin / admin123
```

### Option 2: Manual Installation

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    iptables ipset conntrack geoipupdate

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up GeoIP (see GeoIP Setup section)

# 5. Start collector (in one terminal)
sudo python3 collector.py --interface tun0

# 6. Start web server (in another terminal)
python3 app.py --host 0.0.0.0 --port 8080

# 7. Access dashboard
# Open browser to http://localhost:8080
# Login: admin / admin123
```

## GeoIP Setup

Geographic features require MaxMind GeoLite2 databases (free).

### 1. Create MaxMind Account
- Sign up at: https://www.maxmind.com/en/geolite2/signup
- Generate a license key in your account

### 2. Configure GeoIP Updates

```bash
# Edit GeoIP config
sudo nano /etc/GeoIP.conf

# Add your credentials:
AccountID YOUR_ACCOUNT_ID
LicenseKey YOUR_LICENSE_KEY
EditionIDs GeoLite2-City GeoLite2-Country
DatabaseDirectory /usr/share/GeoIP

# Download databases
sudo geoipupdate

# Verify installation
ls -lh /usr/share/GeoIP/
```

### 3. Auto-update GeoIP Databases

```bash
# Add cron job for weekly updates
sudo crontab -e

# Add this line:
0 2 * * 3 /usr/bin/geoipupdate
```

## Configuration

### Collector Options

```bash
python3 collector.py --help

Options:
  -i, --interface   VPN interface name (default: tun0)
  -p, --port        VPN port (optional)
  -d, --database    SQLite database path (default: vpn_connections.db)
  -g, --geoip-db    GeoIP database path
  -t, --interval    Collection interval in seconds (default: 5)
  --no-conntrack    Disable conntrack monitoring
```

### Web Server Options

```bash
python3 app.py --help

Options:
  --host            Host to bind to (default: 0.0.0.0)
  --port            Port to bind to (default: 8080)
  --debug           Enable debug mode
  --db              Database path (default: vpn_connections.db)
```

### Environment Variables

```bash
# Set custom credentials
export ADMIN_USERNAME='your_username'
export ADMIN_PASSWORD='your_secure_password'
export SECRET_KEY='random-secret-key-here'

# Set database path
export DB_PATH='/path/to/database.db'
```

## Systemd Services

The deployment script creates systemd services for automatic startup.

### Service Management

```bash
# Check status
sudo systemctl status vpn-collector
sudo systemctl status vpn-dashboard

# View logs
sudo journalctl -u vpn-collector -f
sudo journalctl -u vpn-dashboard -f

# Restart services
sudo systemctl restart vpn-collector
sudo systemctl restart vpn-dashboard

# Stop services
sudo systemctl stop vpn-collector vpn-dashboard

# Disable services
sudo systemctl disable vpn-collector vpn-dashboard
```

### Service Files Location

- Collector: `/etc/systemd/system/vpn-collector.service`
- Dashboard: `/etc/systemd/system/vpn-dashboard.service`

## Security Recommendations

### 1. Change Default Password

**IMPORTANT**: Change the default admin password immediately!

```bash
# Method 1: Environment variables
export ADMIN_USERNAME='myuser'
export ADMIN_PASSWORD='MySecurePassword123!'

# Method 2: Edit app.py
nano app.py
# Change ADMIN_USERNAME and ADMIN_PASSWORD constants
```

### 2. Use HTTPS (Production)

Set up Nginx as a reverse proxy with SSL:

```nginx
# /etc/nginx/sites-available/vpn-monitor
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:8080/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Firewall Configuration

```bash
# Allow only specific IPs to access dashboard
sudo ufw allow from YOUR_IP_ADDRESS to any port 8080

# Or use Nginx and close direct access
sudo ufw deny 8080
sudo ufw allow 443/tcp
```

### 4. Generate Strong Secret Key

```bash
# Generate random secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Set it as environment variable
export SECRET_KEY='generated-key-here'
```

## API Endpoints

All endpoints require authentication (session cookie).

### Statistics

```bash
# Current stats (real-time)
GET /api/stats/current

# Response:
{
  "active_ips": 42,
  "total_connections": 156,
  "bytes_in": 1048576,
  "bytes_out": 524288,
  "top_countries": [...]
}

# Summary statistics
GET /api/stats/summary?hours=24

# Country statistics
GET /api/stats/countries?hours=24
```

### Map Data

```bash
# Get map markers
GET /api/map-data?minutes=5

# Response:
{
  "markers": [
    {
      "ip": "1.2.3.4",
      "country_code": "IR",
      "country_name": "Iran",
      "city": "Tehran",
      "lat": 35.6892,
      "lon": 51.3890,
      "count": 5,
      "last_seen": "2024-01-15T12:34:56"
    }
  ],
  "total": 42
}
```

### Historical Data

```bash
# Timeline data for charts
GET /api/history/timeline?hours=24&granularity=hour

# Response:
{
  "timeline": [
    {
      "time_bucket": "2024-01-15 12:00:00",
      "unique_ips": 25,
      "total_connections": 150,
      "total_bytes": 10485760
    }
  ]
}
```

### Recent Connections

```bash
# Get recent connection list
GET /api/connections/recent?limit=50

# Response:
{
  "connections": [...],
  "count": 50
}
```

## WebSocket Events

### Client → Server

```javascript
// Subscribe to real-time updates
socket.emit('subscribe', {});
```

### Server → Client

```javascript
// Connection status
socket.on('status', (data) => {
  console.log(data.connected);
});

// Real-time updates (every 2 seconds)
socket.on('realtime_update', (data) => {
  console.log(data.active_ips);
  console.log(data.bytes_in);
  console.log(data.bytes_out);
});
```

## Troubleshooting

### Collector not finding connections

```bash
# Check if VPN interface exists
ip link show tun0

# Check if conntrack is working
sudo conntrack -L

# Manually test ss command
ss -tunap | grep tun0

# Run collector with verbose output
sudo python3 collector.py --interface tun0 -t 5
```

### GeoIP not working

```bash
# Verify database exists
ls -lh /usr/share/GeoIP/GeoLite2-City.mmdb

# Test GeoIP manually
python3 -c "
import geoip2.database
reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-City.mmdb')
response = reader.city('8.8.8.8')
print(response.country.name, response.city.name)
"

# Update databases
sudo geoipupdate
```

### Dashboard not accessible

```bash
# Check if service is running
sudo systemctl status vpn-dashboard

# Check if port is listening
sudo netstat -tlnp | grep 8080

# Check logs
sudo journalctl -u vpn-dashboard -n 50

# Test manually
python3 app.py --host 0.0.0.0 --port 8080 --debug
```

### WebSocket not connecting

```bash
# Check firewall
sudo ufw status

# Check browser console for errors
# Open browser DevTools → Console

# Verify Socket.IO is loaded
# Browser console: typeof io
```

## Performance Tuning

### Database Optimization

```bash
# Vacuum database regularly
sqlite3 vpn_connections.db "VACUUM;"

# Analyze query performance
sqlite3 vpn_connections.db "ANALYZE;"
```

### Adjust Collection Interval

```bash
# For high-traffic VPNs, increase interval
python3 collector.py --interval 10

# For low-traffic VPNs, decrease interval
python3 collector.py --interval 2
```

### Data Retention

Edit `collector.py` to change data retention:

```python
# Keep data for 30 days instead of 7
collector.cleanup_old_data(days=30)
```

## Upgrading

```bash
# 1. Stop services
sudo systemctl stop vpn-collector vpn-dashboard

# 2. Backup database
cp vpn_connections.db vpn_connections.db.backup

# 3. Pull latest code
git pull

# 4. Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. Restart services
sudo systemctl start vpn-collector vpn-dashboard
```

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop vpn-collector vpn-dashboard
sudo systemctl disable vpn-collector vpn-dashboard

# Remove service files
sudo rm /etc/systemd/system/vpn-collector.service
sudo rm /etc/systemd/system/vpn-dashboard.service

# Reload systemd
sudo systemctl daemon-reload

# Remove installation directory
sudo rm -rf /opt/vpn-monitor

# Optional: Remove dependencies
sudo apt remove geoipupdate
```

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs: `sudo journalctl -u vpn-collector -f`
- Open an issue on GitHub

## Credits

- **Leaflet.js**: Interactive maps
- **Chart.js**: Data visualization
- **MaxMind GeoLite2**: Geographic data
- **Flask**: Web framework
- **Socket.IO**: Real-time communication
