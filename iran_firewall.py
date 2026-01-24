#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║       IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT - v1.0.0            ║
║                                                                   ║
║  Maximize your bandwidth for Iranian users by blocking           ║
║  connections from other countries.                                ║
║                                                                   ║
║  ⚠️  ONLY affects conduit-tunnel-core.exe                        ║
║  ✅ Your PC, browsing, and apps work normally                    ║
║                                                                   ║
║  GitHub: Share this script to help more people!                  ║
╚═══════════════════════════════════════════════════════════════════╝
"""

VERSION = "1.0.0"

import subprocess
import sys
import os
import urllib.request
import json
import time
import webbrowser

RULE_PREFIX = "IranConduit"
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
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the application header"""
    clear_screen()
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║       🇮🇷 IRAN-ONLY FIREWALL FOR PSIPHON CONDUIT v{VERSION} 🇮🇷       ║
╠═══════════════════════════════════════════════════════════════════╣
║  Maximize bandwidth for Iranian users during internet shutdowns  ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass


def run_ps(cmd, check=False):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True, text=True
    )
    success = result.returncode == 0
    if check and not success:
        print(f"   ⚠️  Command failed: {result.stderr[:100]}")
    return success, result.stdout, result.stderr


def is_conduit_running():
    """Check if Psiphon Conduit is running"""
    _, out, _ = run_ps('Get-Process -Name "conduit-tunnel-core" -ErrorAction SilentlyContinue')
    return "conduit" in out.lower() or "Id" in out


def start_conduit():
    """Start Psiphon Conduit"""
    config = load_config()
    conduit_path = config.get('conduit_path')
    
    if conduit_path and os.path.exists(conduit_path):
        print("🚀 Starting Conduit...")
        try:
            # Start the process
            subprocess.Popen([conduit_path], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(2)
            
            if is_conduit_running():
                print("   ✅ Conduit started successfully!")
                return True
            else:
                print("   ⚠️  Conduit may not have started. Check manually.")
                return False
        except Exception as e:
            print(f"   ❌ Failed to start: {e}")
            return False
    else:
        print("   ❌ Conduit path not found.")
        print("   💡 Run 'Enable Iran-only mode' first to locate Conduit.")
        print(f"\n   Or download from: {CONDUIT_URL}")
        return False


def check_and_start_conduit():
    """Check if Conduit is running, offer to start if not"""
    if is_conduit_running():
        print("   🟢 Conduit is running")
        return True
    else:
        print("   ⚪ Conduit is NOT running")
        choice = input("\n   Start Conduit now? (y/n): ").strip().lower()
        if choice == 'y':
            return start_conduit()
        return False


def find_conduit_exe():
    """Find conduit-tunnel-core.exe (supports UWP and regular installs)"""
    config = load_config()
    saved_path = config.get('conduit_path')
    if saved_path and os.path.exists(saved_path):
        print(f"🔍 Using saved path: {saved_path}")
        return saved_path
    
    print("🔍 Searching for Psiphon Conduit...")
    
    # Method 1: Check if UWP app is installed (Windows Store version)
    print("   Checking Windows Store apps...")
    success, out, _ = run_ps('(Get-AppxPackage -Name "*Conduit*").InstallLocation')
    if success and out.strip():
        uwp_path = out.strip()
        # Find exe in UWP package
        exe_path = os.path.join(uwp_path, "conduit-tunnel-core.exe")
        if os.path.exists(exe_path):
            print(f"   ✓ Found UWP app: {exe_path}")
            config['conduit_path'] = exe_path
            save_config(config)
            return exe_path
        # Look for exe in subdirectories
        for root, dirs, files in os.walk(uwp_path):
            if "conduit-tunnel-core.exe" in files:
                path = os.path.join(root, "conduit-tunnel-core.exe")
                print(f"   ✓ Found UWP app: {path}")
                config['conduit_path'] = path
                save_config(config)
                return path
    
    # Method 2: Check common installation paths
    print("   Checking common locations...")
    common_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%"),
        os.path.expandvars(r"%APPDATA%"),
        os.path.expandvars(r"%USERPROFILE%\Downloads"),
        os.path.expandvars(r"%PROGRAMFILES%"),
    ]
    
    for base in common_paths:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            if "conduit-tunnel-core.exe" in files:
                path = os.path.join(root, "conduit-tunnel-core.exe")
                print(f"   ✓ Found: {path}")
                config['conduit_path'] = path
                save_config(config)
                return path
            # Limit depth to avoid long searches
            if root.count(os.sep) - base.count(os.sep) > 4:
                dirs.clear()
    
    # Method 3: Check running processes
    print("   Checking running processes...")
    success, out, _ = run_ps('(Get-Process -Name "conduit-tunnel-core" -ErrorAction SilentlyContinue).Path')
    if success and out.strip():
        path = out.strip()
        if os.path.exists(path):
            print(f"   ✓ Found running process: {path}")
            config['conduit_path'] = path
            save_config(config)
            return path
    
    # Not found, ask user
    print("   ✗ Not found automatically")
    print("\n   💡 TIP: If using Windows Store version, make sure Conduit is running first")
    print("      then try again. The path will be detected from the running process.")
    print("\n   0. Back to main menu")
    path = input("\n   Enter full path (or 0 to go back): ").strip().strip('"')
    
    if path == "0":
        return None
    
    if path and os.path.exists(path):
        config['conduit_path'] = path
        save_config(config)
        return path
    
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


def enable_iran_only():
    """Enable Iran-only mode"""
    print("\n" + "=" * 50)
    print("🇮🇷 ENABLING IRAN-ONLY MODE")
    print("=" * 50 + "\n")
    
    # Check if Conduit is running
    print("📡 Checking Conduit status...")
    if not is_conduit_running():
        print("   ⚪ Conduit is NOT running")
        choice = input("   Start Conduit first? (y/n/0=back): ").strip().lower()
        if choice == '0':
            return False
        if choice == 'y':
            if not start_conduit():
                input("\n   Press Enter to continue anyway...")
    else:
        print("   🟢 Conduit is running")
    
    # Find Conduit
    conduit_path = find_conduit_exe()
    if not conduit_path:
        return False
    
    # Download IPs
    iran_ips = download_iran_ips()
    if not iran_ips:
        print("\n❌ Failed to download Iran IP ranges")
        input("   Press Enter to go back...")
        return False
    
    # Remove existing rules
    print("\n🧹 Cleaning up old rules...")
    disable_iran_only(quiet=True)
    time.sleep(0.5)
    
    conduit_escaped = conduit_path.replace("'", "''")
    
    # Create block-all rule
    print("🔒 Creating block rule for Conduit...")
    success, _, _ = run_ps(f"""
        New-NetFirewallRule -DisplayName "{RULE_PREFIX}-BlockAll" `
            -Description "Block all inbound to Conduit - IranFirewall v{VERSION}" `
            -Direction Inbound -Action Block -Enabled True `
            -Program '{conduit_escaped}'
    """, check=True)
    
    if not success:
        print("   ❌ Failed to create block rule")
        input("   Press Enter to go back...")
        return False
    
    # Allow DNS
    print("🌐 Whitelisting DNS servers...")
    dns_list = ",".join(DNS_SERVERS)
    run_ps(f"""
        New-NetFirewallRule -DisplayName "{RULE_PREFIX}-DNS" `
            -Description "Allow DNS - IranFirewall v{VERSION}" `
            -Direction Inbound -Action Allow -Enabled True `
            -Program '{conduit_escaped}' -RemoteAddress {dns_list}
    """, check=True)
    
    # Allow Iran IPs
    print(f"🇮🇷 Adding {len(iran_ips)} Iran IP ranges...")
    batch_size = 200
    total_batches = (len(iran_ips) + batch_size - 1) // batch_size
    failed_batches = 0
    
    for i in range(0, len(iran_ips), batch_size):
        batch = iran_ips[i:i+batch_size]
        ip_list = ",".join(batch)
        batch_num = i // batch_size
        
        progress = min(i + batch_size, len(iran_ips))
        pct = int(progress / len(iran_ips) * 100)
        print(f"\r   Progress: [{('█' * (pct//5)).ljust(20)}] {pct}% ({progress}/{len(iran_ips)})", end="", flush=True)
        
        success, _, _ = run_ps(f"""
            New-NetFirewallRule -DisplayName "{RULE_PREFIX}-Iran-{batch_num}" `
                -Description "Allow Iran IPs - IranFirewall v{VERSION}" `
                -Direction Inbound -Action Allow -Enabled True `
                -Program '{conduit_escaped}' -RemoteAddress {ip_list}
        """)
        
        if not success:
            failed_batches += 1
    
    print()
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ IRAN-ONLY MODE ENABLED!")
    print("=" * 50)
    print(f"\n   📁 Conduit: {conduit_path}")
    print(f"   🇮🇷 Iran IPs: {len(iran_ips)} ranges allowed")
    print(f"   🌐 DNS servers: {len(DNS_SERVERS)} whitelisted")
    print(f"   📦 Firewall rules: {total_batches + 2} created")
    
    if failed_batches > 0:
        print(f"   ⚠️  {failed_batches} batches failed")
    
    print("\n   ⚠️  YOUR PC IS NOT AFFECTED - ONLY CONDUIT!")
    print("   🇮🇷 Only Iranian users can connect now!")
    
    input("\n   Press Enter to go back to menu...")
    return True


def disable_iran_only(quiet=False):
    """Disable Iran-only mode"""
    if not quiet:
        print("\n🔓 Disabling Iran-only mode...\n")
    
    run_ps(f'Get-NetFirewallRule -DisplayName "{RULE_PREFIX}*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule')
    
    if not quiet:
        print("✅ Iran-only mode DISABLED")
        print("   Conduit now accepts connections from all countries.")
        input("\n   Press Enter to go back to menu...")


def show_status():
    """Show current status"""
    print("\n📊 CURRENT STATUS\n")
    
    # Check firewall rules
    success, out, _ = run_ps(f'Get-NetFirewallRule -DisplayName "{RULE_PREFIX}*" -ErrorAction SilentlyContinue | Select-Object DisplayName')
    
    if RULE_PREFIX in out:
        lines = [l for l in out.split('\n') if RULE_PREFIX in l]
        print(f"   Firewall:  ✅ IRAN-ONLY MODE ENABLED")
        print(f"   Rules:     {len(lines)} firewall rules active")
    else:
        print(f"   Firewall:  ❌ IRAN-ONLY MODE DISABLED")
    
    # Check Conduit
    print(f"\n   Conduit:   ", end="")
    if is_conduit_running():
        print("🟢 Running")
    else:
        print("⚪ Not running")
    
    input("\n   Press Enter to go back to menu...")


def conduit_menu():
    """Conduit management submenu"""
    while True:
        print_header()
        print("─" * 45)
        print("  CONDUIT MANAGEMENT")
        print("─" * 45)
        print("  1. 🟢 Start Conduit")
        print("  2. 🔴 Stop Conduit")
        print("  3. 📊 Check if running")
        print("  4. 🌐 Open Conduit website")
        print("  0. ⬅️  Back to main menu")
        print("─" * 40)
        
        choice = input("\n  Enter choice: ").strip()
        
        if choice == "1":
            if is_conduit_running():
                print("\n   ⚠️  Conduit is already running!")
            else:
                start_conduit()
            input("\n   Press Enter to continue...")
        elif choice == "2":
            print("\n   Stopping Conduit...")
            run_ps('Stop-Process -Name "conduit-tunnel-core" -Force -ErrorAction SilentlyContinue')
            time.sleep(1)
            if not is_conduit_running():
                print("   ✅ Conduit stopped")
            else:
                print("   ⚠️  May still be running")
            input("\n   Press Enter to continue...")
        elif choice == "3":
            print()
            if is_conduit_running():
                print("   🟢 Conduit is RUNNING")
            else:
                print("   ⚪ Conduit is NOT running")
            input("\n   Press Enter to continue...")
        elif choice == "4":
            print(f"\n   Opening {CONDUIT_URL}")
            webbrowser.open(CONDUIT_URL)
            input("\n   Press Enter to continue...")
        elif choice == "0":
            break
        else:
            print("   Invalid choice")


def show_help():
    """Show help"""
    clear_screen()
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    HELP - Iran-Only Firewall                      ║
╚═══════════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
  • Blocks connections to your Psiphon Conduit from non-Iran IPs
  • Lets only Iranian users use your bandwidth
  • Does NOT affect your PC - only Conduit!

HOW IT WORKS:
  1. Creates Windows Firewall rules for conduit-tunnel-core.exe
  2. Blocks all inbound connections to Conduit
  3. Allows only Iran IP ranges + DNS servers

REQUIREMENTS:
  • Windows 10/11
  • Python 3.6+
  • Run as Administrator
  • Psiphon Conduit running

TROUBLESHOOTING:
  • "Access denied" → Right-click, Run as Administrator
  • "Conduit not found" → Enter the path manually
  • "Download failed" → Check internet connection
  
Press Enter to go back to menu...""")
    input()


def main():
    os.system('')  # Enable ANSI colors
    
    print_header()
    
    if not is_admin():
        print("❌ ERROR: This script must be run as Administrator!")
        print("\n   Right-click → Run as administrator")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("✅ Running as Administrator")
    time.sleep(1)
    
    while True:
        print_header()
        print("─" * 45)
        print("  MAIN MENU")
        print("─" * 45)
        print("  1. 🟢 Enable Iran-only mode")
        print("  2. 🔴 Disable Iran-only mode")
        print("  3. 📊 Check status")
        print("  4. 🚀 Conduit management")
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
            conduit_menu()
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
