"""
Automatic Paper Trading Bot
Scans all patterns across Bitcoin, S&P 500, and Gold
Opens paper trades automatically and manages exits
Tracks performance in real-time
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import time
import json
import os

# Import scanners
from ici_scanner import ICIScanner
from pattern_scanners import MomentumScanner
from fous_scanners import ForceScanner, RevivalScanner

@dataclass
class PaperPosition:
    """Paper trading position"""
    id: int
    entry_date: datetime
    market: str
    pattern: str
    timeframe: str
    direction: str
    entry_price: float
    stop_price: float
    target_price: float
    size: float  # Position size in R
    status: str  # 'open', 'closed'

    # Exit info (when closed)
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None  # 'target', 'stop', 'manual'
    pnl_r: Optional[float] = None
    pnl_pct: Optional[float] = None
    bars_held: int = 0

    # Monitoring
    max_favorable: float = 0.0
    max_adverse: float = 0.0
    last_check: Optional[datetime] = None

@dataclass
class PaperAccount:
    """Paper trading account"""
    starting_balance: float
    current_balance: float
    equity: float  # Balance + open P&L
    total_trades: int = 0
    open_positions: int = 0
    closed_positions: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl_r: float = 0.0
    total_pnl_pct: float = 0.0
    risk_per_trade: float = 0.01  # 1% default

class PaperTradingBot:
    """Automated paper trading system"""

    def __init__(self, starting_balance: float = 10000, risk_per_trade: float = 0.01):
        self.account = PaperAccount(
            starting_balance=starting_balance,
            current_balance=starting_balance,
            equity=starting_balance,
            risk_per_trade=risk_per_trade
        )

        self.positions: List[PaperPosition] = []
        self.next_position_id = 1

        # Scanners
        self.ici_scanner = ICIScanner()
        self.momentum_scanner = MomentumScanner()
        self.force_scanner = ForceScanner()
        self.revival_scanner = RevivalScanner()

        # Markets to trade
        self.markets = {
            'BTC-USD': {'name': 'Bitcoin', 'timeframes': ['1h'], 'interval': '1h'},
            'SPY': {'name': 'S&P 500', 'timeframes': ['1h'], 'interval': '1h'},
            'GLD': {'name': 'Gold', 'timeframes': ['1h'], 'interval': '1h'}
        }

        # Settings
        self.max_positions = 10
        self.max_positions_per_market = 3
        self.scan_interval_minutes = 60  # Scan every hour for 1H patterns

        # Trade log
        self.trade_log_file = 'paper_trades_log.csv'
        self.account_log_file = 'paper_account_history.json'

        # Load existing positions if any
        self.load_state()

        print("="*80)
        print("PAPER TRADING BOT INITIALIZED")
        print("="*80)
        print(f"Starting Balance: ${self.account.starting_balance:,.2f}")
        print(f"Risk per Trade: {self.account.risk_per_trade*100:.1f}%")
        print(f"Max Positions: {self.max_positions}")
        print(f"Markets: {', '.join([m['name'] for m in self.markets.values()])}")
        print("="*80)

    def get_latest_data(self, symbol: str, interval: str = '1h',
                       bars: int = 100) -> Optional[pd.DataFrame]:
        """Get latest market data"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='5d', interval=interval)

            if df.empty:
                return None

            df.reset_index(inplace=True)
            if 'Datetime' in df.columns:
                df.rename(columns={'Datetime': 'Date'}, inplace=True)

            return df.tail(bars)

        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None

    def scan_for_setups(self) -> List[Dict]:
        """Scan all markets for new setups"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning for setups...")

        new_setups = []

        for symbol, config in self.markets.items():
            # Check position limit per market
            open_in_market = len([p for p in self.positions
                                 if p.market == symbol and p.status == 'open'])
            if open_in_market >= self.max_positions_per_market:
                print(f"  {config['name']}: Max positions reached ({open_in_market}/{self.max_positions_per_market})")
                continue

            # Get data
            df = self.get_latest_data(symbol, config['interval'])
            if df is None or len(df) < 50:
                print(f"  {config['name']}: Insufficient data")
                continue

            # Scan ICI
            ici_setups = self.ici_scanner.scan(df, timeframe=config['interval'])
            valid_ici = [s for s in ici_setups if s.valid]

            # Scan Momentum (1h only)
            momentum_setups = []
            if config['interval'] == '1h':
                momentum_setups = self.momentum_scanner.scan(df, timeframe='1h')
                valid_ici.extend([s for s in momentum_setups if s.valid])

            # Scan Force
            force_setups = self.force_scanner.scan(df, timeframe=config['interval'])
            valid_force = [s for s in force_setups if s.valid]

            # Scan Revival
            revival_setups = self.revival_scanner.scan(df, timeframe=config['interval'])
            valid_revival = [s for s in revival_setups if s.valid]

            # Get most recent setup (last bar)
            all_valid = valid_ici + valid_force + valid_revival
            if all_valid:
                # Take only the latest setup (most recent date)
                latest = max(all_valid, key=lambda s: s.date)

                # Check if we already have this setup open
                already_open = any(
                    p.market == symbol and
                    p.pattern == latest.pattern_type and
                    abs((p.entry_date - latest.date).total_seconds()) < 3600 and
                    p.status == 'open'
                    for p in self.positions
                )

                if not already_open:
                    new_setups.append({
                        'market': symbol,
                        'market_name': config['name'],
                        'setup': latest
                    })
                    print(f"  {config['name']}: Found {latest.pattern_type} setup!")

        print(f"Total new setups found: {len(new_setups)}")
        return new_setups

    def open_position(self, market: str, market_name: str, setup) -> Optional[PaperPosition]:
        """Open a new paper position"""

        # Check max positions
        open_positions = len([p for p in self.positions if p.status == 'open'])
        if open_positions >= self.max_positions:
            print(f"  Max positions reached ({open_positions}/{self.max_positions})")
            return None

        # Calculate position size
        risk_amount = self.account.current_balance * self.account.risk_per_trade

        # Create position
        position = PaperPosition(
            id=self.next_position_id,
            entry_date=datetime.now(),
            market=market,
            pattern=setup.pattern_type,
            timeframe=setup.timeframe,
            direction='LONG' if setup.is_bullish else 'SHORT',
            entry_price=setup.entry,
            stop_price=setup.stop,
            target_price=setup.target,
            size=1.0,  # 1R position
            status='open',
            max_favorable=setup.entry,
            max_adverse=setup.entry,
            last_check=datetime.now()
        )

        self.positions.append(position)
        self.next_position_id += 1
        self.account.open_positions += 1
        self.account.total_trades += 1

        print(f"\n{'='*80}")
        print(f"POSITION OPENED #{position.id}")
        print(f"{'='*80}")
        print(f"Market: {market_name} ({market})")
        print(f"Pattern: {position.pattern}")
        print(f"Direction: {position.direction}")
        print(f"Entry: ${position.entry_price:,.2f}")
        print(f"Stop: ${position.stop_price:,.2f}")
        print(f"Target: ${position.target_price:,.2f}")
        print(f"Risk: ${risk_amount:.2f} ({self.account.risk_per_trade*100:.1f}%)")
        print(f"Expected R:R: {setup.risk_reward:.2f}")
        print(f"{'='*80}")

        self.save_state()
        return position

    def check_exits(self):
        """Check all open positions for exits"""
        open_positions = [p for p in self.positions if p.status == 'open']

        if not open_positions:
            return

        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking {len(open_positions)} open positions...")

        for position in open_positions:
            # Get current price
            df = self.get_latest_data(position.market, '1m', bars=1)
            if df is None or len(df) == 0:
                print(f"  Position #{position.id}: No data available")
                continue

            current_price = df['Close'].iloc[-1]
            current_high = df['High'].iloc[-1]
            current_low = df['Low'].iloc[-1]

            # Update max favorable/adverse
            if position.direction == 'LONG':
                if current_high > position.max_favorable:
                    position.max_favorable = current_high
                if current_low < position.max_adverse:
                    position.max_adverse = current_low
            else:  # SHORT
                if current_low < position.max_favorable:
                    position.max_favorable = current_low
                if current_high > position.max_adverse:
                    position.max_adverse = current_high

            # Check for exit
            exit_triggered = False
            exit_price = None
            exit_reason = None

            if position.direction == 'LONG':
                # Check stop
                if current_low <= position.stop_price:
                    exit_triggered = True
                    exit_price = position.stop_price
                    exit_reason = 'stop'
                # Check target
                elif current_high >= position.target_price:
                    exit_triggered = True
                    exit_price = position.target_price
                    exit_reason = 'target'

            else:  # SHORT
                # Check stop
                if current_high >= position.stop_price:
                    exit_triggered = True
                    exit_price = position.stop_price
                    exit_reason = 'stop'
                # Check target
                elif current_low <= position.target_price:
                    exit_triggered = True
                    exit_price = position.target_price
                    exit_reason = 'target'

            # Update bars held
            position.bars_held += 1
            position.last_check = datetime.now()

            # Close position if exit triggered
            if exit_triggered:
                self.close_position(position, exit_price, exit_reason)
            else:
                # Show current P&L
                if position.direction == 'LONG':
                    unrealized_pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                    risk = abs(position.entry_price - position.stop_price)
                    unrealized_pnl_r = (current_price - position.entry_price) / risk if risk > 0 else 0
                else:
                    unrealized_pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
                    risk = abs(position.entry_price - position.stop_price)
                    unrealized_pnl_r = (position.entry_price - current_price) / risk if risk > 0 else 0

                print(f"  Position #{position.id} ({position.market} {position.pattern}): "
                      f"${current_price:,.2f} | P&L: {unrealized_pnl_r:+.2f}R ({unrealized_pnl_pct:+.2f}%) | "
                      f"Bars: {position.bars_held}")

        self.save_state()

    def close_position(self, position: PaperPosition, exit_price: float, exit_reason: str):
        """Close a position"""
        position.exit_date = datetime.now()
        position.exit_price = exit_price
        position.exit_reason = exit_reason
        position.status = 'closed'

        # Calculate P&L
        risk = abs(position.entry_price - position.stop_price)

        if position.direction == 'LONG':
            position.pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
            position.pnl_r = (exit_price - position.entry_price) / risk if risk > 0 else 0
        else:  # SHORT
            position.pnl_pct = ((position.entry_price - exit_price) / position.entry_price) * 100
            position.pnl_r = (position.entry_price - exit_price) / risk if risk > 0 else 0

        # Update account
        risk_amount = self.account.starting_balance * self.account.risk_per_trade
        pnl_dollars = position.pnl_r * risk_amount

        self.account.current_balance += pnl_dollars
        self.account.equity = self.account.current_balance
        self.account.open_positions -= 1
        self.account.closed_positions += 1
        self.account.total_pnl_r += position.pnl_r
        self.account.total_pnl_pct += position.pnl_pct

        if position.pnl_r > 0:
            self.account.wins += 1
        else:
            self.account.losses += 1

        # Log
        print(f"\n{'='*80}")
        print(f"POSITION CLOSED #{position.id}")
        print(f"{'='*80}")
        print(f"Market: {position.market}")
        print(f"Pattern: {position.pattern}")
        print(f"Exit Reason: {exit_reason.upper()}")
        print(f"Entry: ${position.entry_price:,.2f} → Exit: ${exit_price:,.2f}")
        print(f"P&L: {position.pnl_r:+.2f}R ({position.pnl_pct:+.2f}%)")
        print(f"Dollars: ${pnl_dollars:+,.2f}")
        print(f"Bars Held: {position.bars_held}")
        print(f"New Balance: ${self.account.current_balance:,.2f}")
        print(f"{'='*80}")

        # Save to log
        self.log_trade(position)
        self.save_state()

    def log_trade(self, position: PaperPosition):
        """Log closed trade to CSV"""
        trade_data = {
            'ID': position.id,
            'Entry_Date': position.entry_date,
            'Exit_Date': position.exit_date,
            'Market': position.market,
            'Pattern': position.pattern,
            'Timeframe': position.timeframe,
            'Direction': position.direction,
            'Entry_Price': position.entry_price,
            'Stop_Price': position.stop_price,
            'Target_Price': position.target_price,
            'Exit_Price': position.exit_price,
            'Exit_Reason': position.exit_reason,
            'PnL_R': position.pnl_r,
            'PnL_Pct': position.pnl_pct,
            'Bars_Held': position.bars_held,
            'Max_Favorable': position.max_favorable,
            'Max_Adverse': position.max_adverse
        }

        df = pd.DataFrame([trade_data])

        # Append to existing log or create new
        if os.path.exists(self.trade_log_file):
            df.to_csv(self.trade_log_file, mode='a', header=False, index=False)
        else:
            df.to_csv(self.trade_log_file, index=False)

    def save_state(self):
        """Save current state to file"""
        state = {
            'account': asdict(self.account),
            'positions': [asdict(p) for p in self.positions],
            'next_position_id': self.next_position_id,
            'last_update': datetime.now().isoformat()
        }

        with open(self.account_log_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def load_state(self):
        """Load state from file"""
        if os.path.exists(self.account_log_file):
            try:
                with open(self.account_log_file, 'r') as f:
                    state = json.load(f)

                # Restore account
                self.account = PaperAccount(**state['account'])

                # Restore positions
                self.positions = []
                for p_dict in state['positions']:
                    # Convert date strings back to datetime
                    p_dict['entry_date'] = pd.to_datetime(p_dict['entry_date'])
                    if p_dict['exit_date']:
                        p_dict['exit_date'] = pd.to_datetime(p_dict['exit_date'])
                    if p_dict['last_check']:
                        p_dict['last_check'] = pd.to_datetime(p_dict['last_check'])

                    self.positions.append(PaperPosition(**p_dict))

                self.next_position_id = state['next_position_id']

                print(f"State loaded from {self.account_log_file}")
                print(f"Restored {len(self.positions)} positions")

            except Exception as e:
                print(f"Error loading state: {e}")

    def print_status(self):
        """Print current account status"""
        open_pos = [p for p in self.positions if p.status == 'open']
        closed_pos = [p for p in self.positions if p.status == 'closed']

        win_rate = (self.account.wins / self.account.closed_positions * 100) if self.account.closed_positions > 0 else 0
        avg_r = self.account.total_pnl_r / self.account.closed_positions if self.account.closed_positions > 0 else 0

        print(f"\n{'='*80}")
        print(f"PAPER TRADING ACCOUNT STATUS")
        print(f"{'='*80}")
        print(f"Balance: ${self.account.current_balance:,.2f} (Start: ${self.account.starting_balance:,.2f})")
        print(f"P&L: ${self.account.current_balance - self.account.starting_balance:+,.2f} "
              f"({(self.account.current_balance/self.account.starting_balance - 1)*100:+.2f}%)")
        print(f"Total Trades: {self.account.total_trades} "
              f"(Open: {self.account.open_positions}, Closed: {self.account.closed_positions})")
        print(f"Win Rate: {win_rate:.1f}% ({self.account.wins}W / {self.account.losses}L)")
        print(f"Total R: {self.account.total_pnl_r:+.2f}R (Avg: {avg_r:+.2f}R per trade)")
        print(f"{'='*80}")

        if open_pos:
            print(f"\nOpen Positions ({len(open_pos)}):")
            for p in open_pos:
                print(f"  #{p.id} {p.market} {p.pattern} {p.direction} @ ${p.entry_price:,.2f} | "
                      f"Target: ${p.target_price:,.2f} | Stop: ${p.stop_price:,.2f}")

    def run(self, duration_hours: Optional[int] = None):
        """Run paper trading bot"""
        print(f"\n{'='*80}")
        print(f"STARTING PAPER TRADING BOT")
        print(f"{'='*80}")
        print(f"Scan Interval: {self.scan_interval_minutes} minutes")
        if duration_hours:
            print(f"Duration: {duration_hours} hours")
        else:
            print(f"Duration: Continuous (Ctrl+C to stop)")
        print(f"{'='*80}")

        start_time = datetime.now()
        scan_count = 0

        try:
            while True:
                scan_count += 1

                # Check exits for open positions
                self.check_exits()

                # Scan for new setups
                new_setups = self.scan_for_setups()

                # Open new positions
                for setup_info in new_setups:
                    self.open_position(
                        setup_info['market'],
                        setup_info['market_name'],
                        setup_info['setup']
                    )

                # Print status
                self.print_status()

                # Check duration
                if duration_hours:
                    elapsed = (datetime.now() - start_time).total_seconds() / 3600
                    if elapsed >= duration_hours:
                        print(f"\nDuration reached ({duration_hours} hours). Stopping...")
                        break

                # Wait for next scan
                print(f"\nNext scan in {self.scan_interval_minutes} minutes...")
                time.sleep(self.scan_interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\nBot stopped by user (Ctrl+C)")

        finally:
            # Final status
            print(f"\n{'='*80}")
            print(f"PAPER TRADING SESSION ENDED")
            print(f"{'='*80}")
            print(f"Duration: {(datetime.now() - start_time).total_seconds() / 3600:.1f} hours")
            print(f"Total Scans: {scan_count}")
            self.print_status()

            # Close any open positions
            open_positions = [p for p in self.positions if p.status == 'open']
            if open_positions:
                print(f"\nClosing {len(open_positions)} open positions at market...")
                for position in open_positions:
                    df = self.get_latest_data(position.market, '1m', bars=1)
                    if df is not None and len(df) > 0:
                        current_price = df['Close'].iloc[-1]
                        self.close_position(position, current_price, 'manual')

            self.save_state()
            print(f"\nState saved to {self.account_log_file}")
            print(f"Trade log saved to {self.trade_log_file}")

if __name__ == "__main__":
    # Create bot with $10,000 starting balance and 1% risk per trade
    bot = PaperTradingBot(starting_balance=10000, risk_per_trade=0.01)

    # Run for 24 hours (or until Ctrl+C)
    # Set duration_hours=None for continuous running
    bot.run(duration_hours=24)
