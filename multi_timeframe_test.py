"""
Multi-Timeframe Pattern Scanner Test
Tests: 1 day, 4 hour, 1 hour, 15 minute
"""
import pandas as pd
from datetime import datetime
from data_loader import DataLoader
from ici_scanner import ICIScanner, ICISetup
from pattern_scanners import MomentumScanner
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


def load_multi_timeframe_data():
    """Load SPY data for all timeframes"""
    print("=" * 100)
    print(" " * 30 + "🔄 LOADING MULTI-TIMEFRAME DATA")
    print("=" * 100)

    data = {}

    # 1 Day - 2 years
    print("\n📥 Loading 1 Day data (2 years)...")
    try:
        import yfinance as yf
        ticker = yf.Ticker('SPY')
        df_1d = ticker.history(period='2y', interval='1d')
        df_1d.reset_index(inplace=True)
        data['1d'] = df_1d
        print(f"   ✓ Loaded {len(df_1d)} bars from {df_1d['Date'].min()} to {df_1d['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['1d'] = None

    # 4 Hour - 60 days (max for intraday)
    print("\n📥 Loading 4 Hour data (60 days)...")
    try:
        # yfinance doesn't have 4h, so we'll download 1h and resample
        ticker = yf.Ticker('SPY')
        df_1h_raw = ticker.history(period='60d', interval='1h')

        # Resample to 4h
        df_1h_raw.index.name = 'Date'
        resampled = pd.DataFrame()
        resampled['Open'] = df_1h_raw['Open'].resample('4h').first()
        resampled['High'] = df_1h_raw['High'].resample('4h').max()
        resampled['Low'] = df_1h_raw['Low'].resample('4h').min()
        resampled['Close'] = df_1h_raw['Close'].resample('4h').last()
        resampled['Volume'] = df_1h_raw['Volume'].resample('4h').sum()
        resampled.dropna(inplace=True)
        resampled.reset_index(inplace=True)

        data['4h'] = resampled
        print(f"   ✓ Loaded {len(resampled)} bars from {resampled['Date'].min()} to {resampled['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['4h'] = None

    # 1 Hour - 60 days
    print("\n📥 Loading 1 Hour data (60 days)...")
    try:
        ticker = yf.Ticker('SPY')
        df_1h = ticker.history(period='60d', interval='1h')
        df_1h.reset_index(inplace=True)
        # Rename Datetime to Date if needed
        if 'Datetime' in df_1h.columns:
            df_1h.rename(columns={'Datetime': 'Date'}, inplace=True)
        data['1h'] = df_1h
        print(f"   ✓ Loaded {len(df_1h)} bars from {df_1h['Date'].min()} to {df_1h['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['1h'] = None

    # 15 Minute - 7 days (max for 15m)
    print("\n📥 Loading 15 Minute data (7 days)...")
    try:
        ticker = yf.Ticker('SPY')
        df_15m = ticker.history(period='7d', interval='15m')
        df_15m.reset_index(inplace=True)
        # Rename Datetime to Date if needed
        if 'Datetime' in df_15m.columns:
            df_15m.rename(columns={'Datetime': 'Date'}, inplace=True)
        data['15m'] = df_15m
        print(f"   ✓ Loaded {len(df_15m)} bars from {df_15m['Date'].min()} to {df_15m['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['15m'] = None

    return data


def analyze_timeframe_setups(setups: List[ICISetup], timeframe: str):
    """Analyze setups for a specific timeframe"""
    if not setups:
        print(f"\n  ❌ No patterns found on {timeframe}")
        return

    valid = [s for s in setups if s.valid]
    bullish = [s for s in setups if s.is_bullish]
    bearish = [s for s in setups if not s.is_bullish]

    print(f"\n  📊 {timeframe.upper()} Results:")
    print(f"     Total setups: {len(setups)}")
    print(f"     Valid setups: {len(valid)} ({len(valid)/len(setups)*100:.1f}%)")
    print(f"     Bullish: {len(bullish)} | Bearish: {len(bearish)}")

    if valid:
        rr_ratios = [s.risk_reward for s in valid]
        fib_levels = [s.correction_pct for s in valid]

        print(f"\n     Risk/Reward: Avg {sum(rr_ratios)/len(rr_ratios):.2f} | "
              f"Min {min(rr_ratios):.2f} | Max {max(rr_ratios):.2f}")
        print(f"     Fibonacci: Avg {sum(fib_levels)/len(fib_levels):.3f} | "
              f"Range {min(fib_levels):.3f}-{max(fib_levels):.3f}")

        ema_count = len([s for s in valid if s.ema_aligned])
        macd_count = len([s for s in valid if s.macd_aligned])

        print(f"     EMA aligned: {ema_count}/{len(valid)} ({ema_count/len(valid)*100:.1f}%)")
        print(f"     MACD aligned: {macd_count}/{len(valid)} ({macd_count/len(valid)*100:.1f}%)")

        # Show top 3
        print(f"\n     🏆 Top 3 by R:R:")
        sorted_valid = sorted(valid, key=lambda s: s.risk_reward, reverse=True)[:3]
        for i, s in enumerate(sorted_valid, 1):
            direction = "LONG" if s.is_bullish else "SHORT"
            date_str = s.date.strftime('%Y-%m-%d %H:%M') if hasattr(s.date, 'hour') else s.date.strftime('%Y-%m-%d')
            print(f"       {i}. {date_str} {direction:5s} | "
                  f"R:R {s.risk_reward:.2f} | Fib {s.correction_pct:.3f}")


def main():
    print("=" * 100)
    print(" " * 25 + "🚀 MULTI-TIMEFRAME PATTERN SCANNER TEST 🚀")
    print("=" * 100)
    print("\nTimeframes: 1 Day, 4 Hour, 1 Hour, 15 Minute")
    print("Pattern: ICI (Impulse-Correction-Impulse)")

    # Load data
    data = load_multi_timeframe_data()

    # Initialize scanners
    print("\n" + "=" * 100)
    print(" " * 35 + "🔧 INITIALIZING SCANNERS")
    print("=" * 100)

    # Use different parameters for different timeframes
    scanners = {
        '1d': ICIScanner(min_impulse_candles=3, min_correction_candles=2, min_risk_reward=1.3),
        '4h': ICIScanner(min_impulse_candles=3, min_correction_candles=2, min_risk_reward=1.3),
        '1h': ICIScanner(min_impulse_candles=3, min_correction_candles=2, min_risk_reward=1.3),
        '15m': ICIScanner(min_impulse_candles=2, min_correction_candles=2, min_risk_reward=1.3),  # Shorter for 15m
    }
    print("\n   ✓ Scanners initialized for all timeframes")

    # Scan each timeframe
    print("\n" + "=" * 100)
    print(" " * 35 + "🔍 SCANNING PATTERNS")
    print("=" * 100)

    results = {}

    for tf in ['1d', '4h', '1h', '15m']:
        print(f"\n{'─' * 100}")
        print(f"🔍 Scanning {tf.upper()} timeframe...")
        print(f"{'─' * 100}")

        if data[tf] is None:
            print(f"   ⚠ No data available for {tf}")
            results[tf] = []
            continue

        try:
            setups = scanners[tf].scan(data[tf], tf)
            setups = scanners[tf].deduplicate_setups(setups)
            results[tf] = setups
            analyze_timeframe_setups(setups, tf)
        except Exception as e:
            print(f"   ✗ Error scanning {tf}: {e}")
            import traceback
            traceback.print_exc()
            results[tf] = []

    # Overall comparison
    print("\n" + "=" * 100)
    print(" " * 30 + "📊 TIMEFRAME COMPARISON SUMMARY")
    print("=" * 100)

    comparison_data = []
    for tf in ['1d', '4h', '1h', '15m']:
        setups = results.get(tf, [])
        valid = [s for s in setups if s.valid]

        if setups:
            avg_rr = sum(s.risk_reward for s in valid) / len(valid) if valid else 0
            avg_fib = sum(s.correction_pct for s in valid) / len(valid) if valid else 0
        else:
            avg_rr = 0
            avg_fib = 0

        comparison_data.append({
            'Timeframe': tf,
            'Bars': len(data[tf]) if data[tf] is not None else 0,
            'Total': len(setups),
            'Valid': len(valid),
            'Valid %': f"{len(valid)/len(setups)*100:.1f}%" if setups else "0%",
            'Avg R:R': f"{avg_rr:.2f}" if avg_rr > 0 else "-",
            'Avg Fib': f"{avg_fib:.3f}" if avg_fib > 0 else "-"
        })

    print("\n┌─ COMPARISON TABLE ───────────────────────────────────────────────────────────┐")
    print("│                                                                              │")
    print("│ Timeframe │ Bars │ Total │ Valid │ Valid % │ Avg R:R │ Avg Fib              │")
    print("│ ──────────────────────────────────────────────────────────────────────────── │")

    for row in comparison_data:
        print(f"│ {row['Timeframe']:9s} │ {row['Bars']:4d} │ {row['Total']:5d} │ "
              f"{row['Valid']:5d} │ {row['Valid %']:7s} │ {row['Avg R:R']:7s} │ "
              f"{row['Avg Fib']:7s}              │")

    print("│                                                                              │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")

    # Export results
    print("\n" + "=" * 100)
    print(" " * 35 + "💾 EXPORTING RESULTS")
    print("=" * 100)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Export all timeframes to separate CSVs
    for tf in ['1d', '4h', '1h', '15m']:
        setups = results.get(tf, [])
        if setups:
            valid = [s for s in setups if s.valid]

            # All setups
            csv_all = f'multi_tf_{tf}_all_{timestamp}.csv'
            data_all = [s.to_dict() for s in setups]
            df_export = pd.DataFrame(data_all)
            df_export.sort_values('Date', inplace=True)
            df_export.to_csv(csv_all, index=False)
            print(f"\n✓ {tf.upper()} all setups: {csv_all} ({len(setups)} setups)")

            # Valid only
            if valid:
                csv_valid = f'multi_tf_{tf}_valid_{timestamp}.csv'
                data_valid = [s.to_dict() for s in valid]
                df_valid = pd.DataFrame(data_valid)
                df_valid.sort_values('Date', inplace=True)
                df_valid.to_csv(csv_valid, index=False)
                print(f"✓ {tf.upper()} valid setups: {csv_valid} ({len(valid)} setups)")

    # Combined export
    all_setups = []
    for tf, setups in results.items():
        all_setups.extend(setups)

    if all_setups:
        csv_combined = f'multi_tf_combined_{timestamp}.csv'
        data_combined = [s.to_dict() for s in all_setups]
        df_combined = pd.DataFrame(data_combined)
        df_combined.sort_values(['Timeframe', 'Date'], inplace=True)
        df_combined.to_csv(csv_combined, index=False)
        print(f"\n✓ Combined all timeframes: {csv_combined} ({len(all_setups)} total setups)")

    print("\n" + "=" * 100)
    print(" " * 35 + "✅ TEST COMPLETE!")
    print("=" * 100)

    # Summary insights
    print("\n🔑 KEY INSIGHTS:")

    # Which timeframe has most setups?
    tf_counts = {tf: len(results.get(tf, [])) for tf in ['1d', '4h', '1h', '15m']}
    best_tf = max(tf_counts, key=tf_counts.get)
    if tf_counts[best_tf] > 0:
        print(f"   • Most setups found on: {best_tf.upper()} ({tf_counts[best_tf]} setups)")

    # Which has best R:R?
    valid_counts = {tf: len([s for s in results.get(tf, []) if s.valid]) for tf in ['1d', '4h', '1h', '15m']}
    total_valid = sum(valid_counts.values())

    if total_valid > 0:
        print(f"   • Total valid setups across all timeframes: {total_valid}")

        # Calculate best avg R:R
        best_rr_tf = None
        best_rr_val = 0
        for tf in ['1d', '4h', '1h', '15m']:
            valid = [s for s in results.get(tf, []) if s.valid]
            if valid:
                avg_rr = sum(s.risk_reward for s in valid) / len(valid)
                if avg_rr > best_rr_val:
                    best_rr_val = avg_rr
                    best_rr_tf = tf

        if best_rr_tf:
            print(f"   • Best average R:R: {best_rr_tf.upper()} ({best_rr_val:.2f})")

    print("\n" + "=" * 100 + "\n")


if __name__ == '__main__':
    main()
