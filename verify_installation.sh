#!/bin/bash
# Verification script for VPN Monitoring Dashboard

echo "========================================="
echo "   VPN Monitor - Installation Check"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
}

ERRORS=0
WARNINGS=0

# Check Python
echo "Checking Python..."
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2)
    check_pass "Python 3 installed: $VERSION"
else
    check_fail "Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check system dependencies
echo ""
echo "Checking system dependencies..."
for cmd in iptables ipset ss; do
    if command -v $cmd &> /dev/null; then
        check_pass "$cmd installed"
    else
        check_fail "$cmd not found"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check conntrack (optional)
if command -v conntrack &> /dev/null; then
    check_pass "conntrack installed"
else
    check_warn "conntrack not found (optional, but recommended)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check GeoIP
echo ""
echo "Checking GeoIP..."
if [ -f "/usr/share/GeoIP/GeoLite2-City.mmdb" ]; then
    check_pass "GeoIP database found"
else
    check_warn "GeoIP database not found (geographic features will be limited)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check if dashboard is installed
echo ""
echo "Checking dashboard installation..."
if [ -d "/opt/vpn-monitor" ]; then
    check_pass "Dashboard installed at /opt/vpn-monitor"

    # Check files
    for file in collector.py app.py requirements.txt; do
        if [ -f "/opt/vpn-monitor/$file" ]; then
            check_pass "$file exists"
        else
            check_fail "$file missing"
            ERRORS=$((ERRORS + 1))
        fi
    done

    # Check virtual environment
    if [ -d "/opt/vpn-monitor/venv" ]; then
        check_pass "Python virtual environment created"
    else
        check_warn "Virtual environment not found"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    check_warn "Dashboard not installed (run: cd dashboard && ./deploy.sh)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check systemd services
echo ""
echo "Checking systemd services..."
for service in vpn-collector vpn-dashboard; do
    if systemctl list-unit-files | grep -q "$service.service"; then
        check_pass "$service.service exists"

        if systemctl is-active --quiet $service; then
            check_pass "$service is running"
        else
            check_fail "$service is not running"
            ERRORS=$((ERRORS + 1))
        fi
    else
        check_warn "$service.service not found"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check if port 8080 is listening
echo ""
echo "Checking network..."
if ss -tlnp | grep -q ":8080"; then
    check_pass "Dashboard listening on port 8080"
else
    check_fail "Port 8080 not listening"
    ERRORS=$((ERRORS + 1))
fi

# Check database
echo ""
echo "Checking database..."
if [ -f "/opt/vpn-monitor/vpn_connections.db" ]; then
    SIZE=$(du -h /opt/vpn-monitor/vpn_connections.db | cut -f1)
    check_pass "Database exists (size: $SIZE)"

    # Check if database has data
    COUNT=$(sqlite3 /opt/vpn-monitor/vpn_connections.db "SELECT COUNT(*) FROM connections" 2>/dev/null || echo "0")
    if [ "$COUNT" -gt 0 ]; then
        check_pass "Database has data ($COUNT records)"
    else
        check_warn "Database is empty (collector may not be working)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    check_warn "Database not found yet (will be created when collector starts)"
    WARNINGS=$((WARNINGS + 1))
fi

# Check VPN interface
echo ""
echo "Checking VPN interface..."
if ip link show tun0 &> /dev/null; then
    check_pass "tun0 interface found"
elif ip link show wg0 &> /dev/null; then
    check_pass "wg0 interface found"
else
    check_warn "No VPN interface found (tun0, wg0)"
    check_warn "Make sure your VPN is running"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "========================================="
echo "           Verification Summary"
echo "========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your VPN monitoring dashboard is ready!"
    echo "Access it at: http://$(hostname -I | awk '{print $1}'):8080"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}! $WARNINGS warning(s) found${NC}"
    echo ""
    echo "Dashboard should work, but some features may be limited"
    echo "Access it at: http://$(hostname -I | awk '{print $1}'):8080"
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}! $WARNINGS warning(s) found${NC}"
    fi
    echo ""
    echo "Please fix the errors above before using the dashboard"
    echo ""
    echo "Common fixes:"
    echo "  - Install dependencies: sudo apt install python3 iptables ipset conntrack"
    echo "  - Deploy dashboard: cd dashboard && ./deploy.sh"
    echo "  - Start services: sudo systemctl start vpn-collector vpn-dashboard"
fi

echo ""
echo "For detailed logs, run:"
echo "  sudo journalctl -u vpn-collector -f"
echo "  sudo journalctl -u vpn-dashboard -f"
echo ""
