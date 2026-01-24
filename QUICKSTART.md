# Quick Start Guide

Get your VPN monitoring dashboard running in 5 minutes!

## Prerequisites

Ubuntu 20.04+ or Debian 11+ server with:
- Python 3.8+
- Root/sudo access
- Active VPN running (Psiphon, OpenVPN, WireGuard, etc.)

## Installation

### Option 1: Dashboard Only (Recommended for most users)

```bash
# Navigate to dashboard directory
cd dashboard

# Run deployment (auto-elevates to sudo)
./deploy.sh

# Access dashboard
# Open browser to: http://YOUR_SERVER_IP:8080
# Login: admin / admin123
```

That's it! The deployment script will:
- Install all dependencies
- Set up the collector
- Start the web dashboard
- Create systemd services

### Option 2: Firewall + Dashboard (Maximum security)

```bash
# Step 1: Set up Iran-only firewall
./run_firewall.sh
# Follow menu to enable Iran-only mode

# Step 2: Deploy dashboard
cd dashboard
./deploy.sh

# Step 3: Access dashboard
# Open browser to: http://YOUR_SERVER_IP:8080
```

## First Login

1. Open browser to `http://YOUR_SERVER_IP:8080`
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. **Change the password immediately!**

## Change Default Password

```bash
# Method 1: Environment variables (recommended)
export ADMIN_USERNAME='your_username'
export ADMIN_PASSWORD='your_secure_password'
sudo systemctl restart vpn-dashboard

# Method 2: Edit systemd service
sudo nano /etc/systemd/system/vpn-dashboard.service
# Add these lines in [Service] section:
#   Environment="ADMIN_USERNAME=your_username"
#   Environment="ADMIN_PASSWORD=your_password"
sudo systemctl daemon-reload
sudo systemctl restart vpn-dashboard
```

## GeoIP Setup (Optional but Recommended)

For accurate geographic features:

1. Sign up for FREE at: https://www.maxmind.com/en/geolite2/signup
2. Get your Account ID and License Key
3. Configure:

```bash
sudo nano /etc/GeoIP.conf

# Add:
AccountID YOUR_ACCOUNT_ID
LicenseKey YOUR_LICENSE_KEY
EditionIDs GeoLite2-City GeoLite2-Country
DatabaseDirectory /usr/share/GeoIP

# Download databases
sudo geoipupdate

# Restart collector
sudo systemctl restart vpn-collector
```

## Verify Installation

```bash
# Check services are running
sudo systemctl status vpn-collector
sudo systemctl status vpn-dashboard

# View real-time logs
sudo journalctl -u vpn-collector -f
sudo journalctl -u vpn-dashboard -f

# Test collector manually
sudo python3 /opt/vpn-monitor/collector.py --interface tun0
```

## Common Issues

### Dashboard not accessible

```bash
# Check if service is running
sudo systemctl status vpn-dashboard

# Check if port is open
sudo ss -tlnp | grep 8080

# View error logs
sudo journalctl -u vpn-dashboard -n 50
```

### No connections showing

```bash
# Verify VPN interface
ip link show tun0

# Check if collector is working
sudo journalctl -u vpn-collector -f

# Manually test connection detection
sudo ss -tunap | grep tun0
```

### GeoIP not working

```bash
# Check database exists
ls -lh /usr/share/GeoIP/GeoLite2-City.mmdb

# Update database
sudo geoipupdate

# Restart collector
sudo systemctl restart vpn-collector
```

## Useful Commands

```bash
# View dashboard logs
sudo journalctl -u vpn-dashboard -f

# View collector logs
sudo journalctl -u vpn-collector -f

# Restart services
sudo systemctl restart vpn-dashboard
sudo systemctl restart vpn-collector

# Stop services
sudo systemctl stop vpn-dashboard vpn-collector

# Check database size
ls -lh /opt/vpn-monitor/vpn_connections.db
```

## Security Checklist

- [ ] Change default admin password
- [ ] Configure firewall to restrict dashboard access
- [ ] Set up HTTPS with Nginx (for production)
- [ ] Regularly update GeoIP databases
- [ ] Monitor logs for suspicious activity

## Next Steps

- Read [dashboard/README.md](dashboard/README.md) for full documentation
- Check [DASHBOARD_ARCHITECTURE.md](DASHBOARD_ARCHITECTURE.md) for architecture details
- Set up Nginx reverse proxy for HTTPS (production)
- Configure automated backups of the database

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#common-issues) section above
2. Review logs: `sudo journalctl -u vpn-dashboard -f`
3. Read the full documentation in [dashboard/README.md](dashboard/README.md)
4. Open an issue on GitHub with error logs

---

**Enjoy your VPN monitoring dashboard!** 🚀
