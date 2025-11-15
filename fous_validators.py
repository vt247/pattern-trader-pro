"""
FOUS Pattern Validators - Volume, RSI, VWAP, Volatility
"""
import pandas as pd
import numpy as np


class FOUSValidator:
    """Validators specific to FOUS patterns"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index)

        Args:
            prices: Close prices
            period: RSI period (default 14)

        Returns:
            RSI values (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Calculate VWAP (Volume Weighted Average Price)

        Args:
            df: DataFrame with High, Low, Close, Volume

        Returns:
            VWAP values
        """
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        return vwap

    @staticmethod
    def is_volume_increasing(df: pd.DataFrame, start_idx: int, count: int) -> bool:
        """
        Check if volume is increasing for consecutive candles

        Args:
            df: DataFrame with Volume
            start_idx: Starting index
            count: Number of candles to check

        Returns:
            True if volume increases each candle
        """
        if start_idx + count > len(df):
            return False

        for i in range(start_idx, start_idx + count - 1):
            if df.iloc[i + 1]['Volume'] <= df.iloc[i]['Volume']:
                return False
        return True

    @staticmethod
    def count_consecutive_green(df: pd.DataFrame, start_idx: int, max_count: int = 10) -> int:
        """
        Count consecutive green (bullish) candles

        Args:
            df: DataFrame with Open, Close
            start_idx: Starting index
            max_count: Maximum to count

        Returns:
            Number of consecutive green candles
        """
        count = 0
        for i in range(start_idx, min(start_idx + max_count, len(df))):
            if df.iloc[i]['Close'] > df.iloc[i]['Open']:
                count += 1
            else:
                break
        return count

    @staticmethod
    def count_consecutive_red(df: pd.DataFrame, start_idx: int, max_count: int = 10) -> int:
        """
        Count consecutive red (bearish) candles

        Args:
            df: DataFrame with Open, Close
            start_idx: Starting index
            max_count: Maximum to count

        Returns:
            Number of consecutive red candles
        """
        count = 0
        for i in range(start_idx, min(start_idx + max_count, len(df))):
            if df.iloc[i]['Close'] < df.iloc[i]['Open']:
                count += 1
            else:
                break
        return count

    @staticmethod
    def has_wickoff_logic(df: pd.DataFrame, idx: int, count: int = 3) -> bool:
        """
        Check Wyckoff logic: Opens lower, closes higher for N candles

        Args:
            df: DataFrame with Open, Close
            idx: Starting index
            count: Number of candles (default 3)

        Returns:
            True if pattern matches
        """
        if idx + count > len(df):
            return False

        for i in range(idx, idx + count - 1):
            current = df.iloc[i]
            next_candle = df.iloc[i + 1]

            # Opens lower than previous close
            if next_candle['Open'] >= current['Close']:
                return False

            # Closes higher than open (green candle)
            if next_candle['Close'] <= next_candle['Open']:
                return False

        return True

    @staticmethod
    def is_volume_spike(df: pd.DataFrame, idx: int, multiplier: float = 3.0,
                       lookback: int = 20) -> bool:
        """
        Check if current volume is a spike (N times average)

        Args:
            df: DataFrame with Volume
            idx: Current index
            multiplier: Volume multiplier (default 3x)
            lookback: Lookback period for average

        Returns:
            True if volume spike detected
        """
        if idx < lookback:
            return False

        avg_volume = df.iloc[idx - lookback:idx]['Volume'].mean()
        current_volume = df.iloc[idx]['Volume']

        return current_volume >= (avg_volume * multiplier)

    @staticmethod
    def calculate_volatility(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate historical volatility (standard deviation of returns)

        Args:
            prices: Close prices
            period: Lookback period

        Returns:
            Volatility values
        """
        returns = prices.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
        return volatility

    @staticmethod
    def is_low_volatility(df: pd.DataFrame, idx: int, period: int = 100,
                         percentile: float = 0.2) -> bool:
        """
        Check if current volatility is near historical low

        Args:
            df: DataFrame with Close
            idx: Current index
            period: Historical period to compare
            percentile: Percentile threshold (0.2 = bottom 20%)

        Returns:
            True if volatility is near historical low
        """
        if idx < period:
            return False

        volatility = FOUSValidator.calculate_volatility(df['Close'])

        if pd.isna(volatility.iloc[idx]):
            return False

        historical_vol = volatility.iloc[max(0, idx - period):idx]
        threshold = historical_vol.quantile(percentile)

        return volatility.iloc[idx] <= threshold

    @staticmethod
    def check_ema_alignment(df: pd.DataFrame, idx: int,
                           fast: int = 9, slow: int = 21) -> tuple:
        """
        Check EMA alignment: EMA(9) vs EMA(21) vs Close

        Args:
            df: DataFrame with Close
            idx: Current index
            fast: Fast EMA period
            slow: Slow EMA period

        Returns:
            (is_bullish, ema_fast, ema_slow) tuple
        """
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()

        if idx >= len(ema_fast) or idx >= len(ema_slow):
            return (False, None, None)

        close = df.iloc[idx]['Close']
        fast_val = ema_fast.iloc[idx]
        slow_val = ema_slow.iloc[idx]

        # Bullish: EMA(9) < EMA(21) < Close
        is_bullish = fast_val < slow_val < close

        return (is_bullish, fast_val, slow_val)

    @staticmethod
    def check_ema_crossover(df: pd.DataFrame, idx: int,
                           fast: int = 9, slow: int = 21) -> bool:
        """
        Check if EMA(9) just crossed above EMA(21)

        Args:
            df: DataFrame with Close
            idx: Current index
            fast: Fast EMA
            slow: Slow EMA

        Returns:
            True if bullish crossover detected
        """
        if idx < 1:
            return False

        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()

        # Previous: fast <= slow
        # Current: fast > slow
        prev_cross = ema_fast.iloc[idx - 1] <= ema_slow.iloc[idx - 1]
        curr_cross = ema_fast.iloc[idx] > ema_slow.iloc[idx]

        return prev_cross and curr_cross

    @staticmethod
    def check_pivot_point(df: pd.DataFrame, idx: int, lookback: int = 5) -> bool:
        """
        Check if recent lows have not been broken

        Args:
            df: DataFrame with Low
            idx: Current index
            lookback: Lookback period

        Returns:
            True if pivot holds (lows not broken)
        """
        if idx < lookback:
            return False

        recent_lows = df.iloc[idx - lookback:idx]['Low']
        min_low = recent_lows.min()
        current_low = df.iloc[idx]['Low']

        # Pivot holds if current low is above min of recent lows
        return current_low >= min_low
