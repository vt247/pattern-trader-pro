"""
Entry validation module - EMA, MACD, Risk/Reward
"""
import pandas as pd
import numpy as np


class EntryValidator:
    """Validate trading setups using technical indicators"""

    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def validate_ema(close_prices: pd.Series, period1: int = 10,
                    period2: int = 20, direction: str = 'long') -> bool:
        """
        Validate EMA alignment

        Args:
            close_prices: Series of closing prices
            period1: Fast EMA period (default 10)
            period2: Slow EMA period (default 20)
            direction: 'long' or 'short'

        Returns:
            True if EMAs are aligned correctly for the direction
        """
        if len(close_prices) < period2:
            return False

        ema_fast = EntryValidator.calculate_ema(close_prices, period1)
        ema_slow = EntryValidator.calculate_ema(close_prices, period2)

        # Get latest values
        fast_value = ema_fast.iloc[-1]
        slow_value = ema_slow.iloc[-1]

        if direction == 'long':
            return fast_value > slow_value
        else:  # short
            return fast_value < slow_value

    @staticmethod
    def calculate_macd(close_prices: pd.Series, fast: int = 12,
                      slow: int = 26, signal: int = 9) -> tuple:
        """
        Calculate MACD indicator

        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
        ema_slow = close_prices.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def validate_macd(close_prices: pd.Series, direction: str = 'long') -> bool:
        """
        Validate MACD alignment

        Args:
            close_prices: Series of closing prices
            direction: 'long' or 'short'

        Returns:
            True if MACD confirms the direction
        """
        if len(close_prices) < 26:
            return False

        macd_line, signal_line, histogram = EntryValidator.calculate_macd(close_prices)

        # Get latest values
        macd_value = macd_line.iloc[-1]
        histogram_value = histogram.iloc[-1]

        if direction == 'long':
            # MACD > 0 and histogram > 0 (bullish)
            return macd_value > 0 and histogram_value > 0
        else:  # short
            # MACD < 0 and histogram < 0 (bearish)
            return macd_value < 0 and histogram_value < 0

    @staticmethod
    def validate_break_of_structure(df: pd.DataFrame, entry_idx: int,
                                    direction: str = 'long',
                                    lookback: int = 20) -> bool:
        """
        Validate break of structure (BOS)

        Args:
            df: DataFrame with OHLC data
            entry_idx: Index of potential entry bar
            direction: 'long' or 'short'
            lookback: Number of bars to look back for structure

        Returns:
            True if structure is broken
        """
        if entry_idx < lookback:
            return False

        lookback_data = df.iloc[max(0, entry_idx - lookback):entry_idx]

        if direction == 'long':
            # For long: price should break above recent highs
            recent_high = lookback_data['High'].max()
            entry_high = df.iloc[entry_idx]['High']
            return entry_high > recent_high
        else:  # short
            # For short: price should break below recent lows
            recent_low = lookback_data['Low'].min()
            entry_low = df.iloc[entry_idx]['Low']
            return entry_low < recent_low

    @staticmethod
    def validate_risk_reward(entry: float, stop: float, target: float,
                           min_ratio: float = 1.3) -> bool:
        """
        Validate risk/reward ratio

        Args:
            entry: Entry price
            stop: Stop loss price
            target: Target price
            min_ratio: Minimum acceptable R:R ratio (default 1.3)

        Returns:
            True if R:R ratio meets minimum requirement
        """
        risk = abs(entry - stop)
        if risk == 0:
            return False

        reward = abs(target - entry)
        ratio = reward / risk

        return ratio >= min_ratio

    @staticmethod
    def is_same_color_candle(row: pd.Series, bullish: bool) -> bool:
        """
        Check if candle is same color (bullish or bearish)

        Args:
            row: DataFrame row with Open and Close
            bullish: True for bullish, False for bearish

        Returns:
            True if candle matches expected direction
        """
        if bullish:
            return row['Close'] > row['Open']
        else:
            return row['Close'] < row['Open']

    @staticmethod
    def count_consecutive_candles(df: pd.DataFrame, start_idx: int,
                                 bullish: bool, max_count: int = 10) -> int:
        """
        Count consecutive same-color candles

        Args:
            df: DataFrame with OHLC data
            start_idx: Starting index
            bullish: True for bullish candles
            max_count: Maximum candles to count

        Returns:
            Number of consecutive same-color candles
        """
        count = 0
        for i in range(start_idx, min(start_idx + max_count, len(df))):
            if EntryValidator.is_same_color_candle(df.iloc[i], bullish):
                count += 1
            else:
                break
        return count
