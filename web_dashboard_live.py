"""
Live Trading Dashboard
Shows all trade signals with charts and results
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__)

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
