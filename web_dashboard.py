"""
Web-based Paper Trading Dashboard
Real-time monitoring via browser at http://localhost:5000
"""

from flask import Flask, render_template, jsonify
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)

class DashboardData:
    """Load and process dashboard data"""

    def __init__(self):
        self.account_file = 'paper_account_history.json'
        self.trade_log_file = 'paper_trades_log.csv'

    def load_state(self):
        """Load current bot state"""
        if not os.path.exists(self.account_file):
            return None

        try:
            with open(self.account_file, 'r') as f:
                return json.load(f)
        except:
            return None

    def load_trades(self):
        """Load trade history"""
        if not os.path.exists(self.trade_log_file):
            return pd.DataFrame()

        try:
            return pd.read_csv(self.trade_log_file)
        except:
            return pd.DataFrame()

    def get_dashboard_data(self):
        """Get all data for dashboard"""
        state = self.load_state()

        if state is None:
            return {
                'status': 'no_data',
                'message': 'No paper trading data found. Start the bot first.'
            }

        account = state['account']
        positions = state['positions']

        # Open positions
        open_positions = [p for p in positions if p['status'] == 'open']

        # Trade history
        df_trades = self.load_trades()

        # Calculate metrics
        metrics = {}
        if not df_trades.empty:
            total_trades = len(df_trades)
            wins = len(df_trades[df_trades['PnL_R'] > 0])
            losses = total_trades - wins
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

            metrics = {
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'total_r': round(df_trades['PnL_R'].sum(), 2),
                'avg_r': round(df_trades['PnL_R'].mean(), 2),
                'avg_win_r': round(df_trades[df_trades['PnL_R'] > 0]['PnL_R'].mean(), 2) if wins > 0 else 0,
                'avg_loss_r': round(df_trades[df_trades['PnL_R'] <= 0]['PnL_R'].mean(), 2) if losses > 0 else 0,
                'profit_factor': 0
            }

            # Profit factor
            gross_profit = df_trades[df_trades['PnL_R'] > 0]['PnL_R'].sum()
            gross_loss = abs(df_trades[df_trades['PnL_R'] <= 0]['PnL_R'].sum())
            if gross_loss > 0:
                metrics['profit_factor'] = round(gross_profit / gross_loss, 2)

            # Pattern stats
            pattern_stats = df_trades.groupby('Pattern').agg({
                'PnL_R': ['count', 'sum', 'mean']
            }).round(2).to_dict()

            # Market stats
            market_stats = df_trades.groupby('Market').agg({
                'PnL_R': ['count', 'sum', 'mean']
            }).round(2).to_dict()

            # Equity curve
            starting_balance = account['starting_balance']
            risk_amount = starting_balance * account['risk_per_trade']
            df_trades['PnL_Dollars'] = df_trades['PnL_R'] * risk_amount
            df_trades['Cumulative_PnL'] = df_trades['PnL_Dollars'].cumsum()
            df_trades['Equity'] = starting_balance + df_trades['Cumulative_PnL']

            equity_curve = df_trades[['Exit_Date', 'Equity']].to_dict('records')

            # Recent trades
            recent_trades = df_trades.tail(10).to_dict('records')
        else:
            pattern_stats = {}
            market_stats = {}
            equity_curve = []
            recent_trades = []

        # Account data
        starting_balance = account['starting_balance']
        current_balance = account['current_balance']
        total_pnl = current_balance - starting_balance
        total_pnl_pct = (total_pnl / starting_balance * 100) if starting_balance > 0 else 0

        return {
            'status': 'ok',
            'account': {
                'starting_balance': starting_balance,
                'current_balance': round(current_balance, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_pct': round(total_pnl_pct, 2),
                'risk_per_trade': account['risk_per_trade'] * 100,
                'total_trades': account['total_trades'],
                'open_positions': account['open_positions'],
                'closed_positions': account['closed_positions']
            },
            'open_positions': open_positions,
            'metrics': metrics,
            'pattern_stats': pattern_stats,
            'market_stats': market_stats,
            'equity_curve': equity_curve,
            'recent_trades': recent_trades,
            'last_update': state.get('last_update', 'Unknown')
        }

dashboard_data = DashboardData()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint for dashboard data"""
    data = dashboard_data.get_dashboard_data()
    return jsonify(data)

@app.route('/api/refresh')
def refresh():
    """Force refresh data"""
    data = dashboard_data.get_dashboard_data()
    return jsonify(data)

if __name__ == '__main__':
    print("="*80)
    print("PAPER TRADING WEB DASHBOARD")
    print("="*80)
    print("\nStarting web server...")
    print("\n🌐 Open your browser and go to:")
    print("\n    http://127.0.0.1:5000")
    print("    or")
    print("    http://localhost:5000")
    print("\n📊 Dashboard will show:")
    print("  - Real-time account balance")
    print("  - Open positions")
    print("  - Performance metrics")
    print("  - Equity curve chart")
    print("  - Recent trades")
    print("\n⚠️  Make sure paper_trading_bot.py is running in another terminal!")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("="*80 + "\n")

    # Use 127.0.0.1 instead of 0.0.0.0 for better compatibility
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
