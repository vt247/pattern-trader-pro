"""
Main S&P 500 Pattern Scanner

Scans for four pattern types:
1. ICI - Impulse-Correction-Impulse on daily/weekly/monthly
2. Momentum - ICI on 1h timeframe
3. W/M - Double top/bottom on weekly/monthly
4. Harmonic - W/M on daily timeframe
"""
import pandas as pd
from datetime import datetime
from typing import List
import os

from data_loader import load_spy_data, DataLoader
from ici_scanner import ICIScanner, ICISetup
from pattern_scanners import MomentumScanner, WMScanner, HarmonicScanner


class PatternScannerReport:
    """Generate reports and statistics for pattern scanning"""

    @staticmethod
    def print_statistics(all_setups: List[ICISetup]):
        """Print statistics for all patterns found"""
        if not all_setups:
            print("\nNo patterns found.")
            return

        print("\n" + "=" * 80)
        print("PATTERN SCANNING STATISTICS")
        print("=" * 80)

        # Overall statistics
        total = len(all_setups)
        valid = len([s for s in all_setups if s.valid])
        invalid = total - valid

        print(f"\nTotal setups found: {total}")
        print(f"Valid setups: {valid} ({valid/total*100:.1f}%)")
        print(f"Invalid setups: {invalid} ({invalid/total*100:.1f}%)")

        # Statistics by pattern type
        print("\n" + "-" * 80)
        print("BY PATTERN TYPE:")
        print("-" * 80)

        pattern_types = {}
        for setup in all_setups:
            ptype = setup.pattern_type
            if ptype not in pattern_types:
                pattern_types[ptype] = {'total': 0, 'valid': 0, 'bullish': 0, 'bearish': 0}
            pattern_types[ptype]['total'] += 1
            if setup.valid:
                pattern_types[ptype]['valid'] += 1
            if setup.is_bullish:
                pattern_types[ptype]['bullish'] += 1
            else:
                pattern_types[ptype]['bearish'] += 1

        for ptype, stats in pattern_types.items():
            print(f"\n{ptype}:")
            print(f"  Total: {stats['total']}")
            print(f"  Valid: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
            print(f"  Bullish: {stats['bullish']}")
            print(f"  Bearish: {stats['bearish']}")

        # Statistics by timeframe
        print("\n" + "-" * 80)
        print("BY TIMEFRAME:")
        print("-" * 80)

        timeframe_stats = {}
        for setup in all_setups:
            tf = setup.timeframe
            if tf not in timeframe_stats:
                timeframe_stats[tf] = {'total': 0, 'valid': 0}
            timeframe_stats[tf]['total'] += 1
            if setup.valid:
                timeframe_stats[tf]['valid'] += 1

        for tf, stats in timeframe_stats.items():
            print(f"\n{tf}:")
            print(f"  Total: {stats['total']}")
            print(f"  Valid: {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")

        # Risk/Reward statistics
        print("\n" + "-" * 80)
        print("RISK/REWARD ANALYSIS:")
        print("-" * 80)

        rr_ratios = [s.risk_reward for s in all_setups if s.valid]
        if rr_ratios:
            print(f"\nAverage R:R: {sum(rr_ratios)/len(rr_ratios):.2f}")
            print(f"Min R:R: {min(rr_ratios):.2f}")
            print(f"Max R:R: {max(rr_ratios):.2f}")

        # Indicator alignment
        print("\n" + "-" * 80)
        print("INDICATOR ALIGNMENT:")
        print("-" * 80)

        ema_aligned = len([s for s in all_setups if s.ema_aligned])
        macd_aligned = len([s for s in all_setups if s.macd_aligned])
        both_aligned = len([s for s in all_setups if s.ema_aligned and s.macd_aligned])

        print(f"\nEMA aligned: {ema_aligned} ({ema_aligned/total*100:.1f}%)")
        print(f"MACD aligned: {macd_aligned} ({macd_aligned/total*100:.1f}%)")
        print(f"Both aligned: {both_aligned} ({both_aligned/total*100:.1f}%)")

        print("\n" + "=" * 80)

    @staticmethod
    def export_to_csv(setups: List[ICISetup], filename: str = 'pattern_setups.csv'):
        """Export setups to CSV file"""
        if not setups:
            print("No setups to export.")
            return

        # Convert setups to list of dicts
        data = [setup.to_dict() for setup in setups]

        # Create DataFrame
        df = pd.DataFrame(data)

        # Sort by date
        df.sort_values('Date', inplace=True)

        # Export
        df.to_csv(filename, index=False)
        print(f"\nExported {len(setups)} setups to {filename}")

    @staticmethod
    def print_recent_setups(setups: List[ICISetup], count: int = 10):
        """Print most recent valid setups"""
        valid_setups = [s for s in setups if s.valid]
        if not valid_setups:
            print("\nNo valid setups found.")
            return

        # Sort by date (most recent first)
        sorted_setups = sorted(valid_setups, key=lambda s: s.date, reverse=True)
        recent = sorted_setups[:count]

        print("\n" + "=" * 80)
        print(f"MOST RECENT {count} VALID SETUPS:")
        print("=" * 80)

        for i, setup in enumerate(recent, 1):
            direction = "LONG" if setup.is_bullish else "SHORT"
            print(f"\n{i}. {setup.date.strftime('%Y-%m-%d')} - {setup.pattern_type} ({setup.timeframe}) - {direction}")
            print(f"   Entry: ${setup.entry:.2f} | Stop: ${setup.stop:.2f} | Target: ${setup.target:.2f}")
            print(f"   R:R: {setup.risk_reward:.2f} | Fib: {setup.correction_pct:.3f}")
            print(f"   EMA: {'✓' if setup.ema_aligned else '✗'} | MACD: {'✓' if setup.macd_aligned else '✗'}")

        print("\n" + "=" * 80)


def run_all_scanners(data_source: str = 'yfinance', csv_path: str = None):
    """
    Run all pattern scanners on SPY data

    Args:
        data_source: 'yfinance' or 'csv'
        csv_path: Path to CSV if using CSV source
    """
    print("=" * 80)
    print("S&P 500 PATTERN SCANNER")
    print("=" * 80)

    # Load data
    print("\n1. Loading SPY data...")
    df_daily = load_spy_data(source=data_source, filepath=csv_path, period='2y', interval='1d')
    print(f"   Loaded {len(df_daily)} daily bars")

    # Initialize scanners
    print("\n2. Initializing scanners...")
    ici_scanner = ICIScanner()
    momentum_scanner = MomentumScanner()
    wm_scanner = WMScanner()
    harmonic_scanner = HarmonicScanner()
    print("   All scanners ready")

    all_setups = []

    # Scan ICI patterns on daily, weekly, monthly
    print("\n3. Scanning ICI patterns...")

    print("   - Daily timeframe...")
    ici_daily = ici_scanner.scan(df_daily, 'daily')
    ici_daily = ici_scanner.deduplicate_setups(ici_daily)
    all_setups.extend(ici_daily)
    print(f"     Found {len(ici_daily)} ICI setups on daily")

    # Resample to weekly
    loader = DataLoader()
    df_weekly = loader.resample_to_timeframe(df_daily, '1W')
    ici_weekly = ici_scanner.scan(df_weekly, 'weekly')
    ici_weekly = ici_scanner.deduplicate_setups(ici_weekly)
    all_setups.extend(ici_weekly)
    print(f"     Found {len(ici_weekly)} ICI setups on weekly")

    # Resample to monthly
    df_monthly = loader.resample_to_timeframe(df_daily, '1M')
    ici_monthly = ici_scanner.scan(df_monthly, 'monthly')
    ici_monthly = ici_scanner.deduplicate_setups(ici_monthly)
    all_setups.extend(ici_monthly)
    print(f"     Found {len(ici_monthly)} ICI setups on monthly")

    # Scan Momentum patterns (would need 1h data from yfinance)
    print("\n4. Scanning Momentum patterns...")
    print("   - Skipping (requires 1h data - use interval='1h' with shorter period)")
    # To enable: df_1h = load_spy_data(source='yfinance', period='60d', interval='1h')
    # momentum_setups = momentum_scanner.scan(df_1h, '1h')

    # Scan W/M patterns
    print("\n5. Scanning W/M patterns...")

    print("   - Weekly timeframe...")
    wm_weekly = wm_scanner.scan(df_weekly, 'weekly')
    all_setups.extend(wm_weekly)
    print(f"     Found {len(wm_weekly)} W/M setups on weekly")

    print("   - Monthly timeframe...")
    wm_monthly = wm_scanner.scan(df_monthly, 'monthly')
    all_setups.extend(wm_monthly)
    print(f"     Found {len(wm_monthly)} W/M setups on monthly")

    # Scan Harmonic patterns
    print("\n6. Scanning Harmonic patterns...")
    print("   - Daily timeframe...")
    harmonic_daily = harmonic_scanner.scan(df_daily, 'daily')
    all_setups.extend(harmonic_daily)
    print(f"     Found {len(harmonic_daily)} Harmonic setups on daily")

    # Generate reports
    print("\n7. Generating reports...")
    reporter = PatternScannerReport()

    # Print statistics
    reporter.print_statistics(all_setups)

    # Print recent setups
    reporter.print_recent_setups(all_setups, count=10)

    # Export to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'spy_patterns_{timestamp}.csv'
    reporter.export_to_csv(all_setups, csv_filename)

    print("\n" + "=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    # Run scanner with yfinance data
    run_all_scanners(data_source='yfinance')

    # To use CSV instead:
    # run_all_scanners(data_source='csv', csv_path='path/to/spy_data.csv')
