# VPN Connection Monitoring Dashboard Architecture

## Overview
Build a web-based dashboard to monitor VPN connections in real-time, showing geographic data, live maps, and statistics - all without relying on VPN application logs.

---

## Part 1: Obtaining Live Connection Data (OS/Network Layer)

### Method 1: Socket State Monitoring (Primary - Best Performance)
**Tool**: `ss` (socket statistics) or `netstat`

```bash
# Show all UDP/TCP connections on VPN interface
ss -tunap

# For real-time monitoring with filters
ss -tunap | grep <VPN_PORT>

# Show only established connections with IP addresses
ss -tunap state established
```

**Advantages**:
- Real-time socket state
- No configuration needed
- Shows source IPs directly
- Very fast

**Data you get**:
- Source IP addresses
- Source ports
- Connection state (ESTABLISHED, etc.)
- Protocol (TCP/UDP)
- Process ID

---

### Method 2: Connection Tracking (Netfilter/conntrack)
**Tool**: `conntrack` - Linux kernel connection tracking

```bash
# Install
sudo apt install conntrack

# Show all tracked connections
conntrack -L

# Watch connections in real-time
conntrack -E

# Filter by interface/protocol
conntrack -L -p udp
```

**Advantages**:
- Kernel-level tracking
- Shows connection lifecycle
- Tracks packets/bytes per connection
- Works even if VPN app doesn't log

**Data you get**:
- Source/destination IPs
- Packets sent/received
- Bytes transferred
- Connection lifetime
- Protocol details

---

### Method 3: Firewall Logging (Best for Historical Data)
**Tool**: iptables with LOG target

```bash
# Log accepted connections (non-blocking)
sudo iptables -I INPUT -i tun0 -j LOG --log-prefix '[VPN-CONN] ' --log-level 4

# View logs
sudo journalctl -k | grep VPN-CONN
sudo tail -f /var/log/kern.log | grep VPN-CONN
```

**Advantages**:
- Persistent logs
- Can track blocked attempts too
- Good for analytics
- Customizable log format

**Data you get**:
- Timestamp
- Source/destination IPs
- Ports
- Protocol
- Packet info

---

### Method 4: eBPF (Production - Most Powerful)
**Tool**: BPF (Berkeley Packet Filter) - Modern Linux observability

```bash
# Using bpftrace for connection tracking
sudo bpftrace -e 'tracepoint:tcp:tcp_probe { printf("%s -> %s\n",
    ntop(args->saddr), ntop(args->daddr)); }'
```

**Advantages**:
- Zero overhead
- Kernel-level visibility
- Real-time streaming
- Production-grade

**Note**: Requires kernel 4.9+ and BPF tools installed

---

## Part 2: Architecture Options

### MINIMAL ARCHITECTURE (Quick Setup, <1 day)

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
│  │  Python Data Collector (collector.py)  │    │
│  │  • Polls ss/conntrack every 1-5 sec    │    │
│  │  • GeoIP lookup (MaxMind DB)           │    │
│  │  • Stores in SQLite                    │    │
│  └──────────────┬─────────────────────────┘    │
│                 │                                │
│                 ▼                                │
│  ┌────────────────────────────────────────┐    │
│  │   Flask Web Server (app.py)            │    │
│  │   • REST API for data                  │    │
│  │   • WebSocket for live updates         │    │
│  │   • Serves HTML/JS dashboard           │    │
│  │   • Simple password auth               │    │
│  └──────────────┬─────────────────────────┘    │
│                 │ Port 8080                     │
└─────────────────┼─────────────────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │   Web Browser   │
        │  (Dark Theme)   │
        │  • Login page   │
        │  • Live map     │
        │  • Statistics   │
        │  • Charts       │
        └─────────────────┘
```

**Tech Stack**:
- **Backend**: Flask (Python)
- **Database**: SQLite (single file)
- **WebSocket**: Flask-SocketIO
- **GeoIP**: MaxMind GeoLite2 (free)
- **Frontend**: Vanilla JS + Leaflet.js (map) + Chart.js

**Pros**:
- Single server
- No external dependencies
- Easy to deploy
- Low resource usage

**Cons**:
- Single point of failure
- Limited scalability
- In-memory data loss on restart

---

### PRODUCTION ARCHITECTURE (Scalable, HA)

```
┌─────────────────────────────────────────────────────────────┐
│                     Linux Server (Ubuntu)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐      ┌─────────────────────────────────┐     │
│  │ VPN App  │─────▶│  eBPF/conntrack Collector       │     │
│  │(Psiphon) │      │  • Streams to message queue     │     │
│  └──────────┘      └───────────┬─────────────────────┘     │
│                                 │                            │
└─────────────────────────────────┼───────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   Redis / RabbitMQ       │
                    │   (Message Queue)        │
                    └──────┬───────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ Worker  │     │ Worker  │     │ Worker  │
    │  Pod 1  │     │  Pod 2  │     │  Pod 3  │
    │• GeoIP  │     │• GeoIP  │     │• GeoIP  │
    │• Process│     │• Process│     │• Process│
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
              ┌────────────────────┐
              │  TimescaleDB       │
              │  (PostgreSQL)      │
              │  • Time-series     │
              │  • Aggregations    │
              └──────┬─────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  API Layer (FastAPI)      │
         │  • REST endpoints         │
         │  • WebSocket server       │
         │  • JWT authentication     │
         │  • Rate limiting          │
         └──────┬────────────────────┘
                │
                ▼
         ┌───────────────────────────┐
         │  Nginx Reverse Proxy      │
         │  • Load balancing         │
         │  • SSL termination        │
         │  • Static file serving    │
         └──────┬────────────────────┘
                │ HTTPS (443)
                ▼
         ┌───────────────────────────┐
         │  React Dashboard          │
         │  • Modern UI framework    │
         │  • Real-time updates      │
         │  • Interactive maps       │
         │  • Responsive design      │
         └───────────────────────────┘
```

**Tech Stack**:
- **Data Collection**: eBPF (bpftrace/bcc)
- **Message Queue**: Redis Streams or RabbitMQ
- **Processing**: Python workers (asyncio)
- **Database**: TimescaleDB (PostgreSQL for time-series)
- **API**: FastAPI (high performance, async)
- **WebSocket**: FastAPI WebSocket
- **Cache**: Redis
- **Frontend**: React + Mapbox GL JS + D3.js
- **Auth**: JWT with refresh tokens
- **Deployment**: Docker + Docker Compose or Kubernetes

**Pros**:
- Horizontally scalable
- High availability
- Fast performance
- Production-ready
- Separation of concerns

**Cons**:
- Complex setup
- Higher resource usage
- More moving parts

---

## Part 3: Data Collection Implementation

### Option A: Minimal Collector (Python)

```python
#!/usr/bin/env python3
"""
VPN Connection Data Collector
Polls ss/conntrack and stores connection data
"""

import subprocess
import re
import time
import sqlite3
from datetime import datetime
import geoip2.database

class ConnectionCollector:
    def __init__(self, db_path='vpn_connections.db',
                 geoip_db='/usr/share/GeoIP/GeoLite2-City.mmdb'):
        self.db_path = db_path
        self.geoip_reader = geoip2.database.Reader(geoip_db)
        self.init_db()

    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                src_ip TEXT NOT NULL,
                src_port INTEGER,
                protocol TEXT,
                state TEXT,
                country TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                bytes_recv INTEGER DEFAULT 0,
                bytes_sent INTEGER DEFAULT 0
            )
        ''')
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON connections(timestamp)
        ''')
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_src_ip
            ON connections(src_ip)
        ''')
        conn.commit()
        conn.close()

    def get_active_connections(self, interface='tun0'):
        """Get active connections using ss"""
        try:
            # Get UDP connections
            result = subprocess.run(
                ['ss', '-tunap', f'src {interface}'],
                capture_output=True,
                text=True
            )

            connections = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if not line.strip():
                    continue

                # Parse ss output
                parts = line.split()
                if len(parts) < 5:
                    continue

                protocol = parts[0]  # tcp or udp
                state = parts[1] if protocol == 'tcp' else 'UNCONN'
                recv_q = parts[2]
                send_q = parts[3]
                local = parts[4]
                peer = parts[5] if len(parts) > 5 else ''

                # Extract peer IP and port
                match = re.match(r'\[(.*?)\]:(\d+)', peer)
                if match:
                    src_ip = match.group(1)
                    src_port = int(match.group(2))

                    connections.append({
                        'src_ip': src_ip,
                        'src_port': src_port,
                        'protocol': protocol,
                        'state': state,
                        'bytes_recv': int(recv_q),
                        'bytes_sent': int(send_q)
                    })

            return connections

        except Exception as e:
            print(f"Error getting connections: {e}")
            return []

    def get_conntrack_data(self):
        """Get connection tracking data (requires root)"""
        try:
            result = subprocess.run(
                ['conntrack', '-L', '-p', 'udp'],
                capture_output=True,
                text=True
            )

            connections = []
            for line in result.stdout.split('\n'):
                if 'src=' not in line:
                    continue

                # Parse conntrack output
                # Example: udp ... src=1.2.3.4 dst=... packets=10 bytes=1234
                src_match = re.search(r'src=([0-9.]+)', line)
                packets_match = re.search(r'packets=(\d+)', line)
                bytes_match = re.search(r'bytes=(\d+)', line)

                if src_match:
                    connections.append({
                        'src_ip': src_match.group(1),
                        'packets': int(packets_match.group(1)) if packets_match else 0,
                        'bytes': int(bytes_match.group(1)) if bytes_match else 0
                    })

            return connections

        except Exception as e:
            print(f"Error getting conntrack data: {e}")
            return []

    def geolocate_ip(self, ip):
        """Get geographic info for IP address"""
        try:
            response = self.geoip_reader.city(ip)
            return {
                'country': response.country.iso_code,
                'city': response.city.name,
                'latitude': response.location.latitude,
                'longitude': response.location.longitude
            }
        except Exception:
            return {
                'country': 'Unknown',
                'city': 'Unknown',
                'latitude': None,
                'longitude': None
            }

    def store_connections(self, connections):
        """Store connections in database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        timestamp = datetime.utcnow().isoformat()

        for conn_data in connections:
            geo = self.geolocate_ip(conn_data['src_ip'])

            c.execute('''
                INSERT INTO connections
                (timestamp, src_ip, src_port, protocol, state,
                 country, city, latitude, longitude, bytes_recv, bytes_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                conn_data['src_ip'],
                conn_data.get('src_port'),
                conn_data.get('protocol', 'udp'),
                conn_data.get('state', 'UNKNOWN'),
                geo['country'],
                geo['city'],
                geo['latitude'],
                geo['longitude'],
                conn_data.get('bytes_recv', 0),
                conn_data.get('bytes_sent', 0)
            ))

        conn.commit()
        conn.close()

    def cleanup_old_data(self, days=7):
        """Remove data older than N days"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            DELETE FROM connections
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        conn.commit()
        conn.close()

    def run(self, interval=5):
        """Run collector in loop"""
        print("Starting VPN connection collector...")
        print(f"Polling every {interval} seconds")

        while True:
            try:
                # Get connections
                connections = self.get_active_connections()

                if connections:
                    print(f"Found {len(connections)} active connections")
                    self.store_connections(connections)

                # Cleanup old data daily
                if int(time.time()) % 86400 < interval:
                    self.cleanup_old_data()

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\nStopping collector...")
                break
            except Exception as e:
                print(f"Error in collection loop: {e}")
                time.sleep(interval)


if __name__ == '__main__':
    collector = ConnectionCollector()
    collector.run(interval=5)
```

---

## Part 4: GeoIP Setup (Critical for Map)

### Download MaxMind GeoLite2 Database (Free)

```bash
# Sign up for free account at https://www.maxmind.com/en/geolite2/signup

# Install geoipupdate
sudo add-apt-repository ppa:maxmind/ppa
sudo apt update
sudo apt install geoipupdate

# Configure with your account
sudo nano /etc/GeoIP.conf

# Add your AccountID and LicenseKey
AccountID YOUR_ACCOUNT_ID
LicenseKey YOUR_LICENSE_KEY
EditionIDs GeoLite2-City GeoLite2-Country

# Download databases
sudo geoipupdate

# Databases will be at:
# /usr/share/GeoIP/GeoLite2-City.mmdb
# /usr/share/GeoIP/GeoLite2-Country.mmdb

# Install Python library
pip3 install geoip2
```

**Accuracy**: ~99% for country-level, ~80% for city-level

---

## Part 5: Web Server Implementation

### Minimal Flask Server

```python
#!/usr/bin/env python3
"""
VPN Monitoring Dashboard - Flask Server
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'CHANGE_THIS_SECRET_KEY'
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple user authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Hardcoded user (change this!)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('admin123'.encode()).hexdigest()

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            user = User(username)
            login_user(user)
            return jsonify({'success': True})

        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
@login_required
def get_stats():
    """Get current statistics"""
    conn = sqlite3.connect('vpn_connections.db')
    c = conn.cursor()

    # Active connections (last 30 seconds)
    c.execute('''
        SELECT COUNT(DISTINCT src_ip)
        FROM connections
        WHERE timestamp > datetime('now', '-30 seconds')
    ''')
    active_count = c.fetchone()[0]

    # Top countries
    c.execute('''
        SELECT country, COUNT(*) as count
        FROM connections
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_countries = [{'country': row[0], 'count': row[1]} for row in c.fetchall()]

    # Total data transferred (last hour)
    c.execute('''
        SELECT SUM(bytes_recv), SUM(bytes_sent)
        FROM connections
        WHERE timestamp > datetime('now', '-1 hour')
    ''')
    bytes_data = c.fetchone()

    conn.close()

    return jsonify({
        'active_connections': active_count,
        'top_countries': top_countries,
        'bytes_received': bytes_data[0] or 0,
        'bytes_sent': bytes_data[1] or 0
    })

@app.route('/api/map-data')
@login_required
def get_map_data():
    """Get data for map visualization"""
    conn = sqlite3.connect('vpn_connections.db')
    c = conn.cursor()

    # Get recent connections with geo data
    c.execute('''
        SELECT src_ip, country, city, latitude, longitude,
               COUNT(*) as connection_count
        FROM connections
        WHERE timestamp > datetime('now', '-5 minutes')
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
        GROUP BY src_ip, country, city, latitude, longitude
    ''')

    markers = []
    for row in c.fetchall():
        markers.append({
            'ip': row[0],
            'country': row[1],
            'city': row[2],
            'lat': row[3],
            'lon': row[4],
            'count': row[5]
        })

    conn.close()

    return jsonify({'markers': markers})

@app.route('/api/history')
@login_required
def get_history():
    """Get historical connection data"""
    hours = int(request.args.get('hours', 24))

    conn = sqlite3.connect('vpn_connections.db')
    c = conn.cursor()

    c.execute('''
        SELECT
            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
            COUNT(DISTINCT src_ip) as unique_ips,
            COUNT(*) as total_connections
        FROM connections
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        GROUP BY hour
        ORDER BY hour
    ''', (hours,))

    data = [{'hour': row[0], 'unique_ips': row[1], 'total': row[2]}
            for row in c.fetchall()]

    conn.close()

    return jsonify({'history': data})

# WebSocket for real-time updates
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'connected': True})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def emit_real_time_update():
    """Called by background task to push updates"""
    # This would be called by a background thread
    socketio.emit('update', {
        'timestamp': datetime.utcnow().isoformat(),
        'connections': get_stats()
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)
```

---

## Part 6: Frontend Implementation

### Key Components

1. **Login Screen** (templates/login.html)
2. **Dashboard** (templates/dashboard.html)
3. **Map Visualization** (Leaflet.js or Mapbox)
4. **Live Statistics** (Chart.js)
5. **Real-time Updates** (Socket.IO)

### Frontend Tech Stack

**Minimal**:
- Vanilla JavaScript
- Leaflet.js for maps (free, no API key)
- Chart.js for charts
- Socket.IO client for WebSocket
- Dark theme CSS

**Production**:
- React or Vue.js
- Mapbox GL JS (better visuals, requires API key)
- D3.js for advanced visualizations
- TailwindCSS for styling
- Recharts or Victory for charts

---

## Part 7: Deployment

### Quick Setup Script

```bash
#!/bin/bash
# deploy.sh - Quick deployment script

echo "Installing dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip iptables ipset conntrack geoipupdate

echo "Installing Python packages..."
pip3 install flask flask-socketio flask-login geoip2 eventlet

echo "Setting up GeoIP..."
# User needs to configure /etc/GeoIP.conf first
sudo geoipupdate

echo "Creating systemd service for collector..."
sudo cat > /etc/systemd/system/vpn-collector.service <<EOF
[Unit]
Description=VPN Connection Collector
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vpn-monitor
ExecStart=/usr/bin/python3 /opt/vpn-monitor/collector.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Creating systemd service for web dashboard..."
sudo cat > /etc/systemd/system/vpn-dashboard.service <<EOF
[Unit]
Description=VPN Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/vpn-monitor
ExecStart=/usr/bin/python3 /opt/vpn-monitor/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable vpn-collector vpn-dashboard
sudo systemctl start vpn-collector vpn-dashboard

echo "Setup complete!"
echo "Access dashboard at http://YOUR_SERVER_IP:8080"
echo "Default login: admin / admin123 (CHANGE THIS!)"
```

---

## Part 8: Production Considerations

### Security
- [ ] Use HTTPS (Let's Encrypt)
- [ ] Strong password/JWT auth
- [ ] Rate limiting
- [ ] Input validation
- [ ] CORS configuration
- [ ] Firewall rules (only expose port 443)

### Performance
- [ ] Database indexing
- [ ] Connection pooling
- [ ] Caching (Redis)
- [ ] Gzip compression
- [ ] CDN for static assets

### Monitoring
- [ ] Application logging
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Uptime monitoring

### Scaling
- [ ] Horizontal scaling (multiple workers)
- [ ] Load balancing
- [ ] Database replication
- [ ] Message queue for async processing

---

## Summary

**For Quick Start** (Minimal Architecture):
1. Use [iran_firewall_linux.py](iran_firewall_linux.py) for firewall
2. Use `ss` or `conntrack` for connection data
3. SQLite for storage
4. Flask + Socket.IO for web server
5. Leaflet.js for map

**For Production** (Scalable Architecture):
1. eBPF for data collection
2. Redis/RabbitMQ for messaging
3. TimescaleDB for time-series storage
4. FastAPI for high-performance API
5. React + Mapbox for rich UI

Both architectures give you:
- ✅ Real-time connection monitoring
- ✅ Geographic visualization on accurate maps
- ✅ Historical data and charts
- ✅ Login authentication
- ✅ Dark futuristic UI
- ✅ OS/network-layer data (no VPN logs needed)

Choose based on your scale and requirements!
