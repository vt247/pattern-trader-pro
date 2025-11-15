"""
Extended Multi-Timeframe Test - Maximum Historical Data
Uses yfinance maximum limits for each timeframe
"""
import pandas as pd
from datetime import datetime
from data_loader import DataLoader
from ici_scanner import ICIScanner
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')


def load_maximum_data():
    """Load maximum available data for each timeframe"""
    print("=" * 100)
    print(" " * 25 + "🔄 LOADING MAXIMUM HISTORICAL DATA")
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
        print(f"   ✓ Loaded {len(df_1d)} bars")
        print(f"   ✓ Range: {df_1d['Date'].min()} to {df_1d['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['1d'] = None

    # 4 Hour - Create from 1h data, max 730 days
    print("\n📥 Loading 4 Hour data (730 days from 1h)...")
    try:
        ticker = yf.Ticker('SPY')
        df_1h_raw = ticker.history(period='730d', interval='1h')

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
        print(f"   ✓ Loaded {len(resampled)} bars")
        print(f"   ✓ Range: {resampled['Date'].min()} to {resampled['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['4h'] = None

    # 1 Hour - 730 days (yfinance max)
    print("\n📥 Loading 1 Hour data (730 days - yfinance max)...")
    try:
        ticker = yf.Ticker('SPY')
        df_1h = ticker.history(period='730d', interval='1h')
        df_1h.reset_index(inplace=True)
        if 'Datetime' in df_1h.columns:
            df_1h.rename(columns={'Datetime': 'Date'}, inplace=True)
        data['1h'] = df_1h
        print(f"   ✓ Loaded {len(df_1h)} bars")
        print(f"   ✓ Range: {df_1h['Date'].min()} to {df_1h['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['1h'] = None

    # 15 Minute - 60 days (yfinance max)
    print("\n📥 Loading 15 Minute data (60 days - yfinance max)...")
    try:
        ticker = yf.Ticker('SPY')
        df_15m = ticker.history(period='60d', interval='15m')
        df_15m.reset_index(inplace=True)
        if 'Datetime' in df_15m.columns:
            df_15m.rename(columns={'Datetime': 'Date'}, inplace=True)
        data['15m'] = df_15m
        print(f"   ✓ Loaded {len(df_15m)} bars")
        print(f"   ✓ Range: {df_15m['Date'].min()} to {df_15m['Date'].max()}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        data['15m'] = None

    return data


def analyze_timeframe_detailed(setups: List, timeframe: str):
    """Detailed analysis with more metrics"""
    if not setups:
        print(f"\n  ❌ No patterns found on {timeframe}")
        return {
            'timeframe': timeframe,
            'total': 0,
            'valid': 0,
            'validity_pct': 0,
            'avg_rr': 0,
            'max_rr': 0,
            'avg_fib': 0,
            'bullish': 0,
            'bearish': 0
        }

    valid = [s for s in setups if s.valid]
    bullish = [s for s in setups if s.is_bullish]
    bearish = [s for s in setups if not s.is_bullish]

    print(f"\n  📊 {timeframe.upper()} Analysis:")
    print(f"     Total setups: {len(setups)}")
    print(f"     Valid setups: {len(valid)} ({len(valid)/len(setups)*100:.1f}%)")
    print(f"     Bullish: {len(bullish)} ({len(bullish)/len(setups)*100:.1f}%)")
    print(f"     Bearish: {len(bearish)} ({len(bearish)/len(setups)*100:.1f}%)")

    stats = {
        'timeframe': timeframe,
        'total': len(setups),
        'valid': len(valid),
        'validity_pct': len(valid)/len(setups)*100 if setups else 0,
        'bullish': len(bullish),
        'bearish': len(bearish),
        'avg_rr': 0,
        'max_rr': 0,
        'min_rr': 0,
        'avg_fib': 0
    }

    if valid:
        rr_ratios = [s.risk_reward for s in valid]
        fib_levels = [s.correction_pct for s in valid]

        stats['avg_rr'] = sum(rr_ratios) / len(rr_ratios)
        stats['max_rr'] = max(rr_ratios)
        stats['min_rr'] = min(rr_ratios)
        stats['avg_fib'] = sum(fib_levels) / len(fib_levels)

        print(f"\n     Risk/Reward:")
        print(f"       Average: {stats['avg_rr']:.2f}")
        print(f"       Min: {stats['min_rr']:.2f}")
        print(f"       Max: {stats['max_rr']:.2f}")

        print(f"\n     Fibonacci:")
        print(f"       Average: {stats['avg_fib']:.3f}")
        print(f"       Range: {min(fib_levels):.3f} - {max(fib_levels):.3f}")

        ema_count = len([s for s in valid if s.ema_aligned])
        macd_count = len([s for s in valid if s.macd_aligned])

        print(f"\n     Indicators:")
        print(f"       EMA aligned: {ema_count}/{len(valid)} ({ema_count/len(valid)*100:.1f}%)")
        print(f"       MACD aligned: {macd_count}/{len(valid)} ({macd_count/len(valid)*100:.1f}%)")

        # Show top 5
        print(f"\n     🏆 Top 5 Valid Setups by R:R:")
        sorted_valid = sorted(valid, key=lambda s: s.risk_reward, reverse=True)[:5]
        for i, s in enumerate(sorted_valid, 1):
            direction = "LONG" if s.is_bullish else "SHORT"
            date_str = s.date.strftime('%Y-%m-%d %H:%M') if hasattr(s.date, 'hour') else s.date.strftime('%Y-%m-%d')
            print(f"       {i}. {date_str} {direction:5s} | "
                  f"R:R {s.risk_reward:.2f} | Fib {s.correction_pct:.3f} | "
                  f"Entry ${s.entry:.2f}")

    return stats


def main():
    print("=" * 100)
    print(" " * 20 + "🚀 EXTENDED MULTI-TIMEFRAME TEST - MAXIMUM DATA 🚀")
    print("=" * 100)
    print("\nData Limits:")
    print("  • 1 Day:   2 years")
    print("  • 4 Hour:  730 days (~2 years)")
    print("  • 1 Hour:  730 days (~2 years)")
    print("  • 15 Min:  60 days (yfinance max)")

    # Load data
    data = load_maximum_data()

    # Initialize scanners
    print("\n" + "=" * 100)
    print(" " * 35 + "🔧 INITIALIZING SCANNERS")
    print("=" * 100)

    scanners = {
        '1d': ICIScanner(min_impulse_candles=3, min_correction_candles=2, min_risk_reward=1.3),
        '4h': ICIScanner(min_impulse_candles=3, min_correction_candles=2, min_risk_reward=1.3),
        '1h': ICIScanner(min_impulse_candles=3, min_correction_candles=2, min_risk_reward=1.3),
        '15m': ICIScanner(min_impulse_candles=2, min_correction_candles=2, min_risk_reward=1.3),
    }
    print("\n   ✓ Scanners initialized")

    # Scan each timeframe
    print("\n" + "=" * 100)
    print(" " * 30 + "🔍 SCANNING ALL TIMEFRAMES")
    print("=" * 100)

    results = {}
    stats_list = []

    for tf in ['1d', '4h', '1h', '15m']:
        print(f"\n{'─' * 100}")
        print(f"🔍 Scanning {tf.upper()} timeframe...")
        print(f"{'─' * 100}")

        if data[tf] is None:
            print(f"   ⚠ No data available")
            results[tf] = []
            continue

        try:
            print(f"   Processing {len(data[tf])} bars...")
            setups = scanners[tf].scan(data[tf], tf)
            setups = scanners[tf].deduplicate_setups(setups)
            results[tf] = setups

            stats = analyze_timeframe_detailed(setups, tf)
            stats_list.append(stats)

        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results[tf] = []

    # Comprehensive comparison
    print("\n" + "=" * 100)
    print(" " * 25 + "📊 COMPREHENSIVE COMPARISON TABLE")
    print("=" * 100)

    print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ TF    │ Bars │ Total │ Valid │ Valid% │ Avg RR │ Max RR │ Bull% │ Bear% │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")

    for stats in stats_list:
        tf = stats['timeframe']
        bars = len(data[tf]) if data[tf] is not None else 0
        bull_pct = (stats['bullish']/stats['total']*100) if stats['total'] > 0 else 0
        bear_pct = (stats['bearish']/stats['total']*100) if stats['total'] > 0 else 0

        print(f"│ {tf:5s} │ {bars:4d} │ {stats['total']:5d} │ {stats['valid']:5d} │ "
              f"{stats['validity_pct']:5.1f}% │ {stats['avg_rr']:6.2f} │ "
              f"{stats['max_rr']:6.2f} │ {bull_pct:5.1f}% │ {bear_pct:5.1f}% │")

    print("└─────────────────────────────────────────────────────────────────────────────┘")

    # Overall statistics
    print("\n" + "=" * 100)
    print(" " * 30 + "📈 OVERALL STATISTICS")
    print("=" * 100)

    total_setups = sum(len(results.get(tf, [])) for tf in ['1d', '4h', '1h', '15m'])
    total_valid = sum(len([s for s in results.get(tf, []) if s.valid]) for tf in ['1d', '4h', '1h', '15m'])

    print(f"\n🎯 Grand Total:")
    print(f"   Total setups found: {total_setups}")
    print(f"   Valid setups: {total_valid} ({total_valid/total_setups*100:.1f}%)" if total_setups > 0 else "   Valid setups: 0")

    # Find best setups across all timeframes
    all_valid = []
    for tf, setups in results.items():
        all_valid.extend([s for s in setups if s.valid])

    if all_valid:
        print(f"\n🏆 Best Setups Across All Timeframes:")
        sorted_all = sorted(all_valid, key=lambda s: s.risk_reward, reverse=True)[:10]
        for i, s in enumerate(sorted_all, 1):
            direction = "LONG" if s.is_bullish else "SHORT"
            date_str = s.date.strftime('%Y-%m-%d %H:%M') if hasattr(s.date, 'hour') else s.date.strftime('%Y-%m-%d')
            print(f"   {i:2d}. [{s.timeframe.upper():4s}] {date_str} {direction:5s} | "
                  f"R:R {s.risk_reward:6.2f} | Entry ${s.entry:.2f} | Fib {s.correction_pct:.3f}")

    # Export results
    print("\n" + "=" * 100)
    print(" " * 35 + "💾 EXPORTING RESULTS")
    print("=" * 100)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Export each timeframe
    for tf in ['1d', '4h', '1h', '15m']:
        setups = results.get(tf, [])
        if setups:
            valid = [s for s in setups if s.valid]

            # All
            csv_all = f'extended_{tf}_all_{timestamp}.csv'
            df_all = pd.DataFrame([s.to_dict() for s in setups])
            df_all.sort_values('Date', inplace=True)
            df_all.to_csv(csv_all, index=False)
            print(f"\n✓ {tf.upper():4s} all: {csv_all} ({len(setups)} setups)")

            # Valid only
            if valid:
                csv_valid = f'extended_{tf}_valid_{timestamp}.csv'
                df_valid = pd.DataFrame([s.to_dict() for s in valid])
                df_valid.sort_values('Date', inplace=True)
                df_valid.to_csv(csv_valid, index=False)
                print(f"  {tf.upper():4s} valid: {csv_valid} ({len(valid)} setups)")

    # Combined export
    if total_setups > 0:
        all_setups = []
        for tf, setups in results.items():
            all_setups.extend(setups)

        csv_combined = f'extended_all_tf_{timestamp}.csv'
        df_combined = pd.DataFrame([s.to_dict() for s in all_setups])
        df_combined.sort_values(['Timeframe', 'Date'], inplace=True)
        df_combined.to_csv(csv_combined, index=False)
        print(f"\n✓ Combined: {csv_combined} ({len(all_setups)} total)")

        # Valid only combined
        if total_valid > 0:
            csv_valid_combined = f'extended_valid_all_tf_{timestamp}.csv'
            all_valid_setups = [s for s in all_setups if s.valid]
            df_valid_combined = pd.DataFrame([s.to_dict() for s in all_valid_setups])
            df_valid_combined.sort_values(['Timeframe', 'Date'], inplace=True)
            df_valid_combined.to_csv(csv_valid_combined, index=False)
            print(f"✓ Valid Combined: {csv_valid_combined} ({total_valid} setups)")

    print("\n" + "=" * 100)
    print(" " * 35 + "✅ EXTENDED TEST COMPLETE!")
    print("=" * 100)

    # Key insights
    print("\n🔑 KEY INSIGHTS:")

    # Best timeframe by validity
    best_validity_tf = max(stats_list, key=lambda x: x['validity_pct'])
    print(f"   • Best validity: {best_validity_tf['timeframe'].upper()} "
          f"({best_validity_tf['validity_pct']:.1f}%)")

    # Best average R:R
    valid_stats = [s for s in stats_list if s['valid'] > 0]
    if valid_stats:
        best_rr_tf = max(valid_stats, key=lambda x: x['avg_rr'])
        print(f"   • Best avg R:R: {best_rr_tf['timeframe'].upper()} "
              f"({best_rr_tf['avg_rr']:.2f})")

    # Most setups
    most_setups_tf = max(stats_list, key=lambda x: x['total'])
    print(f"   • Most setups: {most_setups_tf['timeframe'].upper()} "
          f"({most_setups_tf['total']} total)")

    print("\n" + "=" * 100 + "\n")


if __name__ == '__main__':
    main()
