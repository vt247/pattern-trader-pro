"""
Simple Web Dashboard for PatternTrader Pro
No pandas dependency - production ready
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard_simple.html')

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    # Return demo data for Render deployment
    return jsonify({
        'status': 'live',
        'account': {
            'balance': 10000,
            'equity': 10000,
            'total_trades': 0,
            'open_positions': 0
        },
        'performance': {
            'total_pnl': 0,
            'win_rate': 0,
            'total_r': 0,
            'best_trade': 0,
            'worst_trade': 0
        },
        'equity_history': [
            {'date': '2025-11-15', 'equity': 10000}
        ],
        'positions': [],
        'recent_trades': [],
        'message': 'PatternTrader Pro - Ready for deployment'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
