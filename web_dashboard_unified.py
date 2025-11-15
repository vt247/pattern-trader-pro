"""
Unified Dashboard with Built-in Scanner
Runs scanner in background thread, serves web dashboard
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import os
from datetime import datetime
import threading
import time
from auto_scanner_bot import AutoScannerBot

app = Flask(__name__)

# Global bot instance
scanner_bot = None
scanner_thread = None

def run_scanner():
    """Run scanner in background thread"""
    global scanner_bot
    scanner_bot = AutoScannerBot(initial_balance=1000.0)

    print("Scanner bot started in background")

    while True:
        try:
            scanner_bot.run_hourly_scan()
            print(f"Next scan in 60 minutes...")
            time.sleep(3600)  # 1 hour
        except Exception as e:
            print(f"Scanner error: {e}")
            time.sleep(300)  # Wait 5 min on error

def start_background_scanner():
    """Start scanner in background thread"""
    global scanner_thread
    scanner_thread = threading.Thread(target=run_scanner, daemon=True)
    scanner_thread.start()
    print("Background scanner thread started")

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard_live.html')

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    # Load signals
    signals = []
    if os.path.exists('trade_signals.json'):
        try:
            with open('trade_signals.json', 'r') as f:
                signals = json.load(f)
        except:
            pass

    # Load account state
    account = {
        'balance': 1000,
        'initial_balance': 1000,
        'equity': 1000
    }
    if os.path.exists('account_state.json'):
        try:
            with open('account_state.json', 'r') as f:
                account = json.load(f)
        except:
            pass

    # Calculate stats
    open_signals = [s for s in signals if s['status'] == 'open']
    closed_signals = [s for s in signals if s['status'] != 'open']

    wins = len([s for s in closed_signals if s.get('pnl_r', 0) > 0])
    losses = len([s for s in closed_signals if s.get('pnl_r', 0) < 0])
    win_rate = (wins / len(closed_signals) * 100) if closed_signals else 0

    total_r = sum([s.get('pnl_r', 0) for s in closed_signals])
    total_pnl = account['balance'] - account['initial_balance']
    total_pnl_pct = (total_pnl / account['initial_balance'] * 100) if account['initial_balance'] > 0 else 0

    # Sort signals by timestamp (newest first)
    signals.sort(key=lambda x: x['timestamp'], reverse=True)

    return jsonify({
        'status': 'live',
        'account': {
            'balance': account['balance'],
            'equity': account.get('equity', account['balance']),
            'initial_balance': account['initial_balance'],
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct
        },
        'stats': {
            'total_signals': len(signals),
            'open_positions': len(open_signals),
            'closed_positions': len(closed_signals),
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_r': total_r
        },
        'signals': signals[:50]  # Latest 50 signals
    })

@app.route('/charts/<path:filename>')
def serve_chart(filename):
    """Serve chart images"""
    return send_from_directory('static/charts', filename)

# Start scanner when module is imported (works with gunicorn)
start_background_scanner()

if __name__ == '__main__':
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
