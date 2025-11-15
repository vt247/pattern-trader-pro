"""
ICI (Impulse-Correction-Impulse) Pattern Scanner
"""
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from typing import List, Optional
from fibonacci import FibonacciCalculator
from validators import EntryValidator


@dataclass
class ICISetup:
    """Represents an ICI pattern setup"""
    date: datetime
    pattern_type: str  # 'ICI', 'Momentum', 'W/M', 'Harmonic'
    timeframe: str  # 'daily', 'weekly', 'monthly', '1h', '4h'
    impulse_high: float
    impulse_low: float
    correction_low: float  # For bullish (or correction_high for bearish)
    correction_pct: float  # Fibonacci retracement percentage
    entry: float
    stop: float
    target: float
    is_bullish: bool
    risk_reward: float
    ema_aligned: bool
    macd_aligned: bool
    valid: bool  # Overall validation status

    def to_dict(self):
        """Convert to dictionary for CSV export"""
        return {
            'Date': self.date,
            'Pattern': self.pattern_type,
            'Timeframe': self.timeframe,
            'Direction': 'LONG' if self.is_bullish else 'SHORT',
            'Entry': round(self.entry, 2),
            'Stop': round(self.stop, 2),
            'Target': round(self.target, 2),
            'Correction_Pct': round(self.correction_pct, 3),
            'Risk_Reward': round(self.risk_reward, 2),
            'EMA_Aligned': self.ema_aligned,
            'MACD_Aligned': self.macd_aligned,
            'Valid': self.valid
        }


class ICIScanner:
    """
    Scan for ICI (Impulse-Correction-Impulse) patterns

    Pattern structure:
    1. Impulse: N consecutive same-color candles
    2. Correction: N consecutive opposite-color candles with 0.382-0.786 retracement
    3. Ready for second impulse (entry setup)
    """

    def __init__(self, min_impulse_candles: int = 3,
                 min_correction_candles: int = 2,
                 min_fib_level: float = 0.382,
                 max_fib_level: float = 0.786,
                 extension_target: float = -0.272,
                 min_risk_reward: float = 1.3):
        """
        Initialize ICI Scanner

        Args:
            min_impulse_candles: Minimum candles for impulse move
            min_correction_candles: Minimum candles for correction
            min_fib_level: Minimum Fibonacci retracement
            max_fib_level: Maximum Fibonacci retracement
            extension_target: Extension level for target
            min_risk_reward: Minimum risk/reward ratio
        """
        self.min_impulse_candles = min_impulse_candles
        self.min_correction_candles = min_correction_candles
        self.min_fib_level = min_fib_level
        self.max_fib_level = max_fib_level
        self.extension_target = extension_target
        self.min_risk_reward = min_risk_reward
        self.fib_calc = FibonacciCalculator()
        self.validator = EntryValidator()

    def scan(self, df: pd.DataFrame, timeframe: str = 'daily') -> List[ICISetup]:
        """
        Scan DataFrame for ICI patterns

        Args:
            df: DataFrame with OHLC data (columns: Open, High, Low, Close, Date)
            timeframe: Timeframe being scanned

        Returns:
            List of ICISetup objects
        """
        setups = []

        # Need enough data for pattern + indicators
        if len(df) < 50:
            return setups

        # Scan through dataframe
        for i in range(50, len(df) - 1):  # Leave room for entry validation
            # Try to find bullish ICI
            bullish_setup = self._find_ici_at_index(df, i, True, timeframe)
            if bullish_setup:
                setups.append(bullish_setup)

            # Try to find bearish ICI
            bearish_setup = self._find_ici_at_index(df, i, False, timeframe)
            if bearish_setup:
                setups.append(bearish_setup)

        return setups

    def _find_ici_at_index(self, df: pd.DataFrame, idx: int,
                          bullish: bool, timeframe: str) -> Optional[ICISetup]:
        """
        Try to find ICI pattern ending at given index

        Args:
            df: DataFrame with OHLC data
            idx: Current index to check
            bullish: True for bullish pattern
            timeframe: Current timeframe

        Returns:
            ICISetup if valid pattern found, None otherwise
        """
        # Step 1: Find impulse move (working backwards from idx)
        impulse_end_idx = idx - self.min_correction_candles
        if impulse_end_idx < self.min_impulse_candles:
            return None

        # Count impulse candles backwards
        impulse_candles = 0
        impulse_start_idx = impulse_end_idx

        for i in range(impulse_end_idx, max(0, impulse_end_idx - 20), -1):
            if self.validator.is_same_color_candle(df.iloc[i], bullish):
                impulse_candles += 1
                impulse_start_idx = i
            else:
                break

        if impulse_candles < self.min_impulse_candles:
            return None

        # Step 2: Get impulse high/low
        impulse_data = df.iloc[impulse_start_idx:impulse_end_idx + 1]
        if bullish:
            impulse_high = impulse_data['High'].max()
            impulse_low = impulse_data['Low'].min()
        else:
            impulse_high = impulse_data['High'].max()
            impulse_low = impulse_data['Low'].min()

        # Step 3: Find correction move
        correction_data = df.iloc[impulse_end_idx + 1:idx + 1]
        if len(correction_data) < self.min_correction_candles:
            return None

        # Check if correction candles are opposite color
        correction_candles = 0
        for _, row in correction_data.iterrows():
            if self.validator.is_same_color_candle(row, not bullish):
                correction_candles += 1

        if correction_candles < self.min_correction_candles:
            return None

        # Step 4: Validate Fibonacci retracement
        if bullish:
            correction_low = correction_data['Low'].min()
            correction_pct = self.fib_calc.get_retracement_pct(
                impulse_high, impulse_low, correction_low
            )
            is_valid_fib = self.min_fib_level <= correction_pct <= self.max_fib_level
        else:
            correction_high = correction_data['High'].max()
            # For bearish: retracement is upward from impulse_low to correction_high
            correction_pct = self.fib_calc.get_retracement_pct(
                impulse_low, impulse_high, impulse_low + (impulse_low - correction_high)
            )
            # Reverse calculation for bearish
            impulse_range = impulse_high - impulse_low
            retracement = correction_high - impulse_low
            correction_pct = retracement / impulse_range if impulse_range != 0 else 0
            is_valid_fib = self.min_fib_level <= correction_pct <= self.max_fib_level

        if not is_valid_fib:
            return None

        # Step 5: Calculate entry, stop, target
        current_bar = df.iloc[idx]

        if bullish:
            entry = current_bar['Close']
            stop = correction_low - (impulse_high - impulse_low) * 0.05  # 5% buffer
            target = self.fib_calc.calculate_target(impulse_high, impulse_low,
                                                   self.extension_target)
        else:
            entry = current_bar['Close']
            stop = correction_high + (impulse_high - impulse_low) * 0.05  # 5% buffer
            # For bearish: target is below impulse_low
            target = impulse_low - (impulse_high - impulse_low) * abs(self.extension_target)

        # Step 6: Validate risk/reward
        risk = abs(entry - stop)
        reward = abs(target - entry)
        risk_reward = reward / risk if risk != 0 else 0

        if risk_reward < self.min_risk_reward:
            return None

        # Step 7: Validate EMA and MACD
        close_prices = df['Close'].iloc[:idx + 1]
        direction = 'long' if bullish else 'short'

        ema_aligned = self.validator.validate_ema(close_prices, 10, 20, direction)
        macd_aligned = self.validator.validate_macd(close_prices, direction)

        # Overall validation
        valid = is_valid_fib and risk_reward >= self.min_risk_reward and ema_aligned and macd_aligned

        # Step 8: Create setup
        setup = ICISetup(
            date=df.iloc[idx]['Date'] if 'Date' in df.columns else df.index[idx],
            pattern_type='ICI',
            timeframe=timeframe,
            impulse_high=impulse_high,
            impulse_low=impulse_low,
            correction_low=correction_low if bullish else correction_high,
            correction_pct=correction_pct,
            entry=entry,
            stop=stop,
            target=target,
            is_bullish=bullish,
            risk_reward=risk_reward,
            ema_aligned=ema_aligned,
            macd_aligned=macd_aligned,
            valid=valid
        )

        return setup

    def deduplicate_setups(self, setups: List[ICISetup]) -> List[ICISetup]:
        """
        Remove duplicate setups on same day, keeping best one

        Args:
            setups: List of ICISetup objects

        Returns:
            Deduplicated list
        """
        if not setups:
            return []

        # Group by date
        by_date = {}
        for setup in setups:
            date_key = setup.date.date() if hasattr(setup.date, 'date') else setup.date
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(setup)

        # Keep best setup per day (highest R:R that's valid)
        deduplicated = []
        for date_key, date_setups in by_date.items():
            # Prioritize valid setups
            valid_setups = [s for s in date_setups if s.valid]
            if valid_setups:
                best = max(valid_setups, key=lambda s: s.risk_reward)
            else:
                best = max(date_setups, key=lambda s: s.risk_reward)
            deduplicated.append(best)

        return deduplicated
