#!/bin/bash
# VPN Monitoring Dashboard - Deployment Script
# For Ubuntu/Debian Linux

echo "╔══════════════════════════════════════════════════════════╗"
echo "║    VPN MONITORING DASHBOARD - DEPLOYMENT SCRIPT          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "🔐 This script requires root privileges"
    echo "   Re-running with sudo..."
    echo ""
    exec sudo -E bash "$0" "$@"
fi

echo "✅ Running with root privileges"
echo ""

# Variables
INSTALL_DIR="/opt/vpn-monitor"
DB_PATH="$INSTALL_DIR/vpn_connections.db"
GEOIP_DIR="/usr/share/GeoIP"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Verify required files exist
echo "🔍 Checking for required files..."
MISSING_FILES=0

for file in "collector.py" "app.py" "requirements.txt"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        echo "   ❌ Missing: $file"
        MISSING_FILES=1
    else
        echo "   ✓ Found: $file"
    fi
done

if [ ! -d "$SCRIPT_DIR/templates" ]; then
    echo "   ❌ Missing: templates/ directory"
    MISSING_FILES=1
else
    echo "   ✓ Found: templates/"
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo ""
    echo "❌ ERROR: Missing required files!"
    echo "   Make sure you're running this script from the dashboard directory"
    echo "   Current directory: $SCRIPT_DIR"
    exit 1
fi

echo ""

echo "📦 Step 1: Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv \
    iptables ipset conntrack \
    geoipupdate

echo ""
echo "📁 Step 2: Preparing installation directory..."
# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy files to installation directory
echo "📋 Copying application files..."
if [ -f "$SCRIPT_DIR/collector.py" ]; then
    cp "$SCRIPT_DIR/collector.py" "$INSTALL_DIR/"
    echo "   ✓ collector.py"
else
    echo "   ⚠️  collector.py not found in $SCRIPT_DIR"
fi

if [ -f "$SCRIPT_DIR/app.py" ]; then
    cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/"
    echo "   ✓ app.py"
else
    echo "   ⚠️  app.py not found in $SCRIPT_DIR"
fi

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
    echo "   ✓ requirements.txt"
else
    echo "   ⚠️  requirements.txt not found in $SCRIPT_DIR"
fi

if [ -d "$SCRIPT_DIR/templates" ]; then
    cp -r "$SCRIPT_DIR/templates" "$INSTALL_DIR/"
    echo "   ✓ templates/"
else
    echo "   ⚠️  templates/ directory not found in $SCRIPT_DIR"
fi

if [ -d "$SCRIPT_DIR/static" ]; then
    cp -r "$SCRIPT_DIR/static" "$INSTALL_DIR/"
    echo "   ✓ static/"
fi

# Change to installation directory
cd "$INSTALL_DIR"

echo ""
echo "🐍 Step 3: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "📚 Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Step 5: GeoIP Setup (Optional)"
echo "========================================="
echo "Geographic features require MaxMind GeoIP databases (FREE)"
echo ""

# Check if GeoIP database already exists
if [ -f "$GEOIP_DIR/GeoLite2-City.mmdb" ]; then
    echo "   GeoIP database already exists - skipping"
else
    echo "To enable geographic features:"
    echo "  1. Sign up at: https://www.maxmind.com/en/geolite2/signup"
    echo "  2. Edit /etc/GeoIP.conf with your credentials"
    echo "  3. Run: sudo geoipupdate"
    echo ""
    read -p "Do you want to configure GeoIP now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        read -p "MaxMind Account ID: " ACCOUNT_ID
        read -p "MaxMind License Key: " LICENSE_KEY

        if [ -n "$ACCOUNT_ID" ] && [ -n "$LICENSE_KEY" ]; then
            cat > /etc/GeoIP.conf <<EOF
# GeoIP Configuration
AccountID $ACCOUNT_ID
LicenseKey $LICENSE_KEY
EditionIDs GeoLite2-City GeoLite2-Country
DatabaseDirectory $GEOIP_DIR
EOF
            echo "Downloading GeoIP databases..."
            mkdir -p "$GEOIP_DIR"
            if geoipupdate; then
                echo "   GeoIP databases installed successfully"
            else
                echo "   Warning: GeoIP download failed"
            fi
        else
            echo "   Skipping GeoIP (credentials not provided)"
        fi
    else
        echo "   Skipping GeoIP setup (you can configure it later)"
    fi
fi

echo ""
echo "🔧 Step 6: Creating systemd service for collector..."
cat > /etc/systemd/system/vpn-collector.service <<EOF
[Unit]
Description=VPN Connection Collector
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/collector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🔧 Step 7: Creating systemd service for dashboard..."
cat > /etc/systemd/system/vpn-dashboard.service <<EOF
[Unit]
Description=VPN Monitoring Dashboard
After=network.target vpn-collector.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="SECRET_KEY=$(openssl rand -hex 32)"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/app.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🔄 Step 8: Enabling and starting services..."
systemctl daemon-reload
systemctl enable vpn-collector vpn-dashboard
systemctl start vpn-collector vpn-dashboard

echo ""
echo "⏳ Waiting for services to start..."
sleep 3

echo ""
echo "Step 9: Verifying services..."
echo "========================================="
if systemctl is-active --quiet vpn-collector; then
    echo "   Collector:  RUNNING"
else
    echo "   Collector:  FAILED (check logs: journalctl -u vpn-collector)"
fi

if systemctl is-active --quiet vpn-dashboard; then
    echo "   Dashboard:  RUNNING"
else
    echo "   Dashboard:  FAILED (check logs: journalctl -u vpn-dashboard)"
fi

echo ""
echo "========================================="
echo "        DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "Access the dashboard:"
echo "   http://$(hostname -I | awk '{print $1}'):8080"
echo "   http://localhost:8080"
echo ""
echo "Login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "IMPORTANT: Change the default password!"
echo "   export ADMIN_USERNAME='your_username'"
echo "   export ADMIN_PASSWORD='your_password'"
echo "   sudo systemctl restart vpn-dashboard"
echo ""
echo "Useful commands:"
echo "   View logs:     sudo journalctl -u vpn-dashboard -f"
echo "   Restart:       sudo systemctl restart vpn-dashboard"
echo "   Stop:          sudo systemctl stop vpn-dashboard"
echo ""
