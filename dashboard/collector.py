#!/usr/bin/env python3
"""
VPN Connection Data Collector
Monitors VPN connections and stores geographic data in real-time
"""

import subprocess
import re
import time
import sqlite3
from datetime import datetime
import sys
import os

try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False
    print("⚠️  Warning: geoip2 not installed. Install with: pip3 install geoip2")


class ConnectionCollector:
    def __init__(self,
                 db_path='vpn_connections.db',
                 geoip_db='/usr/share/GeoIP/GeoLite2-City.mmdb',
                 interface='tun0',
                 port=None):
        """
        Initialize connection collector

        Args:
            db_path: Path to SQLite database
            geoip_db: Path to MaxMind GeoIP database
            interface: VPN interface name (tun0, wg0, etc.)
            port: VPN port (optional)
        """
        self.db_path = db_path
        self.interface = interface
        self.port = port

        # Initialize GeoIP reader
        if GEOIP_AVAILABLE and os.path.exists(geoip_db):
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db)
                print(f"✓ GeoIP database loaded: {geoip_db}")
            except Exception as e:
                print(f"⚠️  Failed to load GeoIP database: {e}")
                self.geoip_reader = None
        else:
            self.geoip_reader = None
            if not GEOIP_AVAILABLE:
                print("⚠️  GeoIP lookups disabled (geoip2 not installed)")
            else:
                print(f"⚠️  GeoIP database not found: {geoip_db}")

        self.init_db()

    def init_db(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Main connections table
        c.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                src_ip TEXT NOT NULL,
                src_port INTEGER,
                dst_ip TEXT,
                dst_port INTEGER,
                protocol TEXT,
                state TEXT,
                country_code TEXT,
                country_name TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                bytes_recv INTEGER DEFAULT 0,
                bytes_sent INTEGER DEFAULT 0,
                packets_recv INTEGER DEFAULT 0,
                packets_sent INTEGER DEFAULT 0
            )
        ''')

        # Indexes for performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON connections(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_src_ip ON connections(src_ip)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_country ON connections(country_code)')

        # Summary table for faster queries
        c.execute('''
            CREATE TABLE IF NOT EXISTS connection_summary (
                timestamp TEXT NOT NULL,
                total_connections INTEGER,
                unique_ips INTEGER,
                bytes_total INTEGER,
                PRIMARY KEY (timestamp)
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✓ Database initialized: {self.db_path}")

    def get_active_connections_ss(self):
        """Get active connections using 'ss' command"""
        connections = []

        try:
            # Get all TCP and UDP connections
            for protocol in ['tcp', 'udp']:
                cmd = ['ss', '-tunap', f'({protocol})']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

                for line in result.stdout.split('\n')[1:]:  # Skip header
                    if not line.strip():
                        continue

                    parts = line.split()
                    if len(parts) < 6:
                        continue

                    # Parse based on protocol
                    try:
                        proto = parts[0]
                        state = parts[1] if protocol == 'tcp' else 'ESTABLISHED'
                        recv_q = int(parts[2])
                        send_q = int(parts[3])
                        local_addr = parts[4]
                        peer_addr = parts[5]

                        # Extract IPs and ports
                        # Format: [::ffff:1.2.3.4]:443 or 1.2.3.4:443
                        peer_match = re.search(r'\[?::ffff:([0-9.]+)\]?:(\d+)|([0-9.]+):(\d+)', peer_addr)
                        local_match = re.search(r'\[?::ffff:([0-9.]+)\]?:(\d+)|([0-9.]+):(\d+)', local_addr)

                        if peer_match:
                            src_ip = peer_match.group(1) or peer_match.group(3)
                            src_port = int(peer_match.group(2) or peer_match.group(4))

                            dst_ip = None
                            dst_port = None
                            if local_match:
                                dst_ip = local_match.group(1) or local_match.group(3)
                                dst_port = int(local_match.group(2) or local_match.group(4))

                            # Skip local connections
                            if src_ip.startswith('127.') or src_ip.startswith('::1'):
                                continue

                            connections.append({
                                'src_ip': src_ip,
                                'src_port': src_port,
                                'dst_ip': dst_ip,
                                'dst_port': dst_port,
                                'protocol': proto,
                                'state': state,
                                'bytes_recv': recv_q,
                                'bytes_sent': send_q
                            })
                    except (ValueError, IndexError) as e:
                        continue

        except subprocess.TimeoutExpired:
            print("⚠️  ss command timeout")
        except Exception as e:
            print(f"⚠️  Error reading ss: {e}")

        return connections

    def get_conntrack_connections(self):
        """Get connection tracking data from netfilter (requires root)"""
        connections = []

        try:
            # Try conntrack command
            result = subprocess.run(
                ['conntrack', '-L', '-o', 'extended'],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if not line.strip() or 'src=' not in line:
                    continue

                try:
                    # Parse conntrack output
                    # Example: ipv4 2 udp 17 src=1.2.3.4 dst=... packets=10 bytes=1234

                    # Extract protocol
                    protocol = 'udp' if 'udp' in line else 'tcp'

                    # Extract IPs
                    src_match = re.search(r'src=([0-9.]+)', line)
                    dst_match = re.search(r'dst=([0-9.]+)', line)

                    # Extract ports
                    sport_match = re.search(r'sport=(\d+)', line)
                    dport_match = re.search(r'dport=(\d+)', line)

                    # Extract statistics
                    packets_match = re.search(r'packets=(\d+)', line)
                    bytes_match = re.search(r'bytes=(\d+)', line)

                    if src_match and dst_match:
                        src_ip = src_match.group(1)

                        # Skip local IPs
                        if src_ip.startswith('127.') or src_ip.startswith('10.') or src_ip.startswith('192.168.'):
                            continue

                        connections.append({
                            'src_ip': src_ip,
                            'src_port': int(sport_match.group(1)) if sport_match else None,
                            'dst_ip': dst_match.group(1),
                            'dst_port': int(dport_match.group(1)) if dport_match else None,
                            'protocol': protocol,
                            'state': 'ESTABLISHED',
                            'packets_recv': int(packets_match.group(1)) if packets_match else 0,
                            'bytes_recv': int(bytes_match.group(1)) if bytes_match else 0
                        })
                except (ValueError, AttributeError) as e:
                    continue

        except FileNotFoundError:
            # conntrack not installed
            pass
        except subprocess.TimeoutExpired:
            print("⚠️  conntrack command timeout")
        except Exception as e:
            print(f"⚠️  Error reading conntrack: {e}")

        return connections

    def geolocate_ip(self, ip):
        """Get geographic information for IP address"""
        if not self.geoip_reader:
            return {
                'country_code': 'XX',
                'country_name': 'Unknown',
                'city': 'Unknown',
                'latitude': None,
                'longitude': None
            }

        try:
            response = self.geoip_reader.city(ip)
            return {
                'country_code': response.country.iso_code or 'XX',
                'country_name': response.country.name or 'Unknown',
                'city': response.city.name or 'Unknown',
                'latitude': response.location.latitude,
                'longitude': response.location.longitude
            }
        except geoip2.errors.AddressNotFoundError:
            return {
                'country_code': 'XX',
                'country_name': 'Unknown',
                'city': 'Unknown',
                'latitude': None,
                'longitude': None
            }
        except Exception as e:
            return {
                'country_code': 'XX',
                'country_name': 'Unknown',
                'city': 'Unknown',
                'latitude': None,
                'longitude': None
            }

    def store_connections(self, connections):
        """Store connections in database"""
        if not connections:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        timestamp = datetime.utcnow().isoformat()

        # Cache for geo lookups (avoid repeated lookups)
        geo_cache = {}

        for conn_data in connections:
            src_ip = conn_data['src_ip']

            # Get geo data (with caching)
            if src_ip not in geo_cache:
                geo_cache[src_ip] = self.geolocate_ip(src_ip)
            geo = geo_cache[src_ip]

            # Insert connection record
            c.execute('''
                INSERT INTO connections
                (timestamp, src_ip, src_port, dst_ip, dst_port, protocol, state,
                 country_code, country_name, city, latitude, longitude,
                 bytes_recv, bytes_sent, packets_recv, packets_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                src_ip,
                conn_data.get('src_port'),
                conn_data.get('dst_ip'),
                conn_data.get('dst_port'),
                conn_data.get('protocol', 'udp'),
                conn_data.get('state', 'UNKNOWN'),
                geo['country_code'],
                geo['country_name'],
                geo['city'],
                geo['latitude'],
                geo['longitude'],
                conn_data.get('bytes_recv', 0),
                conn_data.get('bytes_sent', 0),
                conn_data.get('packets_recv', 0),
                conn_data.get('packets_sent', 0)
            ))

        # Update summary
        unique_ips = len(geo_cache)
        total_bytes = sum(c.get('bytes_recv', 0) + c.get('bytes_sent', 0) for c in connections)

        c.execute('''
            INSERT OR REPLACE INTO connection_summary
            (timestamp, total_connections, unique_ips, bytes_total)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, len(connections), unique_ips, total_bytes))

        conn.commit()
        conn.close()

    def cleanup_old_data(self, days=7):
        """Remove data older than N days"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Delete old connections
        c.execute('''
            DELETE FROM connections
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))

        deleted = c.rowcount

        # Delete old summaries
        c.execute('''
            DELETE FROM connection_summary
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))

        conn.commit()
        conn.close()

        if deleted > 0:
            print(f"🗑️  Cleaned up {deleted} old records")

    def run(self, interval=5, use_conntrack=True):
        """
        Run collector in continuous loop

        Args:
            interval: Seconds between collections
            use_conntrack: Try conntrack in addition to ss
        """
        print(f"""
╔══════════════════════════════════════════════════════════╗
║         VPN CONNECTION COLLECTOR - STARTED               ║
╠══════════════════════════════════════════════════════════╣
║  Interface: {self.interface:43} ║
║  Interval:  {interval} seconds{' ' * 37} ║
║  Database:  {self.db_path:43} ║
╚══════════════════════════════════════════════════════════╝
""")

        iteration = 0
        last_cleanup = time.time()

        while True:
            try:
                iteration += 1
                start_time = time.time()

                # Collect from multiple sources
                connections = []

                # Method 1: ss command
                ss_conns = self.get_active_connections_ss()
                connections.extend(ss_conns)

                # Method 2: conntrack (if available and requested)
                if use_conntrack:
                    ct_conns = self.get_conntrack_connections()
                    # Merge with ss data (prefer conntrack for byte counts)
                    for ct_conn in ct_conns:
                        # Check if already in list from ss
                        found = False
                        for conn in connections:
                            if conn['src_ip'] == ct_conn['src_ip'] and conn.get('src_port') == ct_conn.get('src_port'):
                                # Update with conntrack data
                                conn['packets_recv'] = ct_conn.get('packets_recv', 0)
                                conn['bytes_recv'] = max(conn.get('bytes_recv', 0), ct_conn.get('bytes_recv', 0))
                                found = True
                                break
                        if not found:
                            connections.append(ct_conn)

                # Remove duplicates based on src_ip
                unique_connections = {}
                for conn in connections:
                    key = (conn['src_ip'], conn.get('src_port'))
                    if key not in unique_connections:
                        unique_connections[key] = conn

                connections = list(unique_connections.values())

                # Store in database
                if connections:
                    self.store_connections(connections)
                    elapsed = time.time() - start_time
                    print(f"[{iteration:05d}] {datetime.now().strftime('%H:%M:%S')} | "
                          f"Connections: {len(connections):3d} | "
                          f"Unique IPs: {len(set(c['src_ip'] for c in connections)):3d} | "
                          f"Time: {elapsed:.2f}s")
                else:
                    print(f"[{iteration:05d}] {datetime.now().strftime('%H:%M:%S')} | No active connections")

                # Cleanup old data once per day
                if time.time() - last_cleanup > 86400:
                    self.cleanup_old_data()
                    last_cleanup = time.time()

                # Sleep until next interval
                time.sleep(max(0, interval - (time.time() - start_time)))

            except KeyboardInterrupt:
                print("\n\n🛑 Stopping collector...")
                break
            except Exception as e:
                print(f"❌ Error in collection loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(interval)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='VPN Connection Collector')
    parser.add_argument('-i', '--interface', default='tun0',
                        help='VPN interface name (default: tun0)')
    parser.add_argument('-p', '--port', type=int,
                        help='VPN port (optional)')
    parser.add_argument('-d', '--database', default='vpn_connections.db',
                        help='SQLite database path')
    parser.add_argument('-g', '--geoip-db', default='/usr/share/GeoIP/GeoLite2-City.mmdb',
                        help='GeoIP database path')
    parser.add_argument('-t', '--interval', type=int, default=5,
                        help='Collection interval in seconds (default: 5)')
    parser.add_argument('--no-conntrack', action='store_true',
                        help='Disable conntrack monitoring')

    args = parser.parse_args()

    # Check if running as root (recommended for conntrack)
    if os.geteuid() != 0 and not args.no_conntrack:
        print("⚠️  Not running as root - conntrack may not work")
        print("   For full functionality, run with: sudo python3 collector.py")

    # Create collector
    collector = ConnectionCollector(
        db_path=args.database,
        geoip_db=args.geoip_db,
        interface=args.interface,
        port=args.port
    )

    # Run
    collector.run(
        interval=args.interval,
        use_conntrack=not args.no_conntrack
    )


if __name__ == '__main__':
    main()
