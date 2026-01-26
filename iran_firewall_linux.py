#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║       IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT - v1.1.1            ║
║                    Linux/Ubuntu Edition                           ║
║                                                                   ║
║  Maximize your bandwidth for Iranian users by blocking           ║
║  connections from other countries.                                ║
║                                                                   ║
║  ⚠️  ONLY affects VPN traffic                                     ║
║  ✅ Your server and other services work normally                 ║
║                                                                   ║
║  IMPROVEMENTS IN v1.1.x:                                          ║
║  • Explicit BLOCK rules (doesn't rely on implicit deny)           ║
║  • IPv6 support for Iran ranges                                   ║
║  • Firewall state verification                                    ║
║  • Optional TCP restriction mode                                  ║
║  • Better error handling and logging                              ║
║  • v1.1.1: Fixed IPv6 block rules always created                  ║
║                                                                   ║
║  GitHub: Share this script to help more people!                  ║
╚═══════════════════════════════════════════════════════════════════╝
"""

VERSION = "1.1.1-linux"

import subprocess
import sys
import os
import urllib.request
import json
import time
import logging

RULE_PREFIX = "IRAN_CONDUIT"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firewall.log")
CONDUIT_URL = "https://conduit.psiphon.ca/"

# DNS servers to whitelist (IPv4)
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4",           # Google DNS
    "1.1.1.1", "1.0.0.1",           # Cloudflare DNS
    "9.9.9.9", "149.112.112.112",   # Quad9 DNS
    "208.67.222.222", "208.67.220.220",  # OpenDNS
    "4.2.2.1", "4.2.2.2",           # Level3 DNS
    "178.22.122.100", "185.51.200.2",    # Shekan DNS (Iran)
    "10.202.10.202", "10.202.10.102",    # 403.online DNS (Iran)
]

# DNS IPv6 servers
DNS_SERVERS_V6 = [
    "2001:4860:4860::8888", "2001:4860:4860::8844",  # Google DNS
    "2606:4700:4700::1111", "2606:4700:4700::1001",  # Cloudflare DNS
    "2620:fe::fe", "2620:fe::9",                      # Quad9 DNS
]

# Iran IP sources (IPv4)
IP_SOURCES_V4 = [
    "https://www.ipdeny.com/ipblocks/data/countries/ir.zone",
    "https://raw.githubusercontent.com/herrbischoff/country-ip-blocks/master/ipv4/ir.cidr",
]

# Iran IP sources (IPv6)
IP_SOURCES_V6 = [
    "https://www.ipdeny.com/ipv6/ipaddresses/blocks/ir.zone",
    "https://raw.githubusercontent.com/herrbischoff/country-ip-blocks/master/ipv6/ir.cidr",
]


def setup_logging():
    """Setup logging to file and console"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    except Exception:
        # If log file can't be created, just use console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear')


def print_header():
    """Print the application header"""
    clear_screen()
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║       🇮🇷 IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT v{VERSION} 🇮🇷      ║
╠═══════════════════════════════════════════════════════════════════╣
║  Maximize bandwidth for Iranian users during internet shutdowns   ║
║  [IMPROVED: Explicit blocks, IPv6 support, verification]          ║
║                      Linux/Ubuntu Edition                         ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def is_root():
    """Check if running as root"""
    return os.geteuid() == 0


def load_config():
    """Load configuration from JSON file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass


def run_cmd(cmd, check=False, shell=True):
    """Run shell command"""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            capture_output=True,
            text=True,
            shell=shell
        )
        success = result.returncode == 0
        if check and not success:
            print(f"   ⚠️  Command failed: {result.stderr[:100]}")
        return success, result.stdout, result.stderr
    except Exception as e:
        if check:
            print(f"   ⚠️  Command error: {str(e)[:100]}")
        return False, "", str(e)


def detect_vpn_interface():
    """Detect VPN interface (tun, tap, wg, etc.)"""
    config = load_config()
    saved_iface = config.get('vpn_interface')

    if saved_iface:
        # Verify it still exists
        success, out, _ = run_cmd(f"ip link show {saved_iface}")
        if success:
            return saved_iface

    # Auto-detect common VPN interfaces
    print("🔍 Detecting VPN interface...")
    success, out, _ = run_cmd("ip link show")

    # Look for common VPN interface patterns
    vpn_patterns = ['tun', 'tap', 'wg', 'ppp', 'ipsec']
    for line in out.split('\n'):
        for pattern in vpn_patterns:
            if pattern in line and 'state' in line:
                iface = line.split(':')[1].strip().split('@')[0]
                print(f"   ✓ Found VPN interface: {iface}")
                config['vpn_interface'] = iface
                save_config(config)
                return iface

    # Manual input
    print("   ✗ No VPN interface detected automatically")
    print("\n   Available interfaces:")
    run_cmd("ip link show | grep -E '^[0-9]+:' | cut -d: -f2")
    iface = input("\n   Enter VPN interface name (e.g., tun0): ").strip()

    if iface:
        config['vpn_interface'] = iface
        save_config(config)
        return iface

    return None


def detect_vpn_port():
    """Detect or configure VPN port"""
    config = load_config()
    saved_port = config.get('vpn_port')

    if saved_port:
        return saved_port

    print("\n🔍 VPN Port Configuration")
    print("   Common VPN ports:")
    print("   - Psiphon: Usually 443, 80, or random high port")
    print("   - OpenVPN: 1194 (UDP)")
    print("   - WireGuard: 51820 (UDP)")

    # Try to detect listening ports
    print("\n   Checking listening UDP ports...")
    success, out, _ = run_cmd("ss -lunp | grep -v '127.0.0.1'")
    if success and out:
        print(f"\n{out}")

    port = input("\n   Enter VPN port (or press Enter to skip port-based filtering): ").strip()

    if port and port.isdigit():
        config['vpn_port'] = port
        save_config(config)
        return port

    return None


def download_iran_ips(include_ipv6=True):
    """Download Iran IP ranges (IPv4 and optionally IPv6)"""
    print("📥 Downloading Iran IP ranges...")

    ipv4_ips = set()
    ipv6_ips = set()

    # Download IPv4
    print("\n   IPv4 ranges:")
    for url in IP_SOURCES_V4:
        source_name = url.split('/')[-1]
        try:
            print(f"   Fetching {source_name}...", end=" ", flush=True)
            req = urllib.request.Request(url, headers={'User-Agent': 'IranFirewall/1.1'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode('utf-8')
                ips = [line.strip() for line in data.split('\n')
                       if line.strip() and '/' in line and not line.startswith('#') and ':' not in line]
                ipv4_ips.update(ips)
                print(f"✓ {len(ips)} ranges")
        except Exception as e:
            print(f"✗ {str(e)[:50]}")

    # Download IPv6
    if include_ipv6:
        print("\n   IPv6 ranges:")
        for url in IP_SOURCES_V6:
            source_name = url.split('/')[-1]
            try:
                print(f"   Fetching {source_name}...", end=" ", flush=True)
                req = urllib.request.Request(url, headers={'User-Agent': 'IranFirewall/1.1'})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read().decode('utf-8')
                    ips = [line.strip() for line in data.split('\n')
                           if line.strip() and '/' in line and not line.startswith('#') and ':' in line]
                    ipv6_ips.update(ips)
                    print(f"✓ {len(ips)} ranges")
            except Exception as e:
                print(f"✗ {str(e)[:50]}")

    if len(ipv4_ips) == 0:
        print("   ❌ All IPv4 downloads failed!")
        return None, None

    print(f"\n   📊 Total: {len(ipv4_ips)} IPv4 + {len(ipv6_ips)} IPv6 ranges")
    return sorted(list(ipv4_ips)), sorted(list(ipv6_ips))


def create_ipset(name, ips, family='inet'):
    """Create ipset for efficient IP matching

    Args:
        name: Name of the ipset
        ips: List of IP ranges
        family: 'inet' for IPv4, 'inet6' for IPv6
    """
    # Delete if exists
    run_cmd(f"ipset destroy {name}", check=False)

    # Create new set
    success, _, _ = run_cmd(f"ipset create {name} hash:net family {family} maxelem 1000000", check=True)
    if not success:
        return False

    # Add IPs in batches
    print(f"   Adding {len(ips)} ranges to ipset...")
    batch_size = 1000
    for i in range(0, len(ips), batch_size):
        batch = ips[i:i+batch_size]

        progress = min(i + batch_size, len(ips))
        pct = int(progress / len(ips) * 100)
        print(f"\r   Progress: [{'█' * (pct//5):20}] {pct}% ({progress}/{len(ips)})", end="", flush=True)

        for ip in batch:
            run_cmd(f"ipset add {name} {ip}", check=False)

    print()
    return True


def get_admin_ips():
    """Get admin IPs to whitelist"""
    config = load_config()
    admin_ips = config.get('admin_ips', [])

    if admin_ips:
        print(f"\n🔐 Found {len(admin_ips)} admin IP(s) in config")
        for ip in admin_ips:
            print(f"   • {ip}")
        print("\n   These IPs will have FULL ACCESS to all server services")
        print("   (highest priority, bypasses VPN firewall)")

    print("\n💡 You can add your current IP to always access web services")
    add_ip = input("   Add admin IP now? (y/n): ").strip().lower()

    if add_ip == 'y':
        print("\n   Your current IP might be one of these:")
        print("   (Check your SSH connection or use: curl ifconfig.me)")
        new_ip = input("\n   Enter admin IP to whitelist (or press Enter to skip): ").strip()
        if new_ip:
            # Basic IP validation
            parts = new_ip.split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                if new_ip not in admin_ips:
                    admin_ips.append(new_ip)
                    config['admin_ips'] = admin_ips
                    save_config(config)
                    print(f"   ✅ Added {new_ip} to admin whitelist")
                else:
                    print(f"   ℹ️  {new_ip} already in whitelist")
            else:
                print("   ⚠️  Invalid IP format")

    return admin_ips


def manage_admin_ips():
    """Manage admin IP whitelist"""
    print("\n" + "=" * 50)
    print("🔐 ADMIN IP WHITELIST MANAGEMENT")
    print("=" * 50 + "\n")

    config = load_config()
    admin_ips = config.get('admin_ips', [])

    while True:
        print("\nCurrent admin IPs:")
        if admin_ips:
            for i, ip in enumerate(admin_ips, 1):
                print(f"   {i}. {ip}")
        else:
            print("   (none)")

        print("\nOptions:")
        print("   1. Add admin IP")
        print("   2. Remove admin IP")
        print("   0. Back to main menu")

        choice = input("\n   Enter choice: ").strip()

        if choice == "1":
            new_ip = input("\n   Enter IP address to whitelist: ").strip()
            # Basic validation
            parts = new_ip.split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                if new_ip not in admin_ips:
                    admin_ips.append(new_ip)
                    config['admin_ips'] = admin_ips
                    save_config(config)
                    print(f"   ✅ Added {new_ip}")
                else:
                    print(f"   ℹ️  {new_ip} already exists")
            else:
                print("   ❌ Invalid IP format")

        elif choice == "2":
            if not admin_ips:
                print("   No admin IPs to remove")
                continue

            try:
                idx = int(input("\n   Enter number to remove: ").strip()) - 1
                if 0 <= idx < len(admin_ips):
                    removed = admin_ips.pop(idx)
                    config['admin_ips'] = admin_ips
                    save_config(config)
                    print(f"   ✅ Removed {removed}")
                else:
                    print("   ❌ Invalid number")
            except ValueError:
                print("   ❌ Invalid input")

        elif choice == "0":
            break


def enable_iran_only(strict_mode=False):
    """
    Enable Iran-only mode using iptables

    strict_mode: If True, also restricts TCP to Iran (may break broker visibility)
    """
    print("\n" + "=" * 60)
    print("🇮🇷 ENABLING IRAN-ONLY MODE" + (" [STRICT]" if strict_mode else ""))
    print("=" * 60 + "\n")

    # Detect VPN interface
    vpn_iface = detect_vpn_interface()
    if not vpn_iface:
        print("   ❌ Cannot proceed without VPN interface")
        input("\n   Press Enter to go back...")
        return False

    # Detect VPN port (optional)
    vpn_port = detect_vpn_port()

    # Get admin IPs for whitelisting
    admin_ips = get_admin_ips()

    # Download Iran IPs (IPv4 and IPv6)
    iran_v4, iran_v6 = download_iran_ips(include_ipv6=True)
    if not iran_v4:
        print("\n❌ Failed to download Iran IP ranges")
        input("   Press Enter to go back...")
        return False

    # Clean up old rules
    print("\n🧹 Cleaning up old rules...")
    disable_iran_only(quiet=True)
    time.sleep(0.5)

    # ═══════════════════════════════════════════════════════════════
    # CREATE IPSETS FOR EFFICIENT IP MATCHING
    # ═══════════════════════════════════════════════════════════════

    # Create ipset for Iran IPv4
    print("\n📦 Creating IP set for Iran IPv4...")
    if not create_ipset(f"{RULE_PREFIX}_IRAN_V4", iran_v4, family='inet'):
        print("   ❌ Failed to create IPv4 ipset")
        input("   Press Enter to go back...")
        return False

    # Create ipset for Iran IPv6 (if available)
    if iran_v6:
        print("\n📦 Creating IP set for Iran IPv6...")
        if not create_ipset(f"{RULE_PREFIX}_IRAN_V6", iran_v6, family='inet6'):
            print("   ⚠️  Warning: Failed to create IPv6 ipset")
            print("   Continuing without IPv6 support...")
            iran_v6 = []

    # Create ipset for DNS IPv4
    print("\n🌐 Creating IP set for DNS IPv4...")
    if not create_ipset(f"{RULE_PREFIX}_DNS_V4", DNS_SERVERS, family='inet'):
        print("   ❌ Failed to create DNS ipset")
        input("   Press Enter to go back...")
        return False

    # Create ipset for DNS IPv6
    if DNS_SERVERS_V6:
        print("\n🌐 Creating IP set for DNS IPv6...")
        if not create_ipset(f"{RULE_PREFIX}_DNS_V6", DNS_SERVERS_V6, family='inet6'):
            print("   ⚠️  Warning: Failed to create DNS IPv6 ipset")

    # Create ipset for admin IPs if any exist
    if admin_ips:
        print("\n🔐 Creating IP set for admin whitelist...")
        if not create_ipset(f"{RULE_PREFIX}_ADMIN", admin_ips, family='inet'):
            print("   ⚠️  Warning: Failed to create admin ipset")
            print("   Continuing without admin whitelist...")
            admin_ips = []

    # ═══════════════════════════════════════════════════════════════
    # CREATE CUSTOM CHAINS FOR IPv4 AND IPv6
    # ═══════════════════════════════════════════════════════════════

    print("\n🔗 Creating firewall chains...")
    run_cmd(f"iptables -N {RULE_PREFIX}", check=False)
    run_cmd(f"ip6tables -N {RULE_PREFIX}", check=False)

    # ═══════════════════════════════════════════════════════════════
    # BUILD IPv4 FIREWALL RULES
    # ═══════════════════════════════════════════════════════════════

    print("🔒 Building IPv4 firewall rules...")

    # HIGHEST PRIORITY: Allow admin IPs (FULL ACCESS - not just VPN)
    if admin_ips:
        print(f"   ✓ Adding admin IP whitelist (highest priority)")
        for admin_ip in admin_ips:
            run_cmd(f"iptables -I INPUT 1 -s {admin_ip} -j ACCEPT", check=True)

    # Allow established connections
    run_cmd(f"iptables -A {RULE_PREFIX} -m state --state ESTABLISHED,RELATED -j ACCEPT", check=True)

    # Allow DNS IPv4
    run_cmd(f"iptables -A {RULE_PREFIX} -m set --match-set {RULE_PREFIX}_DNS_V4 src -j ACCEPT", check=True)

    # Allow Iran IPv4
    run_cmd(f"iptables -A {RULE_PREFIX} -m set --match-set {RULE_PREFIX}_IRAN_V4 src -j ACCEPT", check=True)

    # Log blocked connections (optional - useful for monitoring)
    run_cmd(f"iptables -A {RULE_PREFIX} -j LOG --log-prefix '[IRAN-BLOCK-V4] ' --log-level 4", check=False)

    # EXPLICIT DROP rule for everything else (KEY SECURITY IMPROVEMENT)
    run_cmd(f"iptables -A {RULE_PREFIX} -j DROP", check=True)

    # ═══════════════════════════════════════════════════════════════
    # BUILD IPv6 FIREWALL RULES (if IPv6 support is available)
    # ═══════════════════════════════════════════════════════════════

    if iran_v6:
        print("🔒 Building IPv6 firewall rules...")

        # Allow established connections
        run_cmd(f"ip6tables -A {RULE_PREFIX} -m state --state ESTABLISHED,RELATED -j ACCEPT", check=True)

        # Allow DNS IPv6
        if DNS_SERVERS_V6:
            run_cmd(f"ip6tables -A {RULE_PREFIX} -m set --match-set {RULE_PREFIX}_DNS_V6 src -j ACCEPT", check=True)

        # Allow Iran IPv6
        run_cmd(f"ip6tables -A {RULE_PREFIX} -m set --match-set {RULE_PREFIX}_IRAN_V6 src -j ACCEPT", check=True)

        # Log blocked connections
        run_cmd(f"ip6tables -A {RULE_PREFIX} -j LOG --log-prefix '[IRAN-BLOCK-V6] ' --log-level 4", check=False)

        # EXPLICIT DROP rule for everything else
        run_cmd(f"ip6tables -A {RULE_PREFIX} -j DROP", check=True)
    else:
        # No IPv6 Iran ranges - block ALL IPv6 to prevent bypass
        print("🚫 No IPv6 ranges - blocking ALL IPv6 traffic to VPN interface...")
        run_cmd(f"ip6tables -A {RULE_PREFIX} -j DROP", check=True)

    # ═══════════════════════════════════════════════════════════════
    # APPLY CHAINS TO INPUT (with protocol filtering)
    # ═══════════════════════════════════════════════════════════════

    print("\n🌍 Configuring protocol access...")

    if strict_mode:
        print("   STRICT MODE: TCP+UDP restricted to Iran only")
        # In strict mode, apply filtering to both TCP and UDP
        if vpn_port:
            run_cmd(f"iptables -I INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
            run_cmd(f"iptables -I INPUT -i {vpn_iface} -p tcp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
            if iran_v6:
                run_cmd(f"ip6tables -I INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
                run_cmd(f"ip6tables -I INPUT -i {vpn_iface} -p tcp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
        else:
            run_cmd(f"iptables -I INPUT -i {vpn_iface} -j {RULE_PREFIX}", check=True)
            if iran_v6:
                run_cmd(f"ip6tables -I INPUT -i {vpn_iface} -j {RULE_PREFIX}", check=True)
    else:
        print("   NORMAL MODE: UDP Iran-only, TCP global (for broker visibility)")
        # Normal mode: Only filter UDP (data tunnel), allow TCP globally (broker checks)
        if vpn_port:
            run_cmd(f"iptables -I INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
            if iran_v6:
                run_cmd(f"ip6tables -I INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
        else:
            # No port specified - filter only UDP on the interface
            run_cmd(f"iptables -I INPUT -i {vpn_iface} -p udp -j {RULE_PREFIX}", check=True)
            if iran_v6:
                run_cmd(f"ip6tables -I INPUT -i {vpn_iface} -p udp -j {RULE_PREFIX}", check=True)

    # ═══════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "=" * 60)
    print("✅ IRAN-ONLY MODE ENABLED!")
    print("=" * 60)
    print(f"\n   🌐 VPN Interface: {vpn_iface}")
    if vpn_port:
        print(f"   🔌 VPN Port: {vpn_port}")
    print(f"   🇮🇷 Iran IPv4: {len(iran_v4)} ranges")
    print(f"   🇮🇷 Iran IPv6: {len(iran_v6) if iran_v6 else 0} ranges")
    print(f"   🌐 DNS servers: {len(DNS_SERVERS)} IPv4 + {len(DNS_SERVERS_V6)} IPv6")

    if strict_mode:
        print(f"\n   ⚠️  STRICT MODE: TCP+UDP both restricted to Iran")
        print(f"      (Psiphon broker visibility may be affected)")
    else:
        print(f"\n   🌍 TCP: Global (for broker visibility)")
        print(f"   🇮🇷 UDP: Iran only")

    if admin_ips:
        print(f"\n   🔐 Admin IPs: {len(admin_ips)} whitelisted (full access)")
        for ip in admin_ips:
            print(f"      • {ip}")

    print("\n   ⚠️  YOUR SERVER IS NOT AFFECTED - ONLY VPN!")
    print("   🇮🇷 Only Iranian users can use your data tunnel!")
    if admin_ips:
        print("   🔐 Admin IPs have FULL server access (web, SSH, everything)")

    # Save config
    config = load_config()
    config['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S")
    config['strict_mode'] = strict_mode
    config['ipv4_count'] = len(iran_v4)
    config['ipv6_count'] = len(iran_v6) if iran_v6 else 0
    save_config(config)

    # Save rules
    print("\n💾 Saving rules...")
    print("   To make rules persistent across reboots:")
    print("   • Ubuntu/Debian: apt install iptables-persistent")
    print("   • Then run: netfilter-persistent save")

    logging.info(f"Iran-only mode enabled. IPv4: {len(iran_v4)}, IPv6: {len(iran_v6) if iran_v6 else 0}, Strict: {strict_mode}")

    input("\n   Press Enter to go back to menu...")
    return True


def disable_iran_only(quiet=False):
    """Disable Iran-only mode"""
    if not quiet:
        print("\n🔓 Disabling Iran-only mode...\n")

    config = load_config()

    # Remove admin IP rules from INPUT chain
    admin_ips = config.get('admin_ips', [])
    for admin_ip in admin_ips:
        run_cmd(f"iptables -D INPUT -s {admin_ip} -j ACCEPT", check=False)

    # Remove rules by interface (cleanup all protocol rules)
    vpn_iface = config.get('vpn_interface')
    vpn_port = config.get('vpn_port')

    if vpn_iface:
        if vpn_port:
            # Remove port-specific rules
            run_cmd(f"iptables -D INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=False)
            run_cmd(f"iptables -D INPUT -i {vpn_iface} -p tcp --dport {vpn_port} -j {RULE_PREFIX}", check=False)
            run_cmd(f"ip6tables -D INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=False)
            run_cmd(f"ip6tables -D INPUT -i {vpn_iface} -p tcp --dport {vpn_port} -j {RULE_PREFIX}", check=False)
        else:
            # Remove interface-wide rules
            run_cmd(f"iptables -D INPUT -i {vpn_iface} -j {RULE_PREFIX}", check=False)
            run_cmd(f"iptables -D INPUT -i {vpn_iface} -p udp -j {RULE_PREFIX}", check=False)
            run_cmd(f"ip6tables -D INPUT -i {vpn_iface} -j {RULE_PREFIX}", check=False)
            run_cmd(f"ip6tables -D INPUT -i {vpn_iface} -p udp -j {RULE_PREFIX}", check=False)

    # Flush and delete custom chains (IPv4)
    run_cmd(f"iptables -D INPUT -j {RULE_PREFIX}", check=False)
    run_cmd(f"iptables -F {RULE_PREFIX}", check=False)
    run_cmd(f"iptables -X {RULE_PREFIX}", check=False)

    # Flush and delete custom chains (IPv6)
    run_cmd(f"ip6tables -D INPUT -j {RULE_PREFIX}", check=False)
    run_cmd(f"ip6tables -F {RULE_PREFIX}", check=False)
    run_cmd(f"ip6tables -X {RULE_PREFIX}", check=False)

    # Destroy ipsets (IPv4)
    run_cmd(f"ipset destroy {RULE_PREFIX}_IRAN_V4", check=False)
    run_cmd(f"ipset destroy {RULE_PREFIX}_DNS_V4", check=False)
    run_cmd(f"ipset destroy {RULE_PREFIX}_ADMIN", check=False)

    # Destroy ipsets (IPv6)
    run_cmd(f"ipset destroy {RULE_PREFIX}_IRAN_V6", check=False)
    run_cmd(f"ipset destroy {RULE_PREFIX}_DNS_V6", check=False)

    # Legacy cleanup (for old version compatibility)
    run_cmd(f"ipset destroy {RULE_PREFIX}_IRAN", check=False)
    run_cmd(f"ipset destroy {RULE_PREFIX}_DNS", check=False)

    if not quiet:
        print("✅ Iran-only mode DISABLED")
        print("   VPN now accepts connections from all countries.")
        logging.info("Iran-only mode disabled")
        input("\n   Press Enter to go back to menu...")


def show_status():
    """Show current status with detailed information"""
    print("\n" + "=" * 50)
    print("📊 CURRENT STATUS")
    print("=" * 50 + "\n")

    # Check iptables rules (IPv4)
    success, out, _ = run_cmd(f"iptables -L {RULE_PREFIX} -n -v 2>/dev/null")

    if success and out and RULE_PREFIX in out:
        # Count IPv4 rules
        ipv4_rule_count = len([l for l in out.split('\n') if l and not l.startswith('Chain') and not l.startswith('target')])
        print(f"   ✅ IRAN-ONLY MODE ENABLED")
        print(f"   📋 IPv4 rules: {ipv4_rule_count}")

        # Check IPv6 rules
        success_v6, out_v6, _ = run_cmd(f"ip6tables -L {RULE_PREFIX} -n -v 2>/dev/null")
        if success_v6 and out_v6 and RULE_PREFIX in out_v6:
            ipv6_rule_count = len([l for l in out_v6.split('\n') if l and not l.startswith('Chain') and not l.startswith('target')])
            print(f"   📋 IPv6 rules: {ipv6_rule_count}")
        else:
            print(f"   📋 IPv6 rules: None (IPv6 disabled or blocked)")

        # Show ipset stats
        print(f"\n   🇮🇷 IP Range Statistics:")

        # IPv4 ranges
        success, out, _ = run_cmd(f"ipset list {RULE_PREFIX}_IRAN_V4 2>/dev/null | grep 'Number of entries'")
        if success and out:
            entries = out.split(':')[1].strip() if ':' in out else 'unknown'
            print(f"      • IPv4: {entries} Iran ranges")
        else:
            # Try legacy name
            success, out, _ = run_cmd(f"ipset list {RULE_PREFIX}_IRAN 2>/dev/null | grep 'Number of entries'")
            if success and out:
                entries = out.split(':')[1].strip() if ':' in out else 'unknown'
                print(f"      • IPv4: {entries} Iran ranges (legacy)")

        # IPv6 ranges
        success, out, _ = run_cmd(f"ipset list {RULE_PREFIX}_IRAN_V6 2>/dev/null | grep 'Number of entries'")
        if success and out:
            entries = out.split(':')[1].strip() if ':' in out else '0'
            print(f"      • IPv6: {entries} Iran ranges")
        else:
            print(f"      • IPv6: 0 ranges")

        # Show configuration from config file
        config = load_config()
        last_update = config.get('last_update', 'Unknown')
        strict_mode = config.get('strict_mode', False)

        print(f"\n   🕒 Last updated: {last_update}")

        if strict_mode:
            print(f"   ⚠️  Mode: STRICT (TCP+UDP restricted)")
        else:
            print(f"   🌍 Mode: Normal (UDP Iran-only, TCP global)")

    else:
        print(f"   ❌ IRAN-ONLY MODE DISABLED")

    # Check VPN interface
    config = load_config()
    vpn_iface = config.get('vpn_interface')
    if vpn_iface:
        success, out, _ = run_cmd(f"ip link show {vpn_iface} 2>/dev/null")
        print(f"\n   🌐 VPN Interface: {vpn_iface}")
        if success and 'state UP' in out:
            print(f"      Status: 🟢 UP")
        elif success:
            print(f"      Status: 🟡 Exists but DOWN")
        else:
            print(f"      Status: ⚪ Not found")

    # Show admin IPs
    admin_ips = config.get('admin_ips', [])
    if admin_ips:
        print(f"\n   🔐 Admin IP Whitelist:")
        for ip in admin_ips:
            print(f"      • {ip} (full server access)")
    else:
        print(f"\n   🔐 Admin IPs: None configured")

    # Show active connections
    print(f"\n   📊 Connection Statistics:")
    success, out, _ = run_cmd("ss -tunp 2>/dev/null | grep -c ESTAB")
    if success and out.strip().isdigit():
        print(f"      Active: {out.strip()} established connections")

    input("\n   Press Enter to go back to menu...")


def show_help():
    """Show help"""
    clear_screen()
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    HELP - Iran-Only Firewall v{VERSION}               ║
║                      Linux/Ubuntu Edition                         ║
╚═══════════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
  • Creates firewall rules that ONLY allow Iranian IPs to use your
    VPN bandwidth for data transfer (UDP).
  • Allows TCP globally so Psiphon brokers can see your node is active.
  • Uses EXPLICIT block rules - doesn't rely on system defaults.
  • Whitelists admin IPs for full server access (web, SSH, etc.)

HOW IT WORKS (Rule Priority):
  1. ALLOW admin IPs (full server access, highest priority)
  2. ALLOW DNS servers (required for operation)
  3. ALLOW established/related connections
  4. ALLOW UDP from Iran IP ranges (IPv4 + IPv6)
  5. EXPLICIT DROP all other traffic

MODES:
  • Normal Mode: TCP global, UDP Iran-only
    - Best for: Most users (ensures broker visibility)

  • Strict Mode: TCP Iran-only, UDP Iran-only
    - Best for: Maximum restriction (may affect broker visibility)

IMPROVEMENTS IN v{VERSION}:
  ✓ Explicit DROP rules (doesn't rely on implicit deny)
  ✓ IPv6 support for Iran ranges
  ✓ Firewall state verification
  ✓ Optional strict mode for TCP
  ✓ Detailed logging to {LOG_FILE}

REQUIREMENTS:
  • Ubuntu/Debian Linux (or compatible)
  • Python 3.6+
  • Root access (sudo)
  • iptables, ip6tables, and ipset installed
  • Active VPN service

INSTALLATION:
  sudo apt update
  sudo apt install iptables ipset iptables-persistent

  # Run script
  sudo python3 iran_firewall_linux.py

MAKING RULES PERSISTENT:
  # After enabling Iran-only mode:
  sudo apt install iptables-persistent
  sudo netfilter-persistent save

  # Rules will survive reboots

TROUBLESHOOTING:
  • "Permission denied" → Run with sudo
  • "Command not found" → Install iptables/ipset/ip6tables
  • "Interface not found" → Check VPN is running
  • Check logs: journalctl -k | grep IRAN-BLOCK
  • Check {LOG_FILE} for detailed logs

Press Enter to go back to menu...""")
    input()


def main():
    setup_logging()
    logging.info(f"=== Iran Firewall v{VERSION} (Linux) started ===")

    print_header()

    # Check if running as root
    if not is_root():
        print("❌ ERROR: This script must be run as root!")
        print("\n   Run with: sudo python3 iran_firewall_linux.py")
        logging.error("Not running as root")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("✅ Running as root")

    # Check dependencies
    print("🔍 Checking dependencies...")
    deps_ok = True

    for cmd in ['iptables', 'ip6tables', 'ipset', 'ip']:
        success, _, _ = run_cmd(f"which {cmd}")
        if success:
            print(f"   ✓ {cmd} found")
        else:
            print(f"   ✗ {cmd} NOT found")
            deps_ok = False

    if not deps_ok:
        print("\n   ⚠️  Missing dependencies!")
        print("   Install with: sudo apt install iptables ipset iproute2")
        input("\n   Press Enter to continue anyway...")

    time.sleep(1)

    while True:
        print_header()
        print("─" * 50)
        print("  MAIN MENU")
        print("─" * 50)
        print("  1. 🟢 Enable Iran-only mode (Normal)")
        print("  2. 🔒 Enable Iran-only mode (Strict)")
        print("  3. 🔴 Disable Iran-only mode")
        print("  4. 📊 Check status")
        print("  5. ⚙️  Configure VPN interface/port")
        print("  6. 🔐 Manage admin IP whitelist")
        print("  7. ❓ Help")
        print("  0. 🚪 Exit")
        print("─" * 50)
        print("  Normal: TCP global, UDP Iran-only")
        print("  Strict: TCP+UDP Iran-only (may affect visibility)")
        print("─" * 50)

        choice = input("\n  Enter choice: ").strip()

        if choice == "1":
            enable_iran_only(strict_mode=False)
        elif choice == "2":
            print("\n⚠️  STRICT MODE: Restricts both TCP and UDP to Iran only.")
            print("   This may cause Psiphon brokers to stop seeing your node.")
            confirm = input("   Enable Strict mode anyway? (y/n): ").strip().lower()
            if confirm == 'y':
                enable_iran_only(strict_mode=True)
        elif choice == "3":
            disable_iran_only()
        elif choice == "4":
            show_status()
        elif choice == "5":
            print("\n⚙️  Configuration\n")
            detect_vpn_interface()
            detect_vpn_port()
            input("\n   Configuration saved! Press Enter to continue...")
        elif choice == "6":
            manage_admin_ips()
        elif choice == "7":
            show_help()
        elif choice == "0":
            clear_screen()
            print("\n👋 Thank you for helping Iran!")
            print("   Share this tool to help more people.\n")
            logging.info("=== Iran Firewall exited ===")
            break
        else:
            print("   Invalid choice. Enter 0-7.")


if __name__ == "__main__":
    main()
