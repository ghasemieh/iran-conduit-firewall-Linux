#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║       IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT - v1.0.0            ║
║                    Linux/Ubuntu Edition                           ║
║                                                                   ║
║  Maximize your bandwidth for Iranian users by blocking           ║
║  connections from other countries.                                ║
║                                                                   ║
║  ⚠️  ONLY affects VPN traffic                                     ║
║  ✅ Your server and other services work normally                 ║
║                                                                   ║
║  GitHub: Share this script to help more people!                  ║
╚═══════════════════════════════════════════════════════════════════╝
"""

VERSION = "1.0.0-linux"

import subprocess
import sys
import os
import urllib.request
import json
import time

RULE_PREFIX = "IRAN_CONDUIT"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
CONDUIT_URL = "https://conduit.psiphon.ca/"

# DNS servers to whitelist
DNS_SERVERS = [
    "8.8.8.8", "8.8.4.4",           # Google DNS
    "1.1.1.1", "1.0.0.1",           # Cloudflare DNS
    "9.9.9.9", "149.112.112.112",   # Quad9 DNS
    "208.67.222.222", "208.67.220.220",  # OpenDNS
    "4.2.2.1", "4.2.2.2",           # Level3 DNS
    "178.22.122.100", "185.51.200.2",    # Shekan DNS (Iran)
    "10.202.10.202", "10.202.10.102",    # 403.online DNS (Iran)
]

# Iran IP sources
IP_SOURCES = [
    "https://www.ipdeny.com/ipblocks/data/countries/ir.zone",
    "https://raw.githubusercontent.com/herrbischoff/country-ip-blocks/master/ipv4/ir.cidr",
]


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear')


def print_header():
    """Print the application header"""
    clear_screen()
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║       🇮🇷 IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT v{VERSION} 🇮🇷       ║
╠═══════════════════════════════════════════════════════════════════╣
║  Maximize bandwidth for Iranian users during internet shutdowns  ║
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


def download_iran_ips():
    """Download Iran IP ranges"""
    print("📥 Downloading Iran IP ranges...")
    all_ips = set()
    success_count = 0

    for url in IP_SOURCES:
        source_name = url.split('/')[-1]
        try:
            print(f"   Fetching {source_name}...", end=" ", flush=True)
            req = urllib.request.Request(url, headers={'User-Agent': 'IranFirewall/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode('utf-8')
                ips = [line.strip() for line in data.split('\n')
                       if line.strip() and '/' in line and not line.startswith('#')]
                all_ips.update(ips)
                print(f"✓ {len(ips)} ranges")
                success_count += 1
        except Exception as e:
            print(f"✗ {str(e)[:50]}")

    if success_count == 0:
        print("   ❌ All downloads failed!")
        return None

    print(f"   📊 Total unique ranges: {len(all_ips)}")
    return sorted(list(all_ips))


def create_ipset(name, ips):
    """Create ipset for efficient IP matching"""
    # Delete if exists
    run_cmd(f"ipset destroy {name}", check=False)

    # Create new set
    success, _, _ = run_cmd(f"ipset create {name} hash:net maxelem 1000000", check=True)
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


def enable_iran_only():
    """Enable Iran-only mode using iptables"""
    print("\n" + "=" * 50)
    print("🇮🇷 ENABLING IRAN-ONLY MODE")
    print("=" * 50 + "\n")

    # Detect VPN interface
    vpn_iface = detect_vpn_interface()
    if not vpn_iface:
        print("   ❌ Cannot proceed without VPN interface")
        input("\n   Press Enter to go back...")
        return False

    # Detect VPN port (optional)
    vpn_port = detect_vpn_port()

    # Download Iran IPs
    iran_ips = download_iran_ips()
    if not iran_ips:
        print("\n❌ Failed to download Iran IP ranges")
        input("   Press Enter to go back...")
        return False

    # Clean up old rules
    print("\n🧹 Cleaning up old rules...")
    disable_iran_only(quiet=True)
    time.sleep(0.5)

    # Create ipset for Iran IPs
    print("\n📦 Creating IP set for Iran...")
    if not create_ipset(f"{RULE_PREFIX}_IRAN", iran_ips):
        print("   ❌ Failed to create ipset")
        input("   Press Enter to go back...")
        return False

    # Create ipset for DNS
    print("\n🌐 Creating IP set for DNS...")
    if not create_ipset(f"{RULE_PREFIX}_DNS", DNS_SERVERS):
        print("   ❌ Failed to create ipset")
        input("   Press Enter to go back...")
        return False

    # Create custom chain
    print("\n🔗 Creating firewall chain...")
    run_cmd(f"iptables -N {RULE_PREFIX}", check=False)

    # Build iptables rules
    print("🔒 Building firewall rules...")

    # Allow established connections
    run_cmd(f"iptables -A {RULE_PREFIX} -m state --state ESTABLISHED,RELATED -j ACCEPT", check=True)

    # Allow DNS
    run_cmd(f"iptables -A {RULE_PREFIX} -m set --match-set {RULE_PREFIX}_DNS src -j ACCEPT", check=True)

    # Allow Iran IPs
    run_cmd(f"iptables -A {RULE_PREFIX} -m set --match-set {RULE_PREFIX}_IRAN src -j ACCEPT", check=True)

    # Log blocked connections (optional - useful for monitoring)
    run_cmd(f"iptables -A {RULE_PREFIX} -j LOG --log-prefix '[IRAN-BLOCK] ' --log-level 4", check=False)

    # Block everything else
    run_cmd(f"iptables -A {RULE_PREFIX} -j DROP", check=True)

    # Apply to INPUT chain based on interface
    if vpn_port:
        run_cmd(f"iptables -I INPUT -i {vpn_iface} -p udp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
        run_cmd(f"iptables -I INPUT -i {vpn_iface} -p tcp --dport {vpn_port} -j {RULE_PREFIX}", check=True)
    else:
        # Apply to all traffic on VPN interface
        run_cmd(f"iptables -I INPUT -i {vpn_iface} -j {RULE_PREFIX}", check=True)

    # Summary
    print("\n" + "=" * 50)
    print("✅ IRAN-ONLY MODE ENABLED!")
    print("=" * 50)
    print(f"\n   🌐 VPN Interface: {vpn_iface}")
    if vpn_port:
        print(f"   🔌 VPN Port: {vpn_port}")
    print(f"   🇮🇷 Iran IPs: {len(iran_ips)} ranges allowed")
    print(f"   🌐 DNS servers: {len(DNS_SERVERS)} whitelisted")

    print("\n   ⚠️  YOUR SERVER IS NOT AFFECTED - ONLY VPN!")
    print("   🇮🇷 Only Iranian users can connect now!")

    # Save rules
    print("\n💾 Saving rules...")
    print("   To make rules persistent across reboots:")
    print("   • Ubuntu/Debian: apt install iptables-persistent")
    print("   • Then run: netfilter-persistent save")

    input("\n   Press Enter to go back to menu...")
    return True


def disable_iran_only(quiet=False):
    """Disable Iran-only mode"""
    if not quiet:
        print("\n🔓 Disabling Iran-only mode...\n")

    # Remove iptables rules
    run_cmd(f"iptables -D INPUT -j {RULE_PREFIX}", check=False)
    run_cmd(f"iptables -F {RULE_PREFIX}", check=False)
    run_cmd(f"iptables -X {RULE_PREFIX}", check=False)

    # Remove rules by interface (cleanup any remaining)
    config = load_config()
    vpn_iface = config.get('vpn_interface')
    if vpn_iface:
        run_cmd(f"iptables -D INPUT -i {vpn_iface} -j {RULE_PREFIX}", check=False)

    # Destroy ipsets
    run_cmd(f"ipset destroy {RULE_PREFIX}_IRAN", check=False)
    run_cmd(f"ipset destroy {RULE_PREFIX}_DNS", check=False)

    if not quiet:
        print("✅ Iran-only mode DISABLED")
        print("   VPN now accepts connections from all countries.")
        input("\n   Press Enter to go back to menu...")


def show_status():
    """Show current status"""
    print("\n📊 CURRENT STATUS\n")

    # Check iptables rules
    success, out, _ = run_cmd(f"iptables -L {RULE_PREFIX} -n -v 2>/dev/null")

    if success and out and RULE_PREFIX in out:
        # Count rules
        rule_count = len([l for l in out.split('\n') if l and not l.startswith('Chain') and not l.startswith('target')])
        print(f"   Firewall:  ✅ IRAN-ONLY MODE ENABLED")
        print(f"   Rules:     {rule_count} iptables rules active")

        # Show ipset stats
        success, out, _ = run_cmd(f"ipset list {RULE_PREFIX}_IRAN | grep 'Number of entries'")
        if success and out:
            entries = out.split(':')[1].strip() if ':' in out else 'unknown'
            print(f"   Iran IPs:  {entries} ranges loaded")
    else:
        print(f"   Firewall:  ❌ IRAN-ONLY MODE DISABLED")

    # Check VPN interface
    config = load_config()
    vpn_iface = config.get('vpn_interface')
    if vpn_iface:
        success, out, _ = run_cmd(f"ip link show {vpn_iface}")
        print(f"\n   VPN Iface: {vpn_iface}")
        if success and 'state UP' in out:
            print(f"   Status:    🟢 Interface is UP")
        elif success:
            print(f"   Status:    🟡 Interface exists but may be DOWN")
        else:
            print(f"   Status:    ⚪ Interface not found")

    # Show active connections
    print(f"\n   📊 Connection Statistics:")
    success, out, _ = run_cmd("ss -tunp | grep -c ESTAB")
    if success and out.strip().isdigit():
        print(f"   Active:    {out.strip()} established connections")

    input("\n   Press Enter to go back to menu...")


def show_help():
    """Show help"""
    clear_screen()
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    HELP - Iran-Only Firewall                      ║
║                      Linux/Ubuntu Edition                         ║
╚═══════════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
  • Blocks connections to your VPN from non-Iran IPs
  • Lets only Iranian users use your bandwidth
  • Does NOT affect your server - only VPN traffic!

HOW IT WORKS:
  1. Creates iptables firewall rules for your VPN interface
  2. Uses ipset for efficient IP range matching
  3. Blocks all inbound connections to VPN
  4. Allows only Iran IP ranges + DNS servers

REQUIREMENTS:
  • Ubuntu/Debian Linux (or compatible)
  • Python 3.6+
  • Root access (sudo)
  • iptables and ipset installed
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
  • "Command not found" → Install iptables/ipset
  • "Interface not found" → Check VPN is running
  • Check logs: journalctl -k | grep IRAN-BLOCK

Press Enter to go back to menu...""")
    input()


def main():
    print_header()

    # Check if running as root
    if not is_root():
        print("❌ ERROR: This script must be run as root!")
        print("\n   Run with: sudo python3 iran_firewall_linux.py")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("✅ Running as root")

    # Check dependencies
    print("🔍 Checking dependencies...")
    deps_ok = True

    for cmd in ['iptables', 'ipset', 'ip']:
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
        print("─" * 45)
        print("  MAIN MENU")
        print("─" * 45)
        print("  1. 🟢 Enable Iran-only mode")
        print("  2. 🔴 Disable Iran-only mode")
        print("  3. 📊 Check status")
        print("  4. ⚙️  Configure VPN interface/port")
        print("  5. ❓ Help")
        print("  0. 🚪 Exit")
        print("─" * 45)

        choice = input("\n  Enter choice: ").strip()

        if choice == "1":
            enable_iran_only()
        elif choice == "2":
            disable_iran_only()
        elif choice == "3":
            show_status()
        elif choice == "4":
            print("\n⚙️  Configuration\n")
            detect_vpn_interface()
            detect_vpn_port()
            input("\n   Configuration saved! Press Enter to continue...")
        elif choice == "5":
            show_help()
        elif choice == "0":
            clear_screen()
            print("\n👋 Thank you for helping Iran!")
            print("   Share this tool to help more people.\n")
            break
        else:
            print("   Invalid choice. Enter 0-5.")


if __name__ == "__main__":
    main()
