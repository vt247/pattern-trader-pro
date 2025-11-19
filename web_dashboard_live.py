"""
Live Trading Dashboard
Shows all trade signals with charts and results
"""

from flask import Flask, render_template, jsonify, send_from_directory, request
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Import the live chart generator and trade outcome checker
from interactive_charts import generate_live_chart, check_trade_outcome
import yfinance as yf
import pandas as pd

# Scanner state
scanner_state = {
    'scanning': False,
    'last_scan': None,
    'scan_count': 0
}

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
        'scanning': scanner_state['scanning'],
        'last_scan': scanner_state['last_scan'],
        'scan_count': scanner_state['scan_count'],
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

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Manually trigger a scan"""
    if scanner_state['scanning']:
        return jsonify({'error': 'Scan already in progress'}), 400

    # Run scan in background thread
    def run_scan():
        scanner_state['scanning'] = True
        try:
            from auto_scanner_bot import AutoScannerBot
            bot = AutoScannerBot(initial_balance=1000.0)
            bot.run_hourly_scan()
            scanner_state['last_scan'] = datetime.now().isoformat()
            scanner_state['scan_count'] += 1
        except Exception as e:
            print(f"Scan error: {e}")
        finally:
            scanner_state['scanning'] = False

    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

    return jsonify({'message': 'Scan started', 'scanning': True})

@app.route('/api/analyze', methods=['POST'])
def analyze_trades():
    """Run AI analysis on all trades"""
    try:
        from trade_analyzer import analyze_trades, load_trades, save_analysis
        trades = load_trades()
        analysis = analyze_trades(trades)
        save_analysis(analysis)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/charts/<path:filename>')
def serve_chart(filename):
    """Serve chart images"""
    return send_from_directory('static/charts', filename)


@app.route('/api/live-chart')
def live_chart():
    """Generate a live chart with current market data"""
    # Get parameters from query string
    symbol = request.args.get('symbol', '')
    timeframe = request.args.get('timeframe', '1d')
    entry = float(request.args.get('entry', 0))
    stop = float(request.args.get('stop', 0))
    target = float(request.args.get('target', 0))
    pattern_type = request.args.get('pattern', 'Unknown')
    timestamp = request.args.get('timestamp', '')
    risk_reward = float(request.args.get('rr', 3.0))

    if not symbol or entry == 0:
        return '<p>Invalid parameters</p>', 400

    # Generate the live chart HTML
    chart_html = generate_live_chart(
        symbol=symbol,
        timeframe=timeframe,
        entry=entry,
        stop=stop,
        target=target,
        pattern_type=pattern_type,
        trade_timestamp=timestamp,
        risk_reward=risk_reward
    )

    # Return full HTML page with the chart
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{pattern_type} - {symbol} Live Chart</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #1a1a1a;
                overflow: hidden;
            }}
        </style>
    </head>
    <body>
        {chart_html}
    </body>
    </html>
    '''


@app.route('/api/trade-status')
def trade_status():
    """Check current trade status (open/sl_hit/tp_hit) using live data"""
    symbol = request.args.get('symbol', '')
    timeframe = request.args.get('timeframe', '1d')
    entry = float(request.args.get('entry', 0))
    stop = float(request.args.get('stop', 0))
    target = float(request.args.get('target', 0))
    timestamp = request.args.get('timestamp', '')
    risk_reward = float(request.args.get('rr', 3.0))

    if not symbol or entry == 0:
        return jsonify({'error': 'Invalid parameters'}), 400

    try:
        # Parse trade start time
        trade_start_time = pd.to_datetime(timestamp) if timestamp else None

        # Calculate period
        if trade_start_time:
            days_since_trade = (datetime.now() - trade_start_time.to_pydatetime().replace(tzinfo=None)).days
        else:
            days_since_trade = 7

        if timeframe == '1d':
            period = f'{max(30 + days_since_trade, 60)}d'
        elif timeframe == '1h':
            period = f'{max(7 + days_since_trade, 14)}d'
        else:
            period = '30d'

        # Fetch data
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)

        if df.empty:
            return jsonify({
                'status': 'unknown',
                'message': 'Unable to fetch market data',
                'current_price': None
            })

        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # Check outcome
        outcome, hit_price, hit_time, _ = check_trade_outcome(
            df, entry, stop, target, trade_start_time
        )

        current_price = float(df['Close'].iloc[-1])
        is_long = target > entry

        # Calculate unrealized P&L
        if is_long:
            unrealized_r = (current_price - entry) / abs(entry - stop)
        else:
            unrealized_r = (entry - current_price) / abs(entry - stop)

        # Determine P&L based on outcome
        if outcome == 'tp_hit':
            pnl_r = risk_reward
        elif outcome == 'sl_hit':
            pnl_r = -1.0
        else:
            pnl_r = unrealized_r

        return jsonify({
            'status': outcome,
            'current_price': current_price,
            'pnl_r': round(pnl_r, 2),
            'hit_time': hit_time.isoformat() if hit_time else None
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'current_price': None
        })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
