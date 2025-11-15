"""
Comprehensive test of all pattern types on 2-year S&P 500 data
"""
import pandas as pd
from datetime import datetime
from data_loader import load_spy_data, DataLoader
from ici_scanner import ICIScanner, ICISetup
from pattern_scanners import MomentumScanner, WMScanner, HarmonicScanner
from typing import List


def analyze_setups(setups: List[ICISetup], pattern_name: str):
    """Detailed analysis of setups"""
    if not setups:
        print(f"\n  ❌ No {pattern_name} patterns found")
        return

    valid = [s for s in setups if s.valid]
    bullish = [s for s in setups if s.is_bullish]
    bearish = [s for s in setups if not s.is_bullish]

    print(f"\n  📊 {pattern_name} Analysis:")
    print(f"     Total setups: {len(setups)}")
    print(f"     Valid setups: {len(valid)} ({len(valid)/len(setups)*100:.1f}%)")
    print(f"     Bullish: {len(bullish)}")
    print(f"     Bearish: {len(bearish)}")

    if valid:
        rr_ratios = [s.risk_reward for s in valid]
        fib_levels = [s.correction_pct for s in valid]

        print(f"\n     Risk/Reward:")
        print(f"       Average: {sum(rr_ratios)/len(rr_ratios):.2f}")
        print(f"       Min: {min(rr_ratios):.2f}")
        print(f"       Max: {max(rr_ratios):.2f}")

        print(f"\n     Fibonacci Levels:")
        print(f"       Average: {sum(fib_levels)/len(fib_levels):.3f}")
        print(f"       Min: {min(fib_levels):.3f}")
        print(f"       Max: {max(fib_levels):.3f}")

        ema_count = len([s for s in valid if s.ema_aligned])
        macd_count = len([s for s in valid if s.macd_aligned])
        both_count = len([s for s in valid if s.ema_aligned and s.macd_aligned])

        print(f"\n     Indicator Alignment:")
        print(f"       EMA aligned: {ema_count}/{len(valid)} ({ema_count/len(valid)*100:.1f}%)")
        print(f"       MACD aligned: {macd_count}/{len(valid)} ({macd_count/len(valid)*100:.1f}%)")
        print(f"       Both aligned: {both_count}/{len(valid)} ({both_count/len(valid)*100:.1f}%)")

        # Show top 3 setups by R:R
        print(f"\n     🏆 Top 3 Setups by Risk/Reward:")
        sorted_valid = sorted(valid, key=lambda s: s.risk_reward, reverse=True)[:3]
        for i, s in enumerate(sorted_valid, 1):
            direction = "LONG" if s.is_bullish else "SHORT"
            print(f"       {i}. {s.date.strftime('%Y-%m-%d')} - {direction}")
            print(f"          Entry: ${s.entry:.2f} | Stop: ${s.stop:.2f} | Target: ${s.target:.2f}")
            print(f"          R:R: {s.risk_reward:.2f} | Fib: {s.correction_pct:.3f}")


def main():
    print("=" * 100)
    print("COMPREHENSIVE S&P 500 PATTERN TEST - 2 YEARS OF DATA")
    print("=" * 100)

    # ========== 1. Load Daily Data ==========
    print("\n" + "🔄 PHASE 1: DATA LOADING")
    print("-" * 100)

    print("\n📥 Loading SPY daily data (2 years)...")
    df_daily = load_spy_data(source='yfinance', period='2y', interval='1d')
    print(f"   ✓ Loaded {len(df_daily)} daily bars")
    print(f"   ✓ Date range: {df_daily['Date'].min()} to {df_daily['Date'].max()}")

    # Resample to different timeframes
    loader = DataLoader()

    print("\n📥 Resampling to weekly...")
    df_weekly = loader.resample_to_timeframe(df_daily, '1W')
    print(f"   ✓ {len(df_weekly)} weekly bars")

    print("\n📥 Resampling to monthly...")
    df_monthly = loader.resample_to_timeframe(df_daily, '1M')
    print(f"   ✓ {len(df_monthly)} monthly bars")

    # Try to load 1h data for momentum
    print("\n📥 Loading 1h data for Momentum patterns (60 days)...")
    try:
        df_1h = load_spy_data(source='yfinance', period='60d', interval='1h')
        print(f"   ✓ Loaded {len(df_1h)} hourly bars")
        has_1h_data = True
    except Exception as e:
        print(f"   ⚠ Could not load 1h data: {e}")
        has_1h_data = False

    # ========== 2. Initialize Scanners ==========
    print("\n" + "🔄 PHASE 2: SCANNER INITIALIZATION")
    print("-" * 100)

    ici_scanner = ICIScanner()
    momentum_scanner = MomentumScanner()
    wm_scanner = WMScanner()
    harmonic_scanner = HarmonicScanner()
    print("\n   ✓ All scanners initialized")

    # ========== 3. Scan ICI Patterns ==========
    print("\n" + "🔄 PHASE 3: ICI PATTERN SCANNING")
    print("-" * 100)

    all_setups = []

    print("\n🔍 Scanning ICI on DAILY timeframe...")
    ici_daily = ici_scanner.scan(df_daily, 'daily')
    ici_daily = ici_scanner.deduplicate_setups(ici_daily)
    all_setups.extend(ici_daily)
    analyze_setups(ici_daily, "ICI Daily")

    print("\n🔍 Scanning ICI on WEEKLY timeframe...")
    ici_weekly = ici_scanner.scan(df_weekly, 'weekly')
    ici_weekly = ici_scanner.deduplicate_setups(ici_weekly)
    all_setups.extend(ici_weekly)
    analyze_setups(ici_weekly, "ICI Weekly")

    print("\n🔍 Scanning ICI on MONTHLY timeframe...")
    ici_monthly = ici_scanner.scan(df_monthly, 'monthly')
    ici_monthly = ici_scanner.deduplicate_setups(ici_monthly)
    all_setups.extend(ici_monthly)
    analyze_setups(ici_monthly, "ICI Monthly")

    # ========== 4. Scan Momentum Patterns ==========
    print("\n" + "🔄 PHASE 4: MOMENTUM PATTERN SCANNING")
    print("-" * 100)

    if has_1h_data:
        print("\n🔍 Scanning MOMENTUM on 1H timeframe...")
        momentum_setups = momentum_scanner.scan(df_1h, '1h')
        momentum_setups = momentum_scanner.deduplicate_setups(momentum_setups)
        all_setups.extend(momentum_setups)
        analyze_setups(momentum_setups, "Momentum 1h")
    else:
        print("\n  ⚠ Skipping Momentum scan (no 1h data)")

    # ========== 5. Scan W/M Patterns ==========
    print("\n" + "🔄 PHASE 5: W/M PATTERN SCANNING")
    print("-" * 100)

    print("\n🔍 Scanning W/M on WEEKLY timeframe...")
    wm_weekly = wm_scanner.scan(df_weekly, 'weekly')
    all_setups.extend(wm_weekly)

    w_weekly = [s for s in wm_weekly if s.pattern_type == 'W']
    m_weekly = [s for s in wm_weekly if s.pattern_type == 'M']

    if w_weekly:
        analyze_setups(w_weekly, "W Pattern (Weekly)")
    if m_weekly:
        analyze_setups(m_weekly, "M Pattern (Weekly)")
    if not wm_weekly:
        print("\n  ❌ No W/M patterns found on weekly")

    print("\n🔍 Scanning W/M on MONTHLY timeframe...")
    wm_monthly = wm_scanner.scan(df_monthly, 'monthly')
    all_setups.extend(wm_monthly)

    w_monthly = [s for s in wm_monthly if s.pattern_type == 'W']
    m_monthly = [s for s in wm_monthly if s.pattern_type == 'M']

    if w_monthly:
        analyze_setups(w_monthly, "W Pattern (Monthly)")
    if m_monthly:
        analyze_setups(m_monthly, "M Pattern (Monthly)")
    if not wm_monthly:
        print("\n  ❌ No W/M patterns found on monthly")

    # ========== 6. Scan Harmonic Patterns ==========
    print("\n" + "🔄 PHASE 6: HARMONIC PATTERN SCANNING")
    print("-" * 100)

    print("\n🔍 Scanning HARMONIC on DAILY timeframe...")
    harmonic_daily = harmonic_scanner.scan(df_daily, 'daily')
    all_setups.extend(harmonic_daily)
    analyze_setups(harmonic_daily, "Harmonic Daily")

    # ========== 7. Overall Summary ==========
    print("\n" + "=" * 100)
    print("📈 OVERALL SUMMARY")
    print("=" * 100)

    total = len(all_setups)
    valid = len([s for s in all_setups if s.valid])

    print(f"\n🎯 Total Patterns Found: {total}")
    print(f"✓ Valid Patterns: {valid} ({valid/total*100:.1f}%)" if total > 0 else "✓ Valid Patterns: 0")
    print(f"✗ Invalid Patterns: {total - valid} ({(total-valid)/total*100:.1f}%)" if total > 0 else "✗ Invalid Patterns: 0")

    # By pattern type
    print(f"\n📊 By Pattern Type:")
    pattern_types = {}
    for setup in all_setups:
        ptype = setup.pattern_type
        if ptype not in pattern_types:
            pattern_types[ptype] = {'total': 0, 'valid': 0}
        pattern_types[ptype]['total'] += 1
        if setup.valid:
            pattern_types[ptype]['valid'] += 1

    for ptype, stats in sorted(pattern_types.items()):
        valid_pct = (stats['valid']/stats['total']*100) if stats['total'] > 0 else 0
        print(f"   {ptype:15s}: {stats['total']:3d} total, {stats['valid']:3d} valid ({valid_pct:.1f}%)")

    # By timeframe
    print(f"\n⏰ By Timeframe:")
    timeframe_stats = {}
    for setup in all_setups:
        tf = setup.timeframe
        if tf not in timeframe_stats:
            timeframe_stats[tf] = {'total': 0, 'valid': 0}
        timeframe_stats[tf]['total'] += 1
        if setup.valid:
            timeframe_stats[tf]['valid'] += 1

    for tf, stats in sorted(timeframe_stats.items()):
        valid_pct = (stats['valid']/stats['total']*100) if stats['total'] > 0 else 0
        print(f"   {tf:15s}: {stats['total']:3d} total, {stats['valid']:3d} valid ({valid_pct:.1f}%)")

    # Export results
    print("\n" + "=" * 100)
    print("💾 EXPORTING RESULTS")
    print("=" * 100)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Export all setups
    csv_all = f'comprehensive_test_all_{timestamp}.csv'
    data_all = [s.to_dict() for s in all_setups]
    df_export = pd.DataFrame(data_all)
    df_export.sort_values('Date', inplace=True)
    df_export.to_csv(csv_all, index=False)
    print(f"\n✓ All setups exported to: {csv_all}")

    # Export valid only
    if valid > 0:
        csv_valid = f'comprehensive_test_valid_{timestamp}.csv'
        valid_setups = [s for s in all_setups if s.valid]
        data_valid = [s.to_dict() for s in valid_setups]
        df_valid = pd.DataFrame(data_valid)
        df_valid.sort_values('Date', inplace=True)
        df_valid.to_csv(csv_valid, index=False)
        print(f"✓ Valid setups exported to: {csv_valid}")

    print("\n" + "=" * 100)
    print("✅ COMPREHENSIVE TEST COMPLETE!")
    print("=" * 100)


if __name__ == '__main__':
    main()
