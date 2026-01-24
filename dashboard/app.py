#!/usr/bin/env python3
"""
VPN Monitoring Dashboard - Web Server
Flask application with real-time updates via WebSocket
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime, timedelta
import hashlib
import os
import threading
import time
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'CHANGE_THIS_SECRET_KEY_IN_PRODUCTION')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration
DB_PATH = os.environ.get('DB_PATH', 'vpn_connections.db')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Change this!


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================== ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username

            if request.is_json:
                return jsonify({'success': True})
            return redirect(url_for('dashboard'))

        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


# ==================== API ENDPOINTS ====================

@app.route('/api/stats/current')
@login_required
def get_current_stats():
    """Get current real-time statistics"""
    conn = get_db()
    c = conn.cursor()

    # Active connections (last 30 seconds)
    c.execute('''
        SELECT COUNT(DISTINCT src_ip) as active_ips,
               COUNT(*) as total_connections
        FROM connections
        WHERE timestamp > datetime('now', '-30 seconds')
    ''')
    row = c.fetchone()
    active_ips = row['active_ips']
    total_connections = row['total_connections']

    # Total bytes (last minute)
    c.execute('''
        SELECT SUM(bytes_recv) as bytes_in,
               SUM(bytes_sent) as bytes_out
        FROM connections
        WHERE timestamp > datetime('now', '-1 minute')
    ''')
    row = c.fetchone()
    bytes_in = row['bytes_in'] or 0
    bytes_out = row['bytes_out'] or 0

    # Top countries (last 5 minutes)
    c.execute('''
        SELECT country_code, country_name, COUNT(DISTINCT src_ip) as count
        FROM connections
        WHERE timestamp > datetime('now', '-5 minutes')
              AND country_code != 'XX'
        GROUP BY country_code, country_name
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_countries = [dict(row) for row in c.fetchall()]

    conn.close()

    return jsonify({
        'active_ips': active_ips,
        'total_connections': total_connections,
        'bytes_in': bytes_in,
        'bytes_out': bytes_out,
        'top_countries': top_countries,
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/map-data')
@login_required
def get_map_data():
    """Get data for map visualization"""
    # Time range (default: last 5 minutes)
    minutes = int(request.args.get('minutes', 5))

    conn = get_db()
    c = conn.cursor()

    # Get recent connections with geo data
    c.execute('''
        SELECT
            src_ip,
            country_code,
            country_name,
            city,
            latitude,
            longitude,
            COUNT(*) as connection_count,
            MAX(timestamp) as last_seen
        FROM connections
        WHERE timestamp > datetime('now', '-' || ? || ' minutes')
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
        GROUP BY src_ip, country_code, country_name, city, latitude, longitude
        ORDER BY connection_count DESC
    ''', (minutes,))

    markers = []
    for row in c.fetchall():
        markers.append({
            'ip': row['src_ip'],
            'country_code': row['country_code'],
            'country_name': row['country_name'],
            'city': row['city'],
            'lat': row['latitude'],
            'lon': row['longitude'],
            'count': row['connection_count'],
            'last_seen': row['last_seen']
        })

    conn.close()

    return jsonify({
        'markers': markers,
        'total': len(markers),
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/connections/recent')
@login_required
def get_recent_connections():
    """Get recent connection list"""
    limit = int(request.args.get('limit', 50))

    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT
            timestamp,
            src_ip,
            src_port,
            country_code,
            country_name,
            city,
            protocol,
            state,
            bytes_recv,
            bytes_sent
        FROM connections
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))

    connections = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify({
        'connections': connections,
        'count': len(connections)
    })


@app.route('/api/history/timeline')
@login_required
def get_history_timeline():
    """Get historical connection data for charts"""
    hours = int(request.args.get('hours', 24))
    granularity = request.args.get('granularity', 'hour')  # minute, hour, day

    conn = get_db()
    c = conn.cursor()

    if granularity == 'minute':
        time_format = '%Y-%m-%d %H:%M:00'
    elif granularity == 'hour':
        time_format = '%Y-%m-%d %H:00:00'
    else:  # day
        time_format = '%Y-%m-%d 00:00:00'

    c.execute(f'''
        SELECT
            strftime(?, timestamp) as time_bucket,
            COUNT(DISTINCT src_ip) as unique_ips,
            COUNT(*) as total_connections,
            SUM(bytes_recv + bytes_sent) as total_bytes
        FROM connections
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        GROUP BY time_bucket
        ORDER BY time_bucket ASC
    ''', (time_format, hours))

    data = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify({
        'timeline': data,
        'granularity': granularity,
        'hours': hours
    })


@app.route('/api/stats/countries')
@login_required
def get_country_stats():
    """Get statistics by country"""
    hours = int(request.args.get('hours', 24))

    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT
            country_code,
            country_name,
            COUNT(DISTINCT src_ip) as unique_ips,
            COUNT(*) as total_connections,
            SUM(bytes_recv + bytes_sent) as total_bytes
        FROM connections
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
              AND country_code != 'XX'
        GROUP BY country_code, country_name
        ORDER BY total_connections DESC
    ''', (hours,))

    countries = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify({
        'countries': countries,
        'count': len(countries)
    })


@app.route('/api/stats/summary')
@login_required
def get_summary_stats():
    """Get summary statistics"""
    hours = int(request.args.get('hours', 24))

    conn = get_db()
    c = conn.cursor()

    # Overall stats
    c.execute('''
        SELECT
            COUNT(DISTINCT src_ip) as total_unique_ips,
            COUNT(*) as total_connections,
            SUM(bytes_recv) as total_bytes_recv,
            SUM(bytes_sent) as total_bytes_sent,
            COUNT(DISTINCT country_code) as countries_count
        FROM connections
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
    ''', (hours,))

    summary = dict(c.fetchone())

    # Protocol breakdown
    c.execute('''
        SELECT protocol, COUNT(*) as count
        FROM connections
        WHERE timestamp > datetime('now', '-' || ? || ' hours')
        GROUP BY protocol
    ''', (hours,))

    summary['protocols'] = [dict(row) for row in c.fetchall()]

    conn.close()

    return jsonify(summary)


# ==================== WEBSOCKET ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('status', {'connected': True, 'timestamp': datetime.utcnow().isoformat()})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')


@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to real-time updates"""
    print(f'Client subscribed to updates: {request.sid}')
    emit('subscribed', {'status': 'success'})


def background_updater():
    """Background thread to push real-time updates"""
    print("🔄 Starting background updater thread...")

    while True:
        try:
            # Get current stats
            conn = get_db()
            c = conn.cursor()

            c.execute('''
                SELECT COUNT(DISTINCT src_ip) as active_ips
                FROM connections
                WHERE timestamp > datetime('now', '-30 seconds')
            ''')
            row = c.fetchone()
            active_ips = row['active_ips']

            c.execute('''
                SELECT SUM(bytes_recv) as bytes_in, SUM(bytes_sent) as bytes_out
                FROM connections
                WHERE timestamp > datetime('now', '-10 seconds')
            ''')
            row = c.fetchone()
            bytes_in = row['bytes_in'] or 0
            bytes_out = row['bytes_out'] or 0

            conn.close()

            # Broadcast to all connected clients
            socketio.emit('realtime_update', {
                'active_ips': active_ips,
                'bytes_in': bytes_in,
                'bytes_out': bytes_out,
                'timestamp': datetime.utcnow().isoformat()
            })

            time.sleep(2)  # Update every 2 seconds

        except Exception as e:
            print(f"❌ Error in background updater: {e}")
            time.sleep(5)


# ==================== MAIN ====================

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='VPN Monitoring Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--db', default='vpn_connections.db', help='Database path')

    args = parser.parse_args()

    global DB_PATH
    DB_PATH = args.db

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"⚠️  Warning: Database not found: {DB_PATH}")
        print("   Make sure the collector is running!")

    # Start background updater thread
    updater_thread = threading.Thread(target=background_updater, daemon=True)
    updater_thread.start()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         VPN MONITORING DASHBOARD - STARTED               ║
╠══════════════════════════════════════════════════════════╣
║  URL:      http://{args.host}:{args.port:<40} ║
║  Database: {args.db:43} ║
║  Login:    {ADMIN_USERNAME} / {ADMIN_PASSWORD:38} ║
║                                                          ║
║  ⚠️  CHANGE DEFAULT PASSWORD IN PRODUCTION!              ║
╚══════════════════════════════════════════════════════════╝
""")

    # Run server
    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        allow_unsafe_werkzeug=True  # For development only
    )


if __name__ == '__main__':
    main()
