"""
Historical Pattern Scanner
Scans current data to find 5 most recent patterns for testing
Just runs a scan and displays results with charts
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import json
from auto_scanner_bot import AutoScannerBot
from dataclasses import asdict
from interactive_charts import draw_interactive_chart

def scan_for_test_patterns():
    """
    Run current scan to find any existing patterns
    This will create charts and save to trade_signals.json for testing
    """
    print(f"\n{'='*60}")
    print(f"SCANNING FOR TEST PATTERNS")
    print(f"Running full scan on all markets...")
    print(f"{'='*60}\n")

    # Create bot instance
    bot = AutoScannerBot(initial_balance=1000.0)

    # Run a full scan
    new_signals = bot.scan_all_markets()

    if new_signals:
        print(f"\n{'='*60}")
        print(f"✓ Found {len(new_signals)} patterns with charts!")
        print(f"{'='*60}\n")

        print("Patterns found:")
        for signal in new_signals:
            print(f"  • {signal.pattern_type} - {signal.market} "
                  f"({signal.timeframe}) R:R={signal.risk_reward:.1f}")
            print(f"    Entry: ${signal.entry:.2f} | Stop: ${signal.stop:.2f} | "
                  f"Target: ${signal.target:.2f}")
            print(f"    Chart: {signal.chart_path}")

        print(f"\nAll signals saved to: trade_signals.json")
        print(f"Charts saved to: static/charts/")
        print(f"\nView dashboard at: http://localhost:5000")

        return new_signals
    else:
        print("\n{'='*60}")
        print("No patterns found in current market conditions")
        print("This is normal - patterns are quite rare!")
        print("{'='*60}")
        print("\nOptions:")
        print("1. Wait for hourly automated scans")
        print("2. Run this script again later")
        print("3. Click 'Scan Now' button in dashboard")
        print("4. Wait for markets to develop patterns")

        # Create dummy test signals for UI testing
        print("\nCreating dummy test signals for UI testing...")
        create_dummy_signals(bot)

        return []

def create_dummy_signals(bot):
    """Create some dummy signals just for testing the UI"""
    from auto_scanner_bot import TradeSignal

    dummy_signals = [
        TradeSignal(
            timestamp=datetime.now().isoformat(),
            pattern_type='ICI',
            market='BTC-USD',
            timeframe='1d',
            entry=45000.0,
            stop=44000.0,
            target=48000.0,
            risk_reward=3.0,
            chart_path='',
            status='open'
        ),
        TradeSignal(
            timestamp=datetime.now().isoformat(),
            pattern_type='Momentum',
            market='SPY',
            timeframe='1h',
            entry=450.0,
            stop=448.0,
            target=456.0,
            risk_reward=3.0,
            chart_path='',
            status='open'
        ),
        TradeSignal(
            timestamp=datetime.now().isoformat(),
            pattern_type='Force',
            market='GLD',
            timeframe='1d',
            entry=185.0,
            stop=183.0,
            target=191.0,
            risk_reward=3.0,
            chart_path='',
            status='open'
        )
    ]

    # Draw interactive charts for dummy signals and update with realistic prices
    for signal in dummy_signals:
        setup = {
            'entry': signal.entry,
            'stop': signal.stop,
            'target': signal.target,
            'risk_reward': signal.risk_reward
        }
        chart_path, trade_rationale = draw_interactive_chart(signal.market, signal.timeframe,
                                                             setup, signal.pattern_type,
                                                             bot.charts_dir)

        # Update signal with realistic prices from chart
        signal.entry = setup['entry']
        signal.stop = setup['stop']
        signal.target = setup['target']
        signal.risk_reward = setup['risk_reward']
        signal.chart_path = chart_path
        signal.trade_rationale = trade_rationale

    # Save to file
    with open('trade_signals.json', 'w') as f:
        json.dump([asdict(s) for s in dummy_signals], f, indent=2)

    print("✓ Created 3 dummy test signals with charts")
    print("  These are for UI testing only - not real patterns")
    print("\nView them at: http://localhost:5000")

if __name__ == '__main__':
    scan_for_test_patterns()
