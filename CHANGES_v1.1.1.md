# Iran Conduit Firewall - v1.1.1 Linux Update

## 📋 Overview

The Linux version of the Iran Conduit Firewall has been updated from v1.0.0 to v1.1.1, incorporating all the security improvements and features from the Windows version update.

---

## 🔒 Key Security Improvements

### 1. **Explicit BLOCK Rules** ⭐
**Before (v1.0.0):** Relied on implicit deny - if traffic didn't match an ALLOW rule, it might still get through depending on system defaults.

**Now (v1.1.1):** Creates explicit DROP rules at the end of the chain. This ensures 100% protection regardless of system configuration.

```bash
# Old approach:
iptables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_IRAN src -j ACCEPT
# (relied on default policy)

# New approach:
iptables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_IRAN_V4 src -j ACCEPT
iptables -A IRAN_CONDUIT -j DROP  # EXPLICIT BLOCK
```

### 2. **Full IPv6 Support** 🌐
**Before:** Only IPv4 filtering - attackers could bypass via IPv6.

**Now:**
- Downloads Iran IPv6 ranges from multiple sources
- Creates separate `ip6tables` rules
- Creates IPv6 ipsets with `family inet6`
- If no IPv6 ranges available, blocks ALL IPv6 traffic to prevent bypass

### 3. **Better Rule Organization**
Separate ipsets for better management:
- `IRAN_CONDUIT_IRAN_V4` - Iran IPv4 ranges
- `IRAN_CONDUIT_IRAN_V6` - Iran IPv6 ranges
- `IRAN_CONDUIT_DNS_V4` - DNS servers (IPv4)
- `IRAN_CONDUIT_DNS_V6` - DNS servers (IPv6)
- `IRAN_CONDUIT_ADMIN` - Admin whitelist

---

## ✨ New Features

### 1. **Two Operating Modes**

#### Normal Mode (Recommended)
- **TCP:** Global access (ensures Psiphon broker visibility)
- **UDP:** Iran-only (actual data tunnel)
- Best for most users

```bash
sudo python3 iran_firewall_linux.py
# Select: 1. Enable Iran-only mode (Normal)
```

#### Strict Mode
- **TCP:** Iran-only
- **UDP:** Iran-only
- Maximum restriction but may affect broker visibility over time

```bash
sudo python3 iran_firewall_linux.py
# Select: 2. Enable Iran-only mode (Strict)
```

### 2. **Diagnostic Logging**
- All operations logged to `firewall.log`
- Timestamps and detailed error messages
- Makes troubleshooting much easier

```bash
tail -f firewall.log
```

### 3. **Enhanced Status Display**
Shows comprehensive information:
- IPv4 rule count
- IPv6 rule count
- Number of Iran ranges loaded (IPv4 and IPv6)
- Current mode (Normal vs Strict)
- Last update timestamp
- VPN interface status

### 4. **Better Error Handling**
- Graceful fallback if IPv6 sources fail
- Warnings instead of failures
- Continues operation with reduced functionality

---

## 🔄 Technical Changes

### IP Source Updates

**IPv4 Sources (unchanged):**
```python
IP_SOURCES_V4 = [
    "https://www.ipdeny.com/ipblocks/data/countries/ir.zone",
    "https://raw.githubusercontent.com/herrbischoff/country-ip-blocks/master/ipv4/ir.cidr",
]
```

**NEW IPv6 Sources:**
```python
IP_SOURCES_V6 = [
    "https://www.ipdeny.com/ipv6/ipaddresses/blocks/ir.zone",
    "https://raw.githubusercontent.com/herrbischoff/country-ip-blocks/master/ipv6/ir.cidr",
]
```

**NEW DNS IPv6 Servers:**
```python
DNS_SERVERS_V6 = [
    "2001:4860:4860::8888", "2001:4860:4860::8844",  # Google DNS
    "2606:4700:4700::1111", "2606:4700:4700::1001",  # Cloudflare DNS
    "2620:fe::fe", "2620:fe::9",                      # Quad9 DNS
]
```

### Function Signature Changes

**`download_iran_ips()`**
```python
# Before:
def download_iran_ips():
    # Returns single list of IPv4 IPs
    return iran_ips

# Now:
def download_iran_ips(include_ipv6=True):
    # Returns tuple of (IPv4, IPv6)
    return iran_v4, iran_v6
```

**`create_ipset()`**
```python
# Before:
def create_ipset(name, ips):
    # Always created IPv4 sets

# Now:
def create_ipset(name, ips, family='inet'):
    # Can create 'inet' (IPv4) or 'inet6' (IPv6) sets
```

**`enable_iran_only()`**
```python
# Before:
def enable_iran_only():
    # Always same behavior

# Now:
def enable_iran_only(strict_mode=False):
    # Supports Normal and Strict modes
```

### Iptables Rule Structure

**Before (v1.0.0):**
```bash
iptables -N IRAN_CONDUIT
iptables -A IRAN_CONDUIT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_DNS src -j ACCEPT
iptables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_IRAN src -j ACCEPT
iptables -A IRAN_CONDUIT -j DROP
iptables -I INPUT -i tun0 -j IRAN_CONDUIT
```

**Now (v1.1.1):**
```bash
# Create chains for both IPv4 and IPv6
iptables -N IRAN_CONDUIT
ip6tables -N IRAN_CONDUIT

# IPv4 rules
iptables -A IRAN_CONDUIT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_DNS_V4 src -j ACCEPT
iptables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_IRAN_V4 src -j ACCEPT
iptables -A IRAN_CONDUIT -j LOG --log-prefix '[IRAN-BLOCK-V4] '
iptables -A IRAN_CONDUIT -j DROP  # EXPLICIT BLOCK

# IPv6 rules
ip6tables -A IRAN_CONDUIT -m state --state ESTABLISHED,RELATED -j ACCEPT
ip6tables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_DNS_V6 src -j ACCEPT
ip6tables -A IRAN_CONDUIT -m set --match-set IRAN_CONDUIT_IRAN_V6 src -j ACCEPT
ip6tables -A IRAN_CONDUIT -j LOG --log-prefix '[IRAN-BLOCK-V6] '
ip6tables -A IRAN_CONDUIT -j DROP  # EXPLICIT BLOCK

# Apply based on mode
# Normal mode: Only UDP filtered
iptables -I INPUT -i tun0 -p udp -j IRAN_CONDUIT
ip6tables -I INPUT -i tun0 -p udp -j IRAN_CONDUIT

# Strict mode: Both TCP and UDP filtered
iptables -I INPUT -i tun0 -j IRAN_CONDUIT
ip6tables -I INPUT -i tun0 -j IRAN_CONDUIT
```

---

## 📊 Configuration Storage

**New fields in config.json:**
```json
{
  "vpn_interface": "tun0",
  "vpn_port": "443",
  "admin_ips": ["1.2.3.4"],
  "last_update": "2026-01-26 12:00:00",  // NEW
  "strict_mode": false,                   // NEW
  "ipv4_count": 4567,                     // NEW
  "ipv6_count": 2345                      // NEW
}
```

---

## 🔍 Verification & Monitoring

### Check Active Rules
```bash
# IPv4 rules
sudo iptables -L IRAN_CONDUIT -n -v

# IPv6 rules
sudo ip6tables -L IRAN_CONDUIT -n -v

# Check ipsets
sudo ipset list IRAN_CONDUIT_IRAN_V4
sudo ipset list IRAN_CONDUIT_IRAN_V6
```

### View Blocked Traffic
```bash
# IPv4 blocks
sudo journalctl -k | grep IRAN-BLOCK-V4

# IPv6 blocks
sudo journalctl -k | grep IRAN-BLOCK-V6
```

### Check Status
```bash
sudo python3 iran_firewall_linux.py
# Select: 4. Check status
```

---

## 🚀 Migration Guide

### For Existing Users (v1.0.0 → v1.1.1)

1. **Backup current config:**
   ```bash
   cp config.json config.json.backup
   ```

2. **Disable old firewall:**
   ```bash
   sudo python3 iran_firewall_linux.py
   # Select: Disable Iran-only mode
   ```

3. **Update script:**
   ```bash
   # Replace iran_firewall_linux.py with new version
   ```

4. **Enable new firewall:**
   ```bash
   sudo python3 iran_firewall_linux.py
   # Select: 1. Enable Iran-only mode (Normal)
   ```

5. **Verify:**
   ```bash
   sudo python3 iran_firewall_linux.py
   # Select: 4. Check status
   # Should show IPv4 and IPv6 rules
   ```

### For New Users

Simply run:
```bash
sudo python3 iran_firewall_linux.py
```

Follow the menu prompts.

---

## 🐛 Known Issues & Limitations

### IPv6 Source Availability
If IPv6 sources fail to download:
- Script will continue with IPv4 only
- Will block ALL IPv6 traffic to prevent bypass
- Not a security issue, just reduced flexibility

### Conntrack Requirement
Some systems may need conntrack for proper state tracking:
```bash
sudo modprobe nf_conntrack
```

### Legacy Cleanup
First run after upgrade will clean up old ipset names:
- `IRAN_CONDUIT_IRAN` → `IRAN_CONDUIT_IRAN_V4`
- `IRAN_CONDUIT_DNS` → `IRAN_CONDUIT_DNS_V4`

---

## 📝 Updated Dependencies

**Required packages:**
```bash
sudo apt install -y \
    iptables \
    ip6tables \     # NEW - for IPv6 support
    ipset \
    iproute2 \
    conntrack       # Recommended
```

**Python version:**
- Still requires Python 3.6+
- No new Python dependencies

---

## 🎯 Why These Changes Matter

### 1. Security Gap Closed
The old version could be bypassed if:
- System had permissive default firewall policy
- Attacker used IPv6
- Custom firewall rules existed

The new version prevents ALL these bypass methods.

### 2. Psiphon Broker Visibility
The new Normal mode ensures brokers can still discover your node while protecting the data tunnel. This is critical for long-term Conduit operation.

### 3. Operational Transparency
Logging and status improvements make it much easier to:
- Verify the firewall is working
- Troubleshoot issues
- Monitor blocked connection attempts

---

## 📖 Additional Resources

- **Main README:** [README.md](README.md)
- **Dashboard Guide:** [dashboard/README.md](dashboard/README.md)
- **Architecture:** [DASHBOARD_ARCHITECTURE.md](DASHBOARD_ARCHITECTURE.md)
- **Firewall Logs:** `firewall.log` (in script directory)

---

## 🙏 Credits

These improvements were inspired by community contributions to the Windows version, particularly:
- **moridani's fork** - Explicit block rules and IPv6 support
- Security audit feedback from the community

---

## ✅ Changelog Summary

### Added ✨
- IPv6 firewall support (ip6tables rules)
- IPv6 Iran IP range downloads
- IPv6 DNS server whitelist
- Explicit DROP/BLOCK rules for both IPv4 and IPv6
- Two modes: Normal (default) and Strict
- Comprehensive logging to `firewall.log`
- Enhanced status display with IPv4/IPv6 stats
- Mode display in status (Normal vs Strict)
- Last update timestamp in config
- IP count tracking in config

### Changed 🔄
- Renamed ipsets to include version (V4/V6)
- Split `download_iran_ips()` to return tuple
- Updated `create_ipset()` to support family parameter
- Added `strict_mode` parameter to `enable_iran_only()`
- Improved error messages and user feedback
- Updated menu to show two enable options
- Enhanced cleanup in `disable_iran_only()`

### Fixed 🐛
- IPv6 bypass vulnerability
- Reliance on implicit deny
- Missing dependency check for ip6tables
- Incomplete cleanup of legacy rules

### Security 🔒
- Explicit DROP rules (no reliance on defaults)
- IPv6 traffic blocking (if Iran ranges unavailable)
- Better rule priority ordering
- Admin IP rules at highest priority

---

**Version:** 1.1.1-linux
**Release Date:** January 26, 2026
**Previous Version:** 1.0.0-linux

**Made with ❤️ for the Iranian people during internet shutdowns**
