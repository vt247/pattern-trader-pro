"""
Data loading module - supports yfinance and CSV
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class DataLoader:
    """Load market data from various sources"""

    @staticmethod
    def load_from_yfinance(symbol: str = 'SPY', period: str = '2y',
                          interval: str = '1d') -> pd.DataFrame:
        """
        Load data from Yahoo Finance

        Args:
            symbol: Stock symbol (default: SPY for S&P 500)
            period: Time period (e.g., '2y', '5y', 'max')
            interval: Data interval ('1d', '1h', '15m', '1wk', '1mo')

        Returns:
            DataFrame with OHLCV data
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError(
                "yfinance not installed. Install with: pip install yfinance"
            )

        print(f"Downloading {symbol} data ({period}, {interval})...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            raise ValueError(f"No data retrieved for {symbol}")

        # Reset index to make Date a column
        df.reset_index(inplace=True)

        # Standardize column names
        df.columns = [col.replace(' ', '_') for col in df.columns]

        # Ensure required columns exist
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        print(f"Loaded {len(df)} rows from {df['Date'].min()} to {df['Date'].max()}")

        return df

    @staticmethod
    def load_from_csv(filepath: str, date_column: str = 'Date',
                     parse_dates: bool = True) -> pd.DataFrame:
        """
        Load data from CSV file

        Args:
            filepath: Path to CSV file
            date_column: Name of date column
            parse_dates: Whether to parse dates

        Returns:
            DataFrame with OHLCV data
        """
        print(f"Loading data from {filepath}...")

        if parse_dates:
            df = pd.read_csv(filepath, parse_dates=[date_column])
        else:
            df = pd.read_csv(filepath)

        # Standardize column names
        df.columns = [col.strip() for col in df.columns]

        # Check for required columns
        required_cols = ['Open', 'High', 'Low', 'Close']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"CSV missing required columns: {missing_cols}")

        print(f"Loaded {len(df)} rows")

        return df

    @staticmethod
    def resample_to_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample data to different timeframe

        Args:
            df: DataFrame with OHLCV data and Date index
            timeframe: Target timeframe ('1h', '4h', '1d', '1W', '1M')

        Returns:
            Resampled DataFrame
        """
        # Make sure Date is the index
        if 'Date' in df.columns:
            df_copy = df.set_index('Date')
        else:
            df_copy = df.copy()

        # Resample OHLCV data
        resampled = pd.DataFrame()
        resampled['Open'] = df_copy['Open'].resample(timeframe).first()
        resampled['High'] = df_copy['High'].resample(timeframe).max()
        resampled['Low'] = df_copy['Low'].resample(timeframe).min()
        resampled['Close'] = df_copy['Close'].resample(timeframe).last()

        if 'Volume' in df_copy.columns:
            resampled['Volume'] = df_copy['Volume'].resample(timeframe).sum()

        # Drop NaN rows
        resampled.dropna(inplace=True)

        # Reset index to make Date a column again
        resampled.reset_index(inplace=True)

        print(f"Resampled to {timeframe}: {len(resampled)} rows")

        return resampled

    @staticmethod
    def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and clean data for scanning

        Args:
            df: Raw DataFrame

        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()

        # Remove rows with NaN in OHLC
        df_clean.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

        # Sort by date
        if 'Date' in df_clean.columns:
            df_clean.sort_values('Date', inplace=True)
            df_clean.reset_index(drop=True, inplace=True)

        # Validate data integrity
        # High should be >= Low
        invalid_rows = df_clean[df_clean['High'] < df_clean['Low']]
        if len(invalid_rows) > 0:
            print(f"Warning: Found {len(invalid_rows)} rows where High < Low")
            df_clean = df_clean[df_clean['High'] >= df_clean['Low']]

        return df_clean


def load_spy_data(source: str = 'yfinance', filepath: Optional[str] = None,
                 period: str = '2y', interval: str = '1d') -> pd.DataFrame:
    """
    Convenience function to load SPY data

    Args:
        source: 'yfinance' or 'csv'
        filepath: Path to CSV (if source='csv')
        period: Time period for yfinance
        interval: Data interval

    Returns:
        Prepared DataFrame
    """
    loader = DataLoader()

    if source == 'yfinance':
        df = loader.load_from_yfinance('SPY', period, interval)
    elif source == 'csv':
        if not filepath:
            raise ValueError("filepath required when source='csv'")
        df = loader.load_from_csv(filepath)
    else:
        raise ValueError(f"Unknown source: {source}")

    return loader.prepare_data(df)
