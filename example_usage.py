"""
Example usage of the S&P 500 Pattern Scanner
"""
from data_loader import load_spy_data, DataLoader
from ici_scanner import ICIScanner
from pattern_scanners import MomentumScanner, WMScanner, HarmonicScanner
from fibonacci import FibonacciCalculator
from validators import EntryValidator


def example_1_basic_ici_scan():
    """Example 1: Basic ICI pattern scanning"""
    print("=" * 80)
    print("EXAMPLE 1: Basic ICI Pattern Scanning")
    print("=" * 80)

    # Load SPY data
    print("\nLoading SPY data...")
    df = load_spy_data(source='yfinance', period='1y', interval='1d')

    # Create scanner
    scanner = ICIScanner(
        min_impulse_candles=3,
        min_correction_candles=2,
        min_fib_level=0.382,
        max_fib_level=0.786,
        min_risk_reward=1.3
    )

    # Scan for patterns
    print("Scanning for ICI patterns...")
    setups = scanner.scan(df, timeframe='daily')

    # Filter valid setups
    valid_setups = [s for s in setups if s.valid]

    print(f"\nFound {len(setups)} total setups")
    print(f"Valid setups: {len(valid_setups)}")

    # Show first valid setup
    if valid_setups:
        setup = valid_setups[0]
        print(f"\nExample setup:")
        print(f"  Date: {setup.date}")
        print(f"  Direction: {'LONG' if setup.is_bullish else 'SHORT'}")
        print(f"  Entry: ${setup.entry:.2f}")
        print(f"  Stop: ${setup.stop:.2f}")
        print(f"  Target: ${setup.target:.2f}")
        print(f"  R:R: {setup.risk_reward:.2f}")


def example_2_fibonacci_calculations():
    """Example 2: Fibonacci calculations"""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Fibonacci Calculations")
    print("=" * 80)

    fib = FibonacciCalculator()

    # Example bullish move
    impulse_high = 100.0
    impulse_low = 90.0

    print(f"\nImpulse move: ${impulse_low:.2f} -> ${impulse_high:.2f}")
    print("\nRetracement levels:")

    for level_name, level_value in fib.RETRACEMENT_LEVELS.items():
        price = fib.calculate_retracement(impulse_high, impulse_low, level_value)
        print(f"  {level_name} ({level_value}): ${price:.2f}")

    print("\nExtension targets:")
    for level_name, level_value in fib.EXTENSION_LEVELS.items():
        price = fib.calculate_extension(impulse_high, impulse_low, level_value)
        print(f"  {level_name} ({level_value}): ${price:.2f}")

    # Check if correction is valid
    correction_price = 94.0
    is_valid = fib.is_valid_correction(impulse_high, impulse_low, correction_price)
    correction_pct = fib.get_retracement_pct(impulse_high, impulse_low, correction_price)

    print(f"\nCorrection to ${correction_price:.2f}:")
    print(f"  Retracement: {correction_pct:.3f} ({correction_pct*100:.1f}%)")
    print(f"  Valid (0.382-0.786): {is_valid}")


def example_3_multi_timeframe():
    """Example 3: Multi-timeframe scanning"""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Multi-Timeframe Scanning")
    print("=" * 80)

    # Load daily data
    print("\nLoading SPY daily data...")
    df_daily = load_spy_data(source='yfinance', period='2y', interval='1d')

    # Create loader for resampling
    loader = DataLoader()

    # Scan on daily
    scanner = ICIScanner()
    daily_setups = scanner.scan(df_daily, 'daily')
    print(f"Daily timeframe: {len(daily_setups)} setups")

    # Resample to weekly
    df_weekly = loader.resample_to_timeframe(df_daily, '1W')
    weekly_setups = scanner.scan(df_weekly, 'weekly')
    print(f"Weekly timeframe: {len(weekly_setups)} setups")

    # Resample to monthly
    df_monthly = loader.resample_to_timeframe(df_daily, '1M')
    monthly_setups = scanner.scan(df_monthly, 'monthly')
    print(f"Monthly timeframe: {len(monthly_setups)} setups")


def example_4_w_m_patterns():
    """Example 4: W and M pattern detection"""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 4: W/M Pattern Detection")
    print("=" * 80)

    # Load data
    print("\nLoading SPY data...")
    df = load_spy_data(source='yfinance', period='2y', interval='1d')

    # Resample to weekly for W/M patterns
    loader = DataLoader()
    df_weekly = loader.resample_to_timeframe(df, '1W')

    # Create W/M scanner
    wm_scanner = WMScanner()

    # Scan for patterns
    print("Scanning for W/M patterns on weekly timeframe...")
    wm_setups = wm_scanner.scan(df_weekly, 'weekly')

    w_patterns = [s for s in wm_setups if s.is_bullish]
    m_patterns = [s for s in wm_setups if not s.is_bullish]

    print(f"\nW patterns (bullish): {len(w_patterns)}")
    print(f"M patterns (bearish): {len(m_patterns)}")


def example_5_custom_parameters():
    """Example 5: Custom scanner parameters"""
    print("\n\n" + "=" * 80)
    print("EXAMPLE 5: Custom Scanner Parameters")
    print("=" * 80)

    # Load data
    df = load_spy_data(source='yfinance', period='1y', interval='1d')

    # Create conservative scanner (tighter parameters)
    print("\n1. Conservative scanner (tighter Fib range, higher R:R):")
    conservative_scanner = ICIScanner(
        min_impulse_candles=4,  # Longer impulse
        min_correction_candles=3,  # Longer correction
        min_fib_level=0.500,  # Tighter range
        max_fib_level=0.618,
        min_risk_reward=2.0  # Higher R:R requirement
    )

    conservative_setups = conservative_scanner.scan(df, 'daily')
    print(f"   Found {len(conservative_setups)} setups")

    # Create aggressive scanner (wider parameters)
    print("\n2. Aggressive scanner (wider Fib range, lower R:R):")
    aggressive_scanner = ICIScanner(
        min_impulse_candles=2,  # Shorter impulse
        min_correction_candles=2,
        min_fib_level=0.382,  # Wider range
        max_fib_level=0.786,
        min_risk_reward=1.0  # Lower R:R requirement
    )

    aggressive_setups = aggressive_scanner.scan(df, 'daily')
    print(f"   Found {len(aggressive_setups)} setups")


if __name__ == '__main__':
    # Run all examples
    example_1_basic_ici_scan()
    example_2_fibonacci_calculations()
    example_3_multi_timeframe()
    example_4_w_m_patterns()
    example_5_custom_parameters()

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 80)
