"""
Gold Complete Pattern Analysis
Tests all 8 patterns (ICI + FOUS) on Gold with maximum historical data
Using GLD ETF for reliable data
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import yfinance as yf
from datetime import datetime
from ici_scanner import ICIScanner
from pattern_scanners import MomentumScanner, WMScanner, HarmonicScanner
from fous_scanners import ForceScanner, SurvivalScanner, RevivalScanner, GoldScanner

def load_gold_data(interval='1d', period='2y'):
    """Load Gold data from yfinance (using GLD ETF)"""
    print(f"\nLoading Gold data: {interval} timeframe, {period} period...")

    # Try GLD ETF first (more reliable), fallback to GC=F futures
    ticker = yf.Ticker('GLD')
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        print(f"GLD failed, trying GC=F futures...")
        ticker = yf.Ticker('GC=F')
        df = ticker.history(period=period, interval=interval)

    if df.empty:
        print(f"Warning: No data returned for {interval}")
        return None

    df.reset_index(inplace=True)

    # Handle both 'Date' and 'Datetime' column names
    if 'Datetime' in df.columns:
        df.rename(columns={'Datetime': 'Date'}, inplace=True)

    print(f"Loaded {len(df)} bars from {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
    return df

def test_ici_patterns_gold():
    """Test all ICI-based patterns on Gold"""
    print("\n" + "="*80)
    print("TESTING ICI PATTERNS ON GOLD")
    print("="*80)

    timeframes = [
        ('1d', '2y'),
        ('1h', '730d'),  # 730 days max for 1h
        ('15m', '60d'),  # 60 days max for 15m
    ]

    all_ici_results = []

    for interval, period in timeframes:
        print(f"\n{'='*80}")
        print(f"Testing {interval.upper()} timeframe")
        print(f"{'='*80}")

        df = load_gold_data(interval, period)
        if df is None or len(df) < 50:
            print(f"Skipping {interval} - insufficient data")
            continue

        # Test ICI
        print(f"\n--- ICI Scanner ---")
        ici_scanner = ICIScanner()
        ici_setups = ici_scanner.scan(df, timeframe=interval)
        valid_ici = [s for s in ici_setups if s.valid]
        print(f"ICI: {len(ici_setups)} total, {len(valid_ici)} valid")
        all_ici_results.extend(ici_setups)

        # Test Momentum (only on 1h)
        if interval == '1h':
            print(f"\n--- Momentum Scanner ---")
            mom_scanner = MomentumScanner()
            mom_setups = mom_scanner.scan(df, timeframe=interval)
            valid_mom = [s for s in mom_setups if s.valid]
            print(f"Momentum: {len(mom_setups)} total, {len(valid_mom)} valid")
            all_ici_results.extend(mom_setups)

        # Test W/M
        print(f"\n--- W/M Scanner ---")
        wm_scanner = WMScanner()
        wm_setups = wm_scanner.scan(df, timeframe=interval)
        valid_wm = [s for s in wm_setups if s.valid]
        print(f"W/M: {len(wm_setups)} total, {len(valid_wm)} valid")
        all_ici_results.extend(wm_setups)

        # Test Harmonic
        print(f"\n--- Harmonic Scanner ---")
        harm_scanner = HarmonicScanner()
        harm_setups = harm_scanner.scan(df, timeframe=interval)
        valid_harm = [s for s in harm_setups if s.valid]
        print(f"Harmonic: {len(harm_setups)} total, {len(valid_harm)} valid")
        all_ici_results.extend(harm_setups)

    return all_ici_results

def test_fous_patterns_gold():
    """Test all FOUS patterns on Gold"""
    print("\n" + "="*80)
    print("TESTING FOUS PATTERNS ON GOLD")
    print("="*80)

    timeframes = [
        ('1h', '730d'),
        ('15m', '60d'),
        ('5m', '60d'),
    ]

    all_fous_results = []

    for interval, period in timeframes:
        print(f"\n{'='*80}")
        print(f"Testing {interval.upper()} timeframe")
        print(f"{'='*80}")

        df = load_gold_data(interval, period)
        if df is None or len(df) < 50:
            print(f"Skipping {interval} - insufficient data")
            continue

        # Test Force
        print(f"\n--- Force Scanner ---")
        force_scanner = ForceScanner()
        force_setups = force_scanner.scan(df, timeframe=interval)
        valid_force = [s for s in force_setups if s.valid]
        print(f"Force: {len(force_setups)} total, {len(valid_force)} valid")
        all_fous_results.extend(force_setups)

        # Test Survival
        print(f"\n--- Survival Scanner ---")
        survival_scanner = SurvivalScanner()
        survival_setups = survival_scanner.scan(df, timeframe=interval)
        valid_survival = [s for s in survival_setups if s.valid]
        print(f"Survival: {len(survival_setups)} total, {len(valid_survival)} valid")
        all_fous_results.extend(survival_setups)

        # Test Revival
        print(f"\n--- Revival Scanner ---")
        revival_scanner = RevivalScanner()
        revival_setups = revival_scanner.scan(df, timeframe=interval)
        valid_revival = [s for s in revival_setups if s.valid]
        print(f"Revival: {len(revival_setups)} total, {len(valid_revival)} valid")
        all_fous_results.extend(revival_setups)

        # Test Gold Pattern
        print(f"\n--- Gold Pattern Scanner ---")
        gold_scanner = GoldScanner()
        gold_setups = gold_scanner.scan(df, timeframe=interval)
        valid_gold = [s for s in gold_setups if s.valid]
        print(f"Gold Pattern: {len(gold_setups)} total, {len(valid_gold)} valid")
        all_fous_results.extend(gold_setups)

    return all_fous_results

def export_results(ici_results, fous_results):
    """Export all results to CSV files"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Export ICI results
    if ici_results:
        ici_data = []
        for setup in ici_results:
            ici_data.append({
                'Date': setup.date,
                'Pattern': setup.pattern_type,
                'Timeframe': setup.timeframe,
                'Direction': 'LONG' if setup.is_bullish else 'SHORT',
                'Entry': setup.entry,
                'Stop': setup.stop,
                'Target': setup.target,
                'R:R': setup.risk_reward,
                'Correction%': setup.correction_pct,
                'EMA_Aligned': setup.ema_aligned,
                'MACD_Aligned': setup.macd_aligned,
                'Valid': setup.valid
            })

        df_ici = pd.DataFrame(ici_data)

        # All ICI setups
        filename_all = f'gold_ici_all_{timestamp}.csv'
        df_ici.to_csv(filename_all, index=False)
        print(f"\nExported all ICI setups to: {filename_all}")

        # Valid only
        df_valid = df_ici[df_ici['Valid'] == True]
        filename_valid = f'gold_ici_valid_{timestamp}.csv'
        df_valid.to_csv(filename_valid, index=False)
        print(f"Exported valid ICI setups to: {filename_valid}")

    # Export FOUS results
    if fous_results:
        fous_data = []
        for setup in fous_results:
            fous_data.append({
                'Date': setup.date,
                'Pattern': setup.pattern_type,
                'Timeframe': setup.timeframe,
                'Entry': setup.entry,
                'Stop': setup.stop,
                'Target': setup.target,
                'R:R': setup.risk_reward,
                'Volume_Spike': setup.volume_spike,
                'RSI': setup.rsi,
                'EMA_Aligned': setup.ema_aligned,
                'VWAP_Bullish': setup.vwap_bullish,
                'Valid': setup.valid
            })

        df_fous = pd.DataFrame(fous_data)

        # All FOUS setups
        filename_all = f'gold_fous_all_{timestamp}.csv'
        df_fous.to_csv(filename_all, index=False)
        print(f"\nExported all FOUS setups to: {filename_all}")

        # Valid only
        df_valid = df_fous[df_fous['Valid'] == True]
        filename_valid = f'gold_fous_valid_{timestamp}.csv'
        df_valid.to_csv(filename_valid, index=False)
        print(f"Exported valid FOUS setups to: {filename_valid}")

def print_summary(ici_results, fous_results):
    """Print comprehensive summary"""
    print("\n" + "="*80)
    print("GOLD ANALYSIS SUMMARY")
    print("="*80)

    # ICI Summary
    print("\n--- ICI PATTERNS SUMMARY ---")
    valid_ici = [s for s in ici_results if s.valid]
    print(f"Total ICI setups: {len(ici_results)}")
    print(f"Valid ICI setups: {len(valid_ici)} ({len(valid_ici)/len(ici_results)*100:.1f}%)")

    if valid_ici:
        avg_rr = sum(s.risk_reward for s in valid_ici) / len(valid_ici)
        print(f"Average R:R: {avg_rr:.2f}")
        best_setup = max(valid_ici, key=lambda s: s.risk_reward)
        print(f"Best R:R: {best_setup.risk_reward:.2f} ({best_setup.pattern_type} {best_setup.timeframe})")

    # By pattern type
    print("\nBy Pattern Type:")
    for pattern in ['ICI', 'Momentum', 'W/M', 'Harmonic']:
        pattern_setups = [s for s in ici_results if s.pattern_type == pattern]
        pattern_valid = [s for s in pattern_setups if s.valid]
        if pattern_setups:
            print(f"  {pattern}: {len(pattern_setups)} total, {len(pattern_valid)} valid ({len(pattern_valid)/len(pattern_setups)*100:.1f}%)")

    # By timeframe
    print("\nBy Timeframe:")
    for tf in ['1d', '1h', '15m']:
        tf_setups = [s for s in ici_results if s.timeframe == tf]
        tf_valid = [s for s in tf_setups if s.valid]
        if tf_setups:
            print(f"  {tf}: {len(tf_setups)} total, {len(tf_valid)} valid ({len(tf_valid)/len(tf_setups)*100:.1f}%)")

    # FOUS Summary
    print("\n--- FOUS PATTERNS SUMMARY ---")
    valid_fous = [s for s in fous_results if s.valid]
    print(f"Total FOUS setups: {len(fous_results)}")
    print(f"Valid FOUS setups: {len(valid_fous)} ({len(valid_fous)/len(fous_results)*100:.1f}%)")

    if valid_fous:
        avg_rr = sum(s.risk_reward for s in valid_fous) / len(valid_fous)
        print(f"Average R:R: {avg_rr:.2f}")
        best_setup = max(valid_fous, key=lambda s: s.risk_reward)
        print(f"Best R:R: {best_setup.risk_reward:.2f} ({best_setup.pattern_type} {best_setup.timeframe})")

    # By pattern type
    print("\nBy Pattern Type:")
    for pattern in ['Force', 'Survival', 'Revival', 'Gold']:
        pattern_setups = [s for s in fous_results if s.pattern_type == pattern]
        pattern_valid = [s for s in pattern_setups if s.valid]
        if pattern_setups:
            print(f"  {pattern}: {len(pattern_setups)} total, {len(pattern_valid)} valid ({len(pattern_valid)/len(pattern_setups)*100:.1f}%)")

    # By timeframe
    print("\nBy Timeframe:")
    for tf in ['1h', '15m', '5m']:
        tf_setups = [s for s in fous_results if s.timeframe == tf]
        tf_valid = [s for s in tf_setups if s.valid]
        if tf_setups:
            print(f"  {tf}: {len(tf_setups)} total, {len(tf_valid)} valid ({len(tf_valid)/len(tf_setups)*100:.1f}%)")

    # Grand Total
    print("\n" + "="*80)
    print("GRAND TOTAL (ALL 8 PATTERNS)")
    print("="*80)
    total_setups = len(ici_results) + len(fous_results)
    total_valid = len(valid_ici) + len(valid_fous)
    print(f"Total setups: {total_setups}")
    print(f"Valid setups: {total_valid} ({total_valid/total_setups*100:.1f}%)")

    if valid_ici or valid_fous:
        all_valid = valid_ici + valid_fous
        avg_rr = sum(s.risk_reward for s in all_valid) / len(all_valid)
        print(f"Combined average R:R: {avg_rr:.2f}")

if __name__ == "__main__":
    print("="*80)
    print("GOLD COMPLETE PATTERN ANALYSIS")
    print("Testing all 8 patterns: ICI, Momentum, W/M, Harmonic, Force, Survival, Revival, Gold")
    print("Using GLD ETF for reliable data")
    print("="*80)

    # Test ICI patterns
    ici_results = test_ici_patterns_gold()

    # Test FOUS patterns
    fous_results = test_fous_patterns_gold()

    # Print summary
    print_summary(ici_results, fous_results)

    # Export results
    export_results(ici_results, fous_results)

    print("\n" + "="*80)
    print("GOLD ANALYSIS COMPLETE!")
    print("="*80)
