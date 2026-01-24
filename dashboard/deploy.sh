#!/bin/bash
# VPN Monitoring Dashboard - Deployment Script
# For Ubuntu/Debian Linux

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════╗"
echo "║    VPN MONITORING DASHBOARD - DEPLOYMENT SCRIPT          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script should be run as root (sudo)"
    echo "   Some steps may fail without root privileges"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Variables
INSTALL_DIR="/opt/vpn-monitor"
DB_PATH="$INSTALL_DIR/vpn_connections.db"
GEOIP_DIR="/usr/share/GeoIP"

echo "📦 Step 1: Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv \
    iptables ipset conntrack \
    geoipupdate

echo ""
echo "📁 Step 2: Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Copy files
echo "📋 Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp "$SCRIPT_DIR/collector.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/app.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/templates" "$INSTALL_DIR/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/static" "$INSTALL_DIR/" 2>/dev/null || true

echo ""
echo "🐍 Step 3: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "📚 Step 4: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "�� Step 5: Setting up GeoIP..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "You need a MaxMind account to download GeoIP databases."
echo "Sign up for FREE at: https://www.maxmind.com/en/geolite2/signup"
echo ""
read -p "Do you have a MaxMind account? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    read -p "Enter your MaxMind Account ID: " ACCOUNT_ID
    read -p "Enter your MaxMind License Key: " LICENSE_KEY

    # Configure GeoIP
    cat > /etc/GeoIP.conf <<EOF
# GeoIP Configuration
AccountID $ACCOUNT_ID
LicenseKey $LICENSE_KEY
EditionIDs GeoLite2-City GeoLite2-Country
DatabaseDirectory $GEOIP_DIR
EOF

    echo "📥 Downloading GeoIP databases..."
    mkdir -p "$GEOIP_DIR"
    geoipupdate

    echo "✅ GeoIP databases installed"
else
    echo "⚠️  Skipping GeoIP setup"
    echo "   Geographic features will be limited without GeoIP"
    echo "   You can configure it later in /etc/GeoIP.conf"
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
echo "📊 Step 9: Checking service status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl status vpn-collector --no-pager -l || true
echo ""
systemctl status vpn-dashboard --no-pager -l || true
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                 ✅ DEPLOYMENT COMPLETE!                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📌 Installation directory: $INSTALL_DIR"
echo "📌 Database: $DB_PATH"
echo ""
echo "🌐 Access the dashboard at:"
echo "   http://$(hostname -I | awk '{print $1}'):8080"
echo "   or"
echo "   http://localhost:8080"
echo ""
echo "🔐 Default credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "   1. Change the default password!"
echo "   2. Set environment variables for security:"
echo "      export ADMIN_USERNAME='your_username'"
echo "      export ADMIN_PASSWORD='your_password'"
echo "   3. Configure firewall to allow port 8080"
echo "   4. For production, use HTTPS with Nginx reverse proxy"
echo ""
echo "📝 Useful commands:"
echo "   • Check collector logs:  sudo journalctl -u vpn-collector -f"
echo "   • Check dashboard logs:  sudo journalctl -u vpn-dashboard -f"
echo "   • Restart collector:     sudo systemctl restart vpn-collector"
echo "   • Restart dashboard:     sudo systemctl restart vpn-dashboard"
echo "   • Stop services:         sudo systemctl stop vpn-collector vpn-dashboard"
echo ""
echo "✨ Enjoy your VPN monitoring dashboard!"
