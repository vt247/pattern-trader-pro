"""
FOUS Patterns Test - Force, Survival, Revival, Gold
Test on S&P 500 (SPY) same timeperiod as ICI patterns
"""
import pandas as pd
from datetime import datetime
from data_loader import DataLoader
from fous_scanners import ForceScanner, SurvivalScanner, RevivalScanner, GoldScanner
import warnings
warnings.filterwarnings('ignore')


def analyze_fous_setups(setups: list, pattern_name: str):
    """Analyze FOUS setups"""
    if not setups:
        print(f"\n  ❌ No {pattern_name} patterns found")
        return {
            'pattern': pattern_name,
            'total': 0,
            'valid': 0,
            'validity_pct': 0,
            'avg_rr': 0,
            'max_rr': 0
        }

    valid = [s for s in setups if s.valid]

    print(f"\n  📊 {pattern_name} Analysis:")
    print(f"     Total setups: {len(setups)}")
    print(f"     Valid setups: {len(valid)} ({len(valid)/len(setups)*100:.1f}%)")

    stats = {
        'pattern': pattern_name,
        'total': len(setups),
        'valid': len(valid),
        'validity_pct': len(valid)/len(setups)*100 if setups else 0,
        'avg_rr': 0,
        'max_rr': 0,
        'min_rr': 0
    }

    if valid:
        rr_ratios = [s.risk_reward for s in valid]

        stats['avg_rr'] = sum(rr_ratios) / len(rr_ratios)
        stats['max_rr'] = max(rr_ratios)
        stats['min_rr'] = min(rr_ratios)

        print(f"\n     Risk/Reward:")
        print(f"       Average: {stats['avg_rr']:.2f}")
        print(f"       Min: {stats['min_rr']:.2f}")
        print(f"       Max: {stats['max_rr']:.2f}")

        # Volume and RSI stats
        volume_spike_count = len([s for s in valid if s.volume_spike])
        ema_aligned_count = len([s for s in valid if s.ema_aligned])
        vwap_bullish_count = len([s for s in valid if s.vwap_bullish])

        print(f"\n     Indicators:")
        print(f"       Volume Spike: {volume_spike_count}/{len(valid)} ({volume_spike_count/len(valid)*100:.1f}%)")
        print(f"       EMA Aligned: {ema_aligned_count}/{len(valid)} ({ema_aligned_count/len(valid)*100:.1f}%)")
        print(f"       VWAP Bullish: {vwap_bullish_count}/{len(valid)} ({vwap_bullish_count/len(valid)*100:.1f}%)")

        # Show top 3
        print(f"\n     🏆 Top 3 by R:R:")
        sorted_valid = sorted(valid, key=lambda s: s.risk_reward, reverse=True)[:3]
        for i, s in enumerate(sorted_valid, 1):
            date_str = s.date.strftime('%Y-%m-%d %H:%M') if hasattr(s.date, 'hour') else s.date.strftime('%Y-%m-%d')
            rsi_str = f"RSI {s.rsi:.0f}" if s.rsi else "RSI N/A"
            print(f"       {i}. {date_str} | R:R {s.risk_reward:.2f} | {rsi_str} | {s.notes[:40]}")

    return stats


def main():
    print("=" * 100)
    print(" " * 25 + "🔥 FOUS PATTERNS TEST - S&P 500 🔥")
    print("=" * 100)
    print("\nPatterns: Force, Survival, Revival, Gold")
    print("Same data as ICI test for comparison")

    # Load maximum data for all timeframes
    print("\n" + "=" * 100)
    print(" " * 35 + "📥 LOADING DATA")
    print("=" * 100)

    try:
        import yfinance as yf

        # Load different timeframes
        print("\n Loading 1 Hour data (730 days)...")
        ticker = yf.Ticker('SPY')
        df_1h = ticker.history(period='730d', interval='1h')
        df_1h.reset_index(inplace=True)
        if 'Datetime' in df_1h.columns:
            df_1h.rename(columns={'Datetime': 'Date'}, inplace=True)
        print(f"   ✓ Loaded {len(df_1h)} bars")

        print("\n📥 Loading 15 Minute data (60 days)...")
        df_15m = ticker.history(period='60d', interval='15m')
        df_15m.reset_index(inplace=True)
        if 'Datetime' in df_15m.columns:
            df_15m.rename(columns={'Datetime': 'Date'}, inplace=True)
        print(f"   ✓ Loaded {len(df_15m)} bars")

        print("\n📥 Loading 5 Minute data (60 days)...")
        df_5m = ticker.history(period='60d', interval='5m')
        df_5m.reset_index(inplace=True)
        if 'Datetime' in df_5m.columns:
            df_5m.rename(columns={'Datetime': 'Date'}, inplace=True)
        print(f"   ✓ Loaded {len(df_5m)} bars")

    except Exception as e:
        print(f"   ✗ Error loading data: {e}")
        return

    # Initialize scanners
    print("\n" + "=" * 100)
    print(" " * 35 + "🔧 INITIALIZING SCANNERS")
    print("=" * 100)

    force_scanner = ForceScanner()
    survival_scanner = SurvivalScanner()
    revival_scanner = RevivalScanner()
    gold_scanner = GoldScanner()

    print("\n   ✓ All FOUS scanners initialized")

    # Scan patterns
    print("\n" + "=" * 100)
    print(" " * 30 + "🔍 SCANNING FOUS PATTERNS")
    print("=" * 100)

    all_stats = []

    # 1 Hour timeframe
    print(f"\n{'─' * 100}")
    print("🔍 Scanning 1 HOUR timeframe...")
    print(f"{'─' * 100}")

    print("\n1. FORCE Pattern (1H):")
    force_1h = force_scanner.scan(df_1h, '1h')
    stats_force_1h = analyze_fous_setups(force_1h, 'Force 1H')
    all_stats.append(stats_force_1h)

    print("\n2. SURVIVAL Pattern (1H):")
    survival_1h = survival_scanner.scan(df_1h, '1h')
    stats_survival_1h = analyze_fous_setups(survival_1h, 'Survival 1H')
    all_stats.append(stats_survival_1h)

    print("\n3. REVIVAL Pattern (1H):")
    revival_1h = revival_scanner.scan(df_1h, '1h')
    stats_revival_1h = analyze_fous_setups(revival_1h, 'Revival 1H')
    all_stats.append(stats_revival_1h)

    print("\n4. GOLD Pattern (1H):")
    gold_1h = gold_scanner.scan(df_1h, '1h')
    stats_gold_1h = analyze_fous_setups(gold_1h, 'Gold 1H')
    all_stats.append(stats_gold_1h)

    # 15 Minute timeframe
    print(f"\n{'─' * 100}")
    print("🔍 Scanning 15 MINUTE timeframe...")
    print(f"{'─' * 100}")

    print("\n1. FORCE Pattern (15M):")
    force_15m = force_scanner.scan(df_15m, '15m')
    stats_force_15m = analyze_fous_setups(force_15m, 'Force 15M')
    all_stats.append(stats_force_15m)

    print("\n2. SURVIVAL Pattern (15M):")
    survival_15m = survival_scanner.scan(df_15m, '15m')
    stats_survival_15m = analyze_fous_setups(survival_15m, 'Survival 15M')
    all_stats.append(stats_survival_15m)

    print("\n3. REVIVAL Pattern (15M):")
    revival_15m = revival_scanner.scan(df_15m, '15m')
    stats_revival_15m = analyze_fous_setups(revival_15m, 'Revival 15M')
    all_stats.append(stats_revival_15m)

    print("\n4. GOLD Pattern (15M):")
    gold_15m = gold_scanner.scan(df_15m, '15m')
    stats_gold_15m = analyze_fous_setups(gold_15m, 'Gold 15M')
    all_stats.append(stats_gold_15m)

    # 5 Minute timeframe
    print(f"\n{'─' * 100}")
    print("🔍 Scanning 5 MINUTE timeframe...")
    print(f"{'─' * 100}")

    print("\n1. FORCE Pattern (5M):")
    force_5m = force_scanner.scan(df_5m, '5m')
    stats_force_5m = analyze_fous_setups(force_5m, 'Force 5M')
    all_stats.append(stats_force_5m)

    print("\n2. SURVIVAL Pattern (5M):")
    survival_5m = survival_scanner.scan(df_5m, '5m')
    stats_survival_5m = analyze_fous_setups(survival_5m, 'Survival 5M')
    all_stats.append(stats_survival_5m)

    print("\n3. REVIVAL Pattern (5M):")
    revival_5m = revival_scanner.scan(df_5m, '5m')
    stats_revival_5m = analyze_fous_setups(revival_5m, 'Revival 5M')
    all_stats.append(stats_revival_5m)

    print("\n4. GOLD Pattern (5M):")
    gold_5m = gold_scanner.scan(df_5m, '5m', df_15m)
    stats_gold_5m = analyze_fous_setups(gold_5m, 'Gold 5M')
    all_stats.append(stats_gold_5m)

    # Summary table
    print("\n" + "=" * 100)
    print(" " * 30 + "📊 FOUS PATTERNS SUMMARY")
    print("=" * 100)

    print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ Pattern      │ TF  │ Total │ Valid │ Valid% │ Avg RR │ Max RR │ Status     │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")

    for stats in all_stats:
        pattern = stats['pattern'].split()[0][:12]
        tf = stats['pattern'].split()[-1] if len(stats['pattern'].split()) > 1 else ''
        status = "✅ Found" if stats['valid'] > 0 else "❌ None"

        print(f"│ {pattern:12s} │ {tf:3s} │ {stats['total']:5d} │ {stats['valid']:5d} │ "
              f"{stats['validity_pct']:5.1f}% │ {stats['avg_rr']:6.2f} │ "
              f"{stats['max_rr']:6.2f} │ {status:10s} │")

    print("└─────────────────────────────────────────────────────────────────────────────┘")

    # Grand totals
    total_setups = sum(s['total'] for s in all_stats)
    total_valid = sum(s['valid'] for s in all_stats)

    print(f"\n🎯 GRAND TOTAL:")
    print(f"   Total setups found: {total_setups}")
    print(f"   Valid setups: {total_valid} ({total_valid/total_setups*100:.1f}%)" if total_setups > 0 else "   Valid setups: 0")

    # Export results
    print("\n" + "=" * 100)
    print(" " * 35 + "💾 EXPORTING RESULTS")
    print("=" * 100)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Combine all valid setups
    all_valid_setups = []
    for setups in [force_1h, survival_1h, revival_1h, gold_1h,
                   force_15m, survival_15m, revival_15m, gold_15m,
                   force_5m, survival_5m, revival_5m, gold_5m]:
        all_valid_setups.extend([s for s in setups if s.valid])

    if all_valid_setups:
        csv_file = f'fous_patterns_valid_{timestamp}.csv'
        df_export = pd.DataFrame([s.to_dict() for s in all_valid_setups])
        df_export.sort_values(['Pattern', 'Date'], inplace=True)
        df_export.to_csv(csv_file, index=False)
        print(f"\n✓ Exported {len(all_valid_setups)} valid FOUS setups to: {csv_file}")
    else:
        print("\n⚠ No valid setups to export")

    print("\n" + "=" * 100)
    print(" " * 35 + "✅ FOUS TEST COMPLETE!")
    print("=" * 100)

    # Key insights
    print("\n🔑 KEY INSIGHTS:")

    pattern_totals = {}
    for stats in all_stats:
        pattern = stats['pattern'].split()[0]
        if pattern not in pattern_totals:
            pattern_totals[pattern] = {'total': 0, 'valid': 0}
        pattern_totals[pattern]['total'] += stats['total']
        pattern_totals[pattern]['valid'] += stats['valid']

    for pattern, counts in sorted(pattern_totals.items()):
        if counts['valid'] > 0:
            print(f"   • {pattern}: {counts['valid']} valid setups found")
        else:
            print(f"   • {pattern}: No valid setups found")

    print("\n" + "=" * 100 + "\n")


if __name__ == '__main__':
    main()
