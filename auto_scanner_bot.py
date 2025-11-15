"""
Automatic Pattern Scanner & Paper Trading Bot
Scans markets hourly, finds setups, paper trades them, and saves charts
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Import our scanners
from ici_scanner import ICIScanner
from pattern_scanners import MomentumScanner, WMScanner, HarmonicScanner
from fous_scanners import ForceScanner, SurvivalScanner, RevivalScanner, GoldScanner

@dataclass
class TradeSignal:
    """Trade signal with all details"""
    timestamp: str
    pattern_type: str
    market: str
    timeframe: str
    entry: float
    stop: float
    target: float
    risk_reward: float
    chart_path: str
    status: str = 'open'  # open, hit_target, hit_stop, timeout
    exit_price: float = 0.0
    exit_date: str = ''
    pnl_r: float = 0.0

class AutoScannerBot:
    """Automatic scanner that finds and trades setups"""

    def __init__(self, initial_balance: float = 1000.0):
        self.markets = {
            'BTC-USD': 'Bitcoin',
            'SPY': 'S&P 500',
            'GLD': 'Gold'
        }
        self.timeframes = ['1d', '1h']
        self.account_balance = initial_balance
        self.initial_balance = initial_balance
        self.risk_per_trade = 0.02  # 2% per trade
        self.max_positions = 10

        # Storage
        self.signals_file = 'trade_signals.json'
        self.charts_dir = 'static/charts'
        self.account_file = 'account_state.json'

        # Create directories
        os.makedirs(self.charts_dir, exist_ok=True)
        os.makedirs('static', exist_ok=True)

        # Load existing data
        self.signals = self.load_signals()
        self.load_account_state()

    def load_signals(self) -> List[TradeSignal]:
        """Load existing signals from file"""
        if os.path.exists(self.signals_file):
            try:
                with open(self.signals_file, 'r') as f:
                    data = json.load(f)
                    return [TradeSignal(**s) for s in data]
            except:
                return []
        return []

    def save_signals(self):
        """Save signals to file"""
        with open(self.signals_file, 'w') as f:
            json.dump([asdict(s) for s in self.signals], f, indent=2)

    def load_account_state(self):
        """Load account state"""
        if os.path.exists(self.account_file):
            try:
                with open(self.account_file, 'r') as f:
                    data = json.load(f)
                    self.account_balance = data.get('balance', self.initial_balance)
                    # Don't override initial_balance if already set
                    if 'initial_balance' not in data:
                        self.save_account_state()
            except:
                # Save initial state if loading fails
                self.save_account_state()
        else:
            # Create initial account state
            self.save_account_state()

    def save_account_state(self):
        """Save account state"""
        with open(self.account_file, 'w') as f:
            json.dump({
                'balance': self.account_balance,
                'initial_balance': self.initial_balance,
                'equity': self.account_balance,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)

    def draw_setup_chart(self, symbol: str, timeframe: str, setup: dict,
                        pattern_type: str) -> str:
        """Draw chart with setup markers and save as image"""
        try:
            # Get data
            period = '90d' if timeframe == '1d' else '7d'
            df = yf.download(symbol, period=period, interval=timeframe, progress=False)

            if df.empty:
                return ''

            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                           gridspec_kw={'height_ratios': [3, 1]})

            # Plot candlesticks
            colors = ['green' if c >= o else 'red'
                     for c, o in zip(df['Close'], df['Open'])]
            ax1.bar(df.index, df['High'] - df['Low'], bottom=df['Low'],
                   color=colors, alpha=0.3, width=0.6)
            ax1.bar(df.index, df['Close'] - df['Open'], bottom=df['Open'],
                   color=colors, alpha=0.8, width=0.6)

            # Mark entry, stop, target
            entry = setup.get('entry', 0)
            stop = setup.get('stop', 0)
            target = setup.get('target', 0)

            if entry > 0:
                ax1.axhline(y=entry, color='blue', linestyle='--', linewidth=2,
                           label=f'Entry: ${entry:.2f}')
                ax1.axhline(y=stop, color='red', linestyle='--', linewidth=2,
                           label=f'Stop: ${stop:.2f}')
                ax1.axhline(y=target, color='green', linestyle='--', linewidth=2,
                           label=f'Target: ${target:.2f}')

            # Add title and labels
            market_name = self.markets.get(symbol, symbol)
            ax1.set_title(f'{pattern_type} Setup - {market_name} ({timeframe})\n'
                         f'Entry: ${entry:.2f} | Stop: ${stop:.2f} | Target: ${target:.2f}',
                         fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price ($)', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)

            # Plot volume
            ax2.bar(df.index, df['Volume'], color=colors, alpha=0.5)
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.set_xlabel('Date', fontsize=12)
            ax2.grid(True, alpha=0.3)

            # Format x-axis
            if timeframe == '1d':
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            else:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

            plt.tight_layout()

            # Save chart
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            chart_filename = f'{pattern_type}_{symbol}_{timeframe}_{timestamp}.png'
            chart_path = os.path.join(self.charts_dir, chart_filename)
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close()

            return f'charts/{chart_filename}'

        except Exception as e:
            print(f"Error drawing chart: {e}")
            return ''

    def scan_market(self, symbol: str, timeframe: str) -> List[Dict]:
        """Scan one market/timeframe for all patterns"""
        setups = []

        try:
            print(f"  Scanning {symbol} {timeframe}...")

            # ICI Scanner
            scanner = ICIScanner(symbol, timeframe)
            ici_setups = scanner.find_all_setups()
            for setup in ici_setups:
                if setup.valid:
                    setups.append({
                        'pattern_type': 'ICI',
                        'entry': setup.entry,
                        'stop': setup.stop,
                        'target': setup.target,
                        'risk_reward': setup.risk_reward
                    })

            # Momentum Scanner
            mom_scanner = MomentumScanner(symbol, timeframe)
            mom_setups = mom_scanner.find_all_setups()
            for setup in mom_setups:
                if setup.valid:
                    setups.append({
                        'pattern_type': 'Momentum',
                        'entry': setup.entry,
                        'stop': setup.stop,
                        'target': setup.target,
                        'risk_reward': setup.risk_reward
                    })

            # FOUS Scanners
            force_scanner = ForceScanner(symbol, timeframe)
            force_setups = force_scanner.find_all_setups()
            for setup in force_setups:
                if setup.valid:
                    setups.append({
                        'pattern_type': 'Force',
                        'entry': setup.entry,
                        'stop': setup.stop,
                        'target': setup.target,
                        'risk_reward': setup.risk_reward
                    })

            revival_scanner = RevivalScanner(symbol, timeframe)
            revival_setups = revival_scanner.find_all_setups()
            for setup in revival_setups:
                if setup.valid:
                    setups.append({
                        'pattern_type': 'Revival',
                        'entry': setup.entry,
                        'stop': setup.stop,
                        'target': setup.target,
                        'risk_reward': setup.risk_reward
                    })

        except Exception as e:
            print(f"  Error scanning {symbol} {timeframe}: {e}")

        return setups

    def scan_all_markets(self):
        """Scan all markets and timeframes"""
        print(f"\n{'='*60}")
        print(f"SCANNING ALL MARKETS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        new_signals = []

        for symbol in self.markets:
            for timeframe in self.timeframes:
                setups = self.scan_market(symbol, timeframe)

                for setup in setups:
                    # Draw chart
                    chart_path = self.draw_setup_chart(symbol, timeframe, setup,
                                                       setup['pattern_type'])

                    # Create signal
                    signal = TradeSignal(
                        timestamp=datetime.now().isoformat(),
                        pattern_type=setup['pattern_type'],
                        market=symbol,
                        timeframe=timeframe,
                        entry=setup['entry'],
                        stop=setup['stop'],
                        target=setup['target'],
                        risk_reward=setup['risk_reward'],
                        chart_path=chart_path,
                        status='open'
                    )

                    new_signals.append(signal)
                    self.signals.append(signal)

                    print(f"  ✓ {setup['pattern_type']} setup found: "
                          f"{symbol} {timeframe} R:R={setup['risk_reward']:.1f}")

        if new_signals:
            self.save_signals()
            print(f"\n✓ Found {len(new_signals)} new setups")
        else:
            print("\n  No new setups found")

        return new_signals

    def update_open_positions(self):
        """Check and update all open positions"""
        print(f"\nUpdating open positions...")

        for signal in self.signals:
            if signal.status == 'open':
                self.check_position_exit(signal)

        self.save_signals()
        self.save_account_state()

    def check_position_exit(self, signal: TradeSignal):
        """Check if position should exit"""
        try:
            # Get current data
            df = yf.download(signal.market, period='7d',
                           interval=signal.timeframe, progress=False)

            if df.empty:
                return

            current_price = df['Close'].iloc[-1]
            is_long = signal.target > signal.entry

            # Check if target hit
            if is_long and current_price >= signal.target:
                signal.status = 'hit_target'
                signal.exit_price = signal.target
                signal.exit_date = datetime.now().isoformat()
                signal.pnl_r = signal.risk_reward
                self.account_balance += (self.account_balance * self.risk_per_trade * signal.risk_reward)
                print(f"  ✓ {signal.pattern_type} {signal.market} HIT TARGET! +{signal.risk_reward:.1f}R")

            elif not is_long and current_price <= signal.target:
                signal.status = 'hit_target'
                signal.exit_price = signal.target
                signal.exit_date = datetime.now().isoformat()
                signal.pnl_r = signal.risk_reward
                self.account_balance += (self.account_balance * self.risk_per_trade * signal.risk_reward)
                print(f"  ✓ {signal.pattern_type} {signal.market} HIT TARGET! +{signal.risk_reward:.1f}R")

            # Check if stop hit
            elif is_long and current_price <= signal.stop:
                signal.status = 'hit_stop'
                signal.exit_price = signal.stop
                signal.exit_date = datetime.now().isoformat()
                signal.pnl_r = -1.0
                self.account_balance -= (self.account_balance * self.risk_per_trade)
                print(f"  ✗ {signal.pattern_type} {signal.market} HIT STOP. -1.0R")

            elif not is_long and current_price >= signal.stop:
                signal.status = 'hit_stop'
                signal.exit_price = signal.stop
                signal.exit_date = datetime.now().isoformat()
                signal.pnl_r = -1.0
                self.account_balance -= (self.account_balance * self.risk_per_trade)
                print(f"  ✗ {signal.pattern_type} {signal.market} HIT STOP. -1.0R")

            # Check timeout (7 days for daily, 2 days for hourly)
            entry_time = datetime.fromisoformat(signal.timestamp)
            age = datetime.now() - entry_time
            timeout_days = 7 if signal.timeframe == '1d' else 2

            if age.days >= timeout_days:
                signal.status = 'timeout'
                signal.exit_price = current_price
                signal.exit_date = datetime.now().isoformat()

                # Calculate P&L
                if is_long:
                    pnl_pct = (current_price - signal.entry) / (signal.entry - signal.stop)
                else:
                    pnl_pct = (signal.entry - current_price) / (signal.stop - signal.entry)

                signal.pnl_r = pnl_pct
                self.account_balance += (self.account_balance * self.risk_per_trade * pnl_pct)
                print(f"  ⏱ {signal.pattern_type} {signal.market} TIMEOUT. {pnl_pct:+.2f}R")

        except Exception as e:
            print(f"  Error checking position: {e}")

    def run_hourly_scan(self):
        """Run one hourly scan cycle"""
        # Update existing positions
        self.update_open_positions()

        # Check if we can take new positions
        open_positions = len([s for s in self.signals if s.status == 'open'])

        if open_positions < self.max_positions:
            # Scan for new setups
            new_signals = self.scan_all_markets()
            print(f"\nAccount Balance: ${self.account_balance:.2f}")
            print(f"Open Positions: {open_positions}")
        else:
            print(f"\nMax positions reached ({self.max_positions}). Skipping scan.")

    def run_forever(self, scan_interval_minutes: int = 60):
        """Run continuous scanning loop"""
        print(f"\n{'='*60}")
        print(f"AUTO SCANNER BOT STARTED")
        print(f"Initial Balance: ${self.account_balance:.2f}")
        print(f"Scan Interval: {scan_interval_minutes} minutes")
        print(f"{'='*60}\n")

        while True:
            try:
                self.run_hourly_scan()

                print(f"\nNext scan in {scan_interval_minutes} minutes...")
                time.sleep(scan_interval_minutes * 60)

            except KeyboardInterrupt:
                print("\n\nBot stopped by user")
                break
            except Exception as e:
                print(f"\nError in main loop: {e}")
                print("Retrying in 5 minutes...")
                time.sleep(300)

if __name__ == '__main__':
    bot = AutoScannerBot()
    bot.run_forever(scan_interval_minutes=60)
