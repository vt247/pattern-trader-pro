"""
Paper Trading Dashboard
Real-time monitoring and visualization of paper trading bot
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List

class PaperTradingDashboard:
    """Dashboard for monitoring paper trading performance"""

    def __init__(self):
        self.account_file = 'paper_account_history.json'
        self.trade_log_file = 'paper_trades_log.csv'

    def load_account_state(self) -> Dict:
        """Load current account state"""
        if not os.path.exists(self.account_file):
            return None

        with open(self.account_file, 'r') as f:
            return json.load(f)

    def load_trade_history(self) -> pd.DataFrame:
        """Load trade history"""
        if not os.path.exists(self.trade_log_file):
            return pd.DataFrame()

        return pd.read_csv(self.trade_log_file)

    def calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        if df.empty:
            return {}

        total_trades = len(df)
        wins = len(df[df['PnL_R'] > 0])
        losses = len(df[df['PnL_R'] <= 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        total_r = df['PnL_R'].sum()
        avg_r = df['PnL_R'].mean()

        winning_trades = df[df['PnL_R'] > 0]
        losing_trades = df[df['PnL_R'] <= 0]

        avg_win_r = winning_trades['PnL_R'].mean() if len(winning_trades) > 0 else 0
        avg_loss_r = losing_trades['PnL_R'].mean() if len(losing_trades) > 0 else 0

        gross_profit = winning_trades['PnL_R'].sum()
        gross_loss = abs(losing_trades['PnL_R'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # By pattern
        pattern_stats = df.groupby('Pattern').agg({
            'PnL_R': ['count', 'sum', 'mean']
        }).round(2)

        # By market
        market_stats = df.groupby('Market').agg({
            'PnL_R': ['count', 'sum', 'mean']
        }).round(2)

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_r': total_r,
            'avg_r': avg_r,
            'avg_win_r': avg_win_r,
            'avg_loss_r': avg_loss_r,
            'profit_factor': profit_factor,
            'pattern_stats': pattern_stats,
            'market_stats': market_stats
        }

    def print_dashboard(self):
        """Print full dashboard"""
        print("\n" + "="*80)
        print("PAPER TRADING DASHBOARD")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # Load data
        state = self.load_account_state()
        df_trades = self.load_trade_history()

        if state is None:
            print("\nNo paper trading data found.")
            print("Start the bot with: python paper_trading_bot.py")
            return

        # Account overview
        account = state['account']
        starting_balance = account['starting_balance']
        current_balance = account['current_balance']
        total_pnl = current_balance - starting_balance
        total_pnl_pct = (total_pnl / starting_balance * 100) if starting_balance > 0 else 0

        print("\n--- ACCOUNT OVERVIEW ---")
        print(f"Starting Balance: ${starting_balance:,.2f}")
        print(f"Current Balance: ${current_balance:,.2f}")
        print(f"Total P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")
        print(f"Risk per Trade: {account['risk_per_trade']*100:.1f}%")

        # Open positions
        positions = state['positions']
        open_positions = [p for p in positions if p['status'] == 'open']

        print(f"\n--- POSITIONS ---")
        print(f"Total Trades: {account['total_trades']}")
        print(f"Open: {account['open_positions']}")
        print(f"Closed: {account['closed_positions']}")

        if open_positions:
            print(f"\nOpen Positions:")
            for p in open_positions:
                print(f"  #{p['id']} {p['market']} {p['pattern']} {p['direction']} "
                      f"Entry: ${p['entry_price']:,.2f} | Target: ${p['target_price']:,.2f} | "
                      f"Stop: ${p['stop_price']:,.2f}")

        # Performance metrics
        if not df_trades.empty:
            metrics = self.calculate_metrics(df_trades)

            print("\n--- PERFORMANCE METRICS ---")
            print(f"Win Rate: {metrics['win_rate']:.2f}% ({metrics['wins']}W / {metrics['losses']}L)")
            print(f"Total R: {metrics['total_r']:+.2f}R")
            print(f"Average R: {metrics['avg_r']:+.2f}R per trade")
            print(f"Average Win: {metrics['avg_win_r']:+.2f}R")
            print(f"Average Loss: {metrics['avg_loss_r']:+.2f}R")
            print(f"Profit Factor: {metrics['profit_factor']:.2f}")

            # Pattern breakdown
            print("\n--- BY PATTERN ---")
            print(metrics['pattern_stats'])

            # Market breakdown
            print("\n--- BY MARKET ---")
            print(metrics['market_stats'])

            # Recent trades
            print("\n--- RECENT TRADES (Last 10) ---")
            recent = df_trades.tail(10)[['ID', 'Market', 'Pattern', 'Direction',
                                         'Exit_Reason', 'PnL_R', 'PnL_Pct', 'Bars_Held']]
            print(recent.to_string(index=False))

        # Last update
        last_update = state.get('last_update', 'Unknown')
        print(f"\n--- STATUS ---")
        print(f"Last Update: {last_update}")
        print(f"State File: {self.account_file}")
        print(f"Trade Log: {self.trade_log_file}")

        print("\n" + "="*80)

    def export_equity_curve(self, output_file: str = 'equity_curve.csv'):
        """Export equity curve"""
        df = self.load_trade_history()
        if df.empty:
            print("No trades to export")
            return

        state = self.load_account_state()
        if not state:
            print("No account state found")
            return

        starting_balance = state['account']['starting_balance']
        risk_per_trade = state['account']['risk_per_trade']
        risk_amount = starting_balance * risk_per_trade

        # Calculate cumulative equity
        df['PnL_Dollars'] = df['PnL_R'] * risk_amount
        df['Cumulative_PnL'] = df['PnL_Dollars'].cumsum()
        df['Equity'] = starting_balance + df['Cumulative_PnL']
        df['Equity_Pct'] = ((df['Equity'] / starting_balance) - 1) * 100

        # Save
        equity_df = df[['Exit_Date', 'Equity', 'Equity_Pct', 'Cumulative_PnL',
                       'PnL_R', 'Market', 'Pattern', 'Exit_Reason']]
        equity_df.to_csv(output_file, index=False)
        print(f"Equity curve exported to: {output_file}")

if __name__ == "__main__":
    dashboard = PaperTradingDashboard()
    dashboard.print_dashboard()
    dashboard.export_equity_curve()
