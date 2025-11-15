"""
Complete Backtest System
Backtests all 1,772 valid setups across Bitcoin, S&P 500, and Gold
Simulates actual trading according to pattern rules
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict
import time

@dataclass
class BacktestResult:
    """Result of a single backtested trade"""
    original_date: datetime
    pattern: str
    market: str
    timeframe: str
    direction: str
    entry: float
    stop: float
    target: float
    expected_rr: float

    # Backtest results
    exit_price: float
    exit_reason: str  # 'target', 'stop', 'partial'
    pnl_r: float  # P&L in R multiples
    pnl_pct: float  # P&L in percentage
    actual_rr: float  # Actual R:R achieved
    win: bool
    bars_held: int

    # Additional metrics
    max_favorable: float  # Best price reached
    max_adverse: float  # Worst price reached

class Backtester:
    """Backtests trading setups using historical data"""

    def __init__(self):
        self.data_cache = {}  # Cache downloaded data

    def get_historical_data(self, symbol: str, start_date: datetime,
                           interval: str = '1h', days_after: int = 30):
        """Get historical data for backtesting"""
        cache_key = f"{symbol}_{interval}_{start_date.date()}"

        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        # Download data
        end_date = start_date + timedelta(days=days_after)

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)

            if df.empty:
                return None

            df.reset_index(inplace=True)
            if 'Datetime' in df.columns:
                df.rename(columns={'Datetime': 'Date'}, inplace=True)

            self.data_cache[cache_key] = df
            return df

        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
            return None

    def backtest_trade(self, setup: Dict, symbol: str, interval: str = '1h') -> BacktestResult:
        """Backtest a single trade setup"""

        # Parse setup details
        entry_date = pd.to_datetime(setup['Date'])
        entry = float(setup['Entry'])
        stop = float(setup['Stop'])
        target = float(setup['Target'])
        pattern = setup['Pattern']
        market = symbol
        timeframe = setup['Timeframe']

        # Determine direction
        if 'Direction' in setup:
            direction = setup['Direction']
        else:
            # For FOUS patterns, infer from entry/stop
            direction = 'LONG' if target > entry else 'SHORT'

        # Handle different R:R column names
        if 'R:R' in setup:
            expected_rr = float(setup['R:R'])
        elif 'Risk_Reward' in setup:
            expected_rr = float(setup['Risk_Reward'])
        else:
            expected_rr = 0.0

        # Get historical data starting from entry
        df = self.get_historical_data(symbol, entry_date, interval=interval, days_after=60)

        if df is None or len(df) < 2:
            # Can't backtest - return neutral result
            return BacktestResult(
                original_date=entry_date,
                pattern=pattern,
                market=market,
                timeframe=timeframe,
                direction=direction,
                entry=entry,
                stop=stop,
                target=target,
                expected_rr=expected_rr,
                exit_price=entry,
                exit_reason='no_data',
                pnl_r=0.0,
                pnl_pct=0.0,
                actual_rr=0.0,
                win=False,
                bars_held=0,
                max_favorable=entry,
                max_adverse=entry
            )

        # Find entry bar (first bar after setup date)
        df = df[df['Date'] >= entry_date].reset_index(drop=True)

        if len(df) < 1:
            # No data after entry
            return BacktestResult(
                original_date=entry_date,
                pattern=pattern,
                market=market,
                timeframe=timeframe,
                direction=direction,
                entry=entry,
                stop=stop,
                target=target,
                expected_rr=expected_rr,
                exit_price=entry,
                exit_reason='no_data',
                pnl_r=0.0,
                pnl_pct=0.0,
                actual_rr=0.0,
                win=False,
                bars_held=0,
                max_favorable=entry,
                max_adverse=entry
            )

        # Simulate trade
        exit_price = entry
        exit_reason = 'timeout'
        bars_held = 0
        max_favorable = entry
        max_adverse = entry

        risk = abs(entry - stop)

        if direction == 'LONG':
            for idx, row in df.iterrows():
                bars_held = idx
                high = row['High']
                low = row['Low']
                close = row['Close']

                # Track max favorable/adverse
                if high > max_favorable:
                    max_favorable = high
                if low < max_adverse:
                    max_adverse = low

                # Check stop first (conservative)
                if low <= stop:
                    exit_price = stop
                    exit_reason = 'stop'
                    break

                # Check target
                if high >= target:
                    exit_price = target
                    exit_reason = 'target'
                    break

                # Timeout after 30 bars
                if idx >= 30:
                    exit_price = close
                    exit_reason = 'timeout'
                    break

        else:  # SHORT
            for idx, row in df.iterrows():
                bars_held = idx
                high = row['High']
                low = row['Low']
                close = row['Close']

                # Track max favorable/adverse
                if low < max_favorable:
                    max_favorable = low
                if high > max_adverse:
                    max_adverse = high

                # Check stop first (conservative)
                if high >= stop:
                    exit_price = stop
                    exit_reason = 'stop'
                    break

                # Check target
                if low <= target:
                    exit_price = target
                    exit_reason = 'target'
                    break

                # Timeout after 30 bars
                if idx >= 30:
                    exit_price = close
                    exit_reason = 'timeout'
                    break

        # Calculate P&L
        if direction == 'LONG':
            pnl_pct = ((exit_price - entry) / entry) * 100
            pnl_r = (exit_price - entry) / risk if risk > 0 else 0
        else:  # SHORT
            pnl_pct = ((entry - exit_price) / entry) * 100
            pnl_r = (entry - exit_price) / risk if risk > 0 else 0

        actual_rr = pnl_r if pnl_r > 0 else pnl_r  # Keep negative for losses
        win = pnl_r > 0

        return BacktestResult(
            original_date=entry_date,
            pattern=pattern,
            market=market,
            timeframe=timeframe,
            direction=direction,
            entry=entry,
            stop=stop,
            target=target,
            expected_rr=expected_rr,
            exit_price=exit_price,
            exit_reason=exit_reason,
            pnl_r=pnl_r,
            pnl_pct=pnl_pct,
            actual_rr=actual_rr,
            win=win,
            bars_held=bars_held,
            max_favorable=max_favorable,
            max_adverse=max_adverse
        )

def backtest_market(csv_file: str, market_name: str, symbol: str,
                   interval_map: Dict[str, str]) -> List[BacktestResult]:
    """Backtest all setups for a single market"""

    print(f"\n{'='*80}")
    print(f"BACKTESTING {market_name.upper()}")
    print(f"{'='*80}")

    # Load setups
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} valid setups from {csv_file}")

    backtester = Backtester()
    results = []

    total = len(df)
    for idx, row in df.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"Progress: {idx + 1}/{total} ({(idx + 1)/total*100:.1f}%)")

        # Get appropriate interval for timeframe
        timeframe = row['Timeframe']
        interval = interval_map.get(timeframe, '1h')

        result = backtester.backtest_trade(row.to_dict(), symbol, interval)
        results.append(result)

        # Rate limiting
        if (idx + 1) % 10 == 0:
            time.sleep(0.5)

    print(f"Completed: {len(results)} trades backtested")
    return results

def calculate_metrics(results: List[BacktestResult]) -> Dict:
    """Calculate performance metrics from backtest results"""

    if not results:
        return {}

    # Filter out no_data results
    valid_results = [r for r in results if r.exit_reason != 'no_data']

    if not valid_results:
        return {}

    total_trades = len(valid_results)
    wins = [r for r in valid_results if r.win]
    losses = [r for r in valid_results if not r.win]

    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    # R-multiples
    total_r = sum(r.pnl_r for r in valid_results)
    avg_r = total_r / total_trades if total_trades > 0 else 0

    avg_win_r = sum(r.pnl_r for r in wins) / win_count if win_count > 0 else 0
    avg_loss_r = sum(r.pnl_r for r in losses) / loss_count if loss_count > 0 else 0

    # Percentages
    total_pnl_pct = sum(r.pnl_pct for r in valid_results)
    avg_pnl_pct = total_pnl_pct / total_trades if total_trades > 0 else 0

    avg_win_pct = sum(r.pnl_pct for r in wins) / win_count if win_count > 0 else 0
    avg_loss_pct = sum(r.pnl_pct for r in losses) / loss_count if loss_count > 0 else 0

    # Profit factor
    gross_profit = sum(r.pnl_r for r in wins)
    gross_loss = abs(sum(r.pnl_r for r in losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    # Expectancy (average R per trade)
    expectancy = avg_r

    # Exit reasons
    target_hits = len([r for r in valid_results if r.exit_reason == 'target'])
    stop_hits = len([r for r in valid_results if r.exit_reason == 'stop'])
    timeouts = len([r for r in valid_results if r.exit_reason == 'timeout'])

    # Average bars held
    avg_bars = sum(r.bars_held for r in valid_results) / total_trades if total_trades > 0 else 0

    return {
        'total_trades': total_trades,
        'wins': win_count,
        'losses': loss_count,
        'win_rate': win_rate,
        'total_r': total_r,
        'avg_r': avg_r,
        'avg_win_r': avg_win_r,
        'avg_loss_r': avg_loss_r,
        'total_pnl_pct': total_pnl_pct,
        'avg_pnl_pct': avg_pnl_pct,
        'avg_win_pct': avg_win_pct,
        'avg_loss_pct': avg_loss_pct,
        'profit_factor': profit_factor,
        'expectancy': expectancy,
        'target_hits': target_hits,
        'stop_hits': stop_hits,
        'timeouts': timeouts,
        'avg_bars_held': avg_bars
    }

def export_backtest_results(results: List[BacktestResult], filename: str):
    """Export backtest results to CSV"""
    data = []
    for r in results:
        data.append({
            'Date': r.original_date,
            'Market': r.market,
            'Pattern': r.pattern,
            'Timeframe': r.timeframe,
            'Direction': r.direction,
            'Entry': r.entry,
            'Stop': r.stop,
            'Target': r.target,
            'Expected_RR': r.expected_rr,
            'Exit_Price': r.exit_price,
            'Exit_Reason': r.exit_reason,
            'PnL_R': r.pnl_r,
            'PnL_Pct': r.pnl_pct,
            'Actual_RR': r.actual_rr,
            'Win': r.win,
            'Bars_Held': r.bars_held,
            'Max_Favorable': r.max_favorable,
            'Max_Adverse': r.max_adverse
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Exported backtest results to: {filename}")

def print_metrics(metrics: Dict, market_name: str):
    """Print performance metrics"""
    print(f"\n{'='*80}")
    print(f"{market_name.upper()} BACKTEST RESULTS")
    print(f"{'='*80}")

    if not metrics:
        print("No valid trades to analyze")
        return

    print(f"\n--- TRADE STATISTICS ---")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Wins: {metrics['wins']}")
    print(f"Losses: {metrics['losses']}")
    print(f"Win Rate: {metrics['win_rate']:.2f}%")

    print(f"\n--- R-MULTIPLE ANALYSIS ---")
    print(f"Total R: {metrics['total_r']:.2f}R")
    print(f"Average R per Trade: {metrics['avg_r']:.2f}R")
    print(f"Average Win: {metrics['avg_win_r']:.2f}R")
    print(f"Average Loss: {metrics['avg_loss_r']:.2f}R")
    print(f"Expectancy: {metrics['expectancy']:.2f}R per trade")

    print(f"\n--- PERCENTAGE ANALYSIS ---")
    print(f"Total P&L: {metrics['total_pnl_pct']:.2f}%")
    print(f"Average P&L per Trade: {metrics['avg_pnl_pct']:.2f}%")
    print(f"Average Win: {metrics['avg_win_pct']:.2f}%")
    print(f"Average Loss: {metrics['avg_loss_pct']:.2f}%")

    print(f"\n--- PERFORMANCE METRICS ---")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Average Bars Held: {metrics['avg_bars_held']:.1f}")

    print(f"\n--- EXIT ANALYSIS ---")
    print(f"Target Hits: {metrics['target_hits']} ({metrics['target_hits']/metrics['total_trades']*100:.1f}%)")
    print(f"Stop Hits: {metrics['stop_hits']} ({metrics['stop_hits']/metrics['total_trades']*100:.1f}%)")
    print(f"Timeouts: {metrics['timeouts']} ({metrics['timeouts']/metrics['total_trades']*100:.1f}%)")

if __name__ == "__main__":
    print("="*80)
    print("COMPLETE BACKTEST - ALL MARKETS")
    print("Testing all 1,772 valid setups")
    print("="*80)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Interval mapping for different timeframes
    interval_map = {
        '1d': '1d',
        '4h': '1h',  # Use 1h data for 4h patterns
        '1h': '1h',
        '15m': '15m',
        '5m': '5m'
    }

    all_results = []
    all_metrics = {}

    # Backtest Bitcoin
    btc_ici_results = backtest_market(
        'bitcoin_ici_valid_20251115_222726.csv',
        'Bitcoin ICI',
        'BTC-USD',
        interval_map
    )

    btc_fous_results = backtest_market(
        'bitcoin_fous_valid_20251115_222726.csv',
        'Bitcoin FOUS',
        'BTC-USD',
        interval_map
    )

    btc_results = btc_ici_results + btc_fous_results
    btc_metrics = calculate_metrics(btc_results)
    print_metrics(btc_metrics, 'Bitcoin')
    all_results.extend(btc_results)
    all_metrics['Bitcoin'] = btc_metrics

    # Backtest S&P 500
    spy_ici_results = backtest_market(
        'extended_valid_all_tf_20251115_172701.csv',
        'S&P 500 ICI',
        'SPY',
        interval_map
    )

    spy_fous_results = backtest_market(
        'fous_patterns_valid_20251115_194743.csv',
        'S&P 500 FOUS',
        'SPY',
        interval_map
    )

    spy_results = spy_ici_results + spy_fous_results
    spy_metrics = calculate_metrics(spy_results)
    print_metrics(spy_metrics, 'S&P 500')
    all_results.extend(spy_results)
    all_metrics['S&P 500'] = spy_metrics

    # Backtest Gold
    gold_ici_results = backtest_market(
        'gold_ici_valid_20251115_223958.csv',
        'Gold ICI',
        'GLD',
        interval_map
    )

    gold_fous_results = backtest_market(
        'gold_fous_valid_20251115_223958.csv',
        'Gold FOUS',
        'GLD',
        interval_map
    )

    gold_results = gold_ici_results + gold_fous_results
    gold_metrics = calculate_metrics(gold_results)
    print_metrics(gold_metrics, 'Gold')
    all_results.extend(gold_results)
    all_metrics['Gold'] = gold_metrics

    # Combined metrics
    combined_metrics = calculate_metrics(all_results)
    print_metrics(combined_metrics, 'COMBINED ALL MARKETS')

    # Export all results
    export_backtest_results(all_results, f'backtest_all_markets_{timestamp}.csv')
    export_backtest_results(btc_results, f'backtest_bitcoin_{timestamp}.csv')
    export_backtest_results(spy_results, f'backtest_sp500_{timestamp}.csv')
    export_backtest_results(gold_results, f'backtest_gold_{timestamp}.csv')

    print("\n" + "="*80)
    print("BACKTEST COMPLETE!")
    print("="*80)
    print(f"\nBacktested {len(all_results)} total trades")
    print(f"Bitcoin: {len(btc_results)} trades")
    print(f"S&P 500: {len(spy_results)} trades")
    print(f"Gold: {len(gold_results)} trades")
