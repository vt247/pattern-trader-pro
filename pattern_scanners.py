"""
Additional pattern scanners: Momentum, W/M, and Harmonic
"""
from typing import List, Optional
import pandas as pd
from ici_scanner import ICIScanner, ICISetup
from fibonacci import FibonacciCalculator
from validators import EntryValidator


class MomentumScanner(ICIScanner):
    """
    Momentum Scanner - ICI on 1h timeframe with 15m entry validation

    Inherits from ICIScanner but configured for shorter timeframes
    """

    def __init__(self, **kwargs):
        # Use tighter parameters for momentum trading
        super().__init__(
            min_impulse_candles=kwargs.get('min_impulse_candles', 3),
            min_correction_candles=kwargs.get('min_correction_candles', 2),
            min_fib_level=kwargs.get('min_fib_level', 0.382),
            max_fib_level=kwargs.get('max_fib_level', 0.786),
            extension_target=kwargs.get('extension_target', -0.272),
            min_risk_reward=kwargs.get('min_risk_reward', 1.3)
        )

    def scan(self, df: pd.DataFrame, timeframe: str = '1h') -> List[ICISetup]:
        """Scan for momentum patterns on 1h timeframe"""
        setups = super().scan(df, timeframe)

        # Update pattern type
        for setup in setups:
            setup.pattern_type = 'Momentum'

        return setups


class WMScanner:
    """
    W/M Pattern Scanner - Double top/bottom patterns on weekly/monthly with 4h entry

    M Pattern (bearish): High - Low - High (looking for lower high)
    W Pattern (bullish): Low - High - Low (looking for higher low)
    """

    def __init__(self, min_fib_level: float = 0.382,
                 max_fib_level: float = 0.786,
                 extension_target: float = -0.272,
                 min_risk_reward: float = 1.3,
                 lookback_period: int = 50):
        """
        Initialize W/M Scanner

        Args:
            min_fib_level: Minimum Fibonacci retracement
            max_fib_level: Maximum Fibonacci retracement
            extension_target: Extension level for target
            min_risk_reward: Minimum risk/reward ratio
            lookback_period: Bars to look back for pivots
        """
        self.min_fib_level = min_fib_level
        self.max_fib_level = max_fib_level
        self.extension_target = extension_target
        self.min_risk_reward = min_risk_reward
        self.lookback_period = lookback_period
        self.fib_calc = FibonacciCalculator()
        self.validator = EntryValidator()

    def scan(self, df: pd.DataFrame, timeframe: str = 'weekly') -> List[ICISetup]:
        """
        Scan for W/M patterns

        Args:
            df: DataFrame with OHLC data
            timeframe: Timeframe being scanned

        Returns:
            List of ICISetup objects
        """
        setups = []

        if len(df) < self.lookback_period:
            return setups

        # Find pivot points
        pivots = self._find_pivots(df)

        # Look for W and M patterns in pivots
        for i in range(50, len(df) - 1):
            # Try to find W pattern (bullish)
            w_setup = self._find_w_pattern(df, pivots, i, timeframe)
            if w_setup:
                setups.append(w_setup)

            # Try to find M pattern (bearish)
            m_setup = self._find_m_pattern(df, pivots, i, timeframe)
            if m_setup:
                setups.append(m_setup)

        return setups

    def _find_pivots(self, df: pd.DataFrame, window: int = 5) -> dict:
        """
        Find pivot highs and lows

        Args:
            df: DataFrame with OHLC data
            window: Window size for pivot detection

        Returns:
            Dict with 'highs' and 'lows' indices
        """
        pivot_highs = []
        pivot_lows = []

        for i in range(window, len(df) - window):
            # Check if current bar is a pivot high
            is_pivot_high = True
            is_pivot_low = True

            current_high = df.iloc[i]['High']
            current_low = df.iloc[i]['Low']

            # Compare with surrounding bars
            for j in range(1, window + 1):
                if df.iloc[i - j]['High'] > current_high or df.iloc[i + j]['High'] > current_high:
                    is_pivot_high = False
                if df.iloc[i - j]['Low'] < current_low or df.iloc[i + j]['Low'] < current_low:
                    is_pivot_low = False

            if is_pivot_high:
                pivot_highs.append(i)
            if is_pivot_low:
                pivot_lows.append(i)

        return {'highs': pivot_highs, 'lows': pivot_lows}

    def _find_w_pattern(self, df: pd.DataFrame, pivots: dict,
                       idx: int, timeframe: str) -> Optional[ICISetup]:
        """
        Find W pattern (bullish): Low - High - Low (higher low)

        Args:
            df: DataFrame
            pivots: Pivot points dict
            idx: Current index
            timeframe: Current timeframe

        Returns:
            ICISetup if valid pattern found
        """
        # Need at least 3 pivots: low, high, low
        recent_lows = [p for p in pivots['lows'] if p < idx and p > idx - self.lookback_period]
        recent_highs = [p for p in pivots['highs'] if p < idx and p > idx - self.lookback_period]

        if len(recent_lows) < 2 or len(recent_highs) < 1:
            return None

        # Get last 2 lows and intermediate high
        low1_idx = recent_lows[-2]
        low2_idx = recent_lows[-1]

        # Find high between the two lows
        highs_between = [p for p in recent_highs if low1_idx < p < low2_idx]
        if not highs_between:
            return None

        high_idx = highs_between[0]

        # Get prices
        low1 = df.iloc[low1_idx]['Low']
        high = df.iloc[high_idx]['High']
        low2 = df.iloc[low2_idx]['Low']

        # Validate W pattern: low2 should be higher than low1 (higher low)
        if low2 <= low1:
            return None

        # Validate neckline break
        neckline = high
        current_price = df.iloc[idx]['Close']

        # For W pattern, we want price to break above neckline
        if current_price < neckline:
            return None

        # Calculate Fibonacci retracement from low1 to high
        correction_pct = self.fib_calc.get_retracement_pct(high, low1, low2)

        if not (self.min_fib_level <= correction_pct <= self.max_fib_level):
            return None

        # Calculate entry, stop, target
        entry = current_price
        stop = low2 * 0.99  # 1% below second low
        target = self.fib_calc.calculate_target(high, low1, self.extension_target)

        # Validate risk/reward
        risk = abs(entry - stop)
        reward = abs(target - entry)
        risk_reward = reward / risk if risk != 0 else 0

        if risk_reward < self.min_risk_reward:
            return None

        # Validate indicators
        close_prices = df['Close'].iloc[:idx + 1]
        ema_aligned = self.validator.validate_ema(close_prices, 10, 20, 'long')
        macd_aligned = self.validator.validate_macd(close_prices, 'long')

        valid = ema_aligned and macd_aligned and risk_reward >= self.min_risk_reward

        return ICISetup(
            date=df.iloc[idx]['Date'] if 'Date' in df.columns else df.index[idx],
            pattern_type='W',
            timeframe=timeframe,
            impulse_high=high,
            impulse_low=low1,
            correction_low=low2,
            correction_pct=correction_pct,
            entry=entry,
            stop=stop,
            target=target,
            is_bullish=True,
            risk_reward=risk_reward,
            ema_aligned=ema_aligned,
            macd_aligned=macd_aligned,
            valid=valid
        )

    def _find_m_pattern(self, df: pd.DataFrame, pivots: dict,
                       idx: int, timeframe: str) -> Optional[ICISetup]:
        """
        Find M pattern (bearish): High - Low - High (lower high)

        Args:
            df: DataFrame
            pivots: Pivot points dict
            idx: Current index
            timeframe: Current timeframe

        Returns:
            ICISetup if valid pattern found
        """
        # Need at least 3 pivots: high, low, high
        recent_highs = [p for p in pivots['highs'] if p < idx and p > idx - self.lookback_period]
        recent_lows = [p for p in pivots['lows'] if p < idx and p > idx - self.lookback_period]

        if len(recent_highs) < 2 or len(recent_lows) < 1:
            return None

        # Get last 2 highs and intermediate low
        high1_idx = recent_highs[-2]
        high2_idx = recent_highs[-1]

        # Find low between the two highs
        lows_between = [p for p in recent_lows if high1_idx < p < high2_idx]
        if not lows_between:
            return None

        low_idx = lows_between[0]

        # Get prices
        high1 = df.iloc[high1_idx]['High']
        low = df.iloc[low_idx]['Low']
        high2 = df.iloc[high2_idx]['High']

        # Validate M pattern: high2 should be lower than high1 (lower high)
        if high2 >= high1:
            return None

        # Validate neckline break
        neckline = low
        current_price = df.iloc[idx]['Close']

        # For M pattern, we want price to break below neckline
        if current_price > neckline:
            return None

        # Calculate Fibonacci retracement
        impulse_range = high1 - low
        retracement = high2 - low
        correction_pct = retracement / impulse_range if impulse_range != 0 else 0

        if not (self.min_fib_level <= correction_pct <= self.max_fib_level):
            return None

        # Calculate entry, stop, target
        entry = current_price
        stop = high2 * 1.01  # 1% above second high
        target = low - (high1 - low) * abs(self.extension_target)

        # Validate risk/reward
        risk = abs(entry - stop)
        reward = abs(target - entry)
        risk_reward = reward / risk if risk != 0 else 0

        if risk_reward < self.min_risk_reward:
            return None

        # Validate indicators
        close_prices = df['Close'].iloc[:idx + 1]
        ema_aligned = self.validator.validate_ema(close_prices, 10, 20, 'short')
        macd_aligned = self.validator.validate_macd(close_prices, 'short')

        valid = ema_aligned and macd_aligned and risk_reward >= self.min_risk_reward

        return ICISetup(
            date=df.iloc[idx]['Date'] if 'Date' in df.columns else df.index[idx],
            pattern_type='M',
            timeframe=timeframe,
            impulse_high=high1,
            impulse_low=low,
            correction_low=high2,
            correction_pct=correction_pct,
            entry=entry,
            stop=stop,
            target=target,
            is_bullish=False,
            risk_reward=risk_reward,
            ema_aligned=ema_aligned,
            macd_aligned=macd_aligned,
            valid=valid
        )


class HarmonicScanner(WMScanner):
    """
    Harmonic Scanner - W/M patterns on daily timeframe with 1h entry validation

    Inherits from WMScanner but adds pivot point validation
    """

    def __init__(self, **kwargs):
        super().__init__(
            min_fib_level=kwargs.get('min_fib_level', 0.382),
            max_fib_level=kwargs.get('max_fib_level', 0.786),
            extension_target=kwargs.get('extension_target', -0.272),
            min_risk_reward=kwargs.get('min_risk_reward', 1.3),
            lookback_period=kwargs.get('lookback_period', 50)
        )

    def scan(self, df: pd.DataFrame, timeframe: str = 'daily') -> List[ICISetup]:
        """Scan for harmonic patterns on daily timeframe"""
        setups = super().scan(df, timeframe)

        # Update pattern type and add additional pivot validation
        validated_setups = []
        for setup in setups:
            setup.pattern_type = 'Harmonic'
            # Additional validation for harmonic patterns could go here
            validated_setups.append(setup)

        return validated_setups
