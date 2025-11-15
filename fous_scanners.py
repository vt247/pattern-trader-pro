"""
FOUS Pattern Scanners: Force, Survival, Revival, Gold
"""
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from typing import List, Optional
from fous_validators import FOUSValidator


@dataclass
class FOUSSetup:
    """Represents a FOUS pattern setup"""
    date: datetime
    pattern_type: str  # 'Force', 'Survival', 'Revival', 'Gold'
    timeframe: str
    entry: float
    stop: float
    target: float
    risk_reward: float
    volume_spike: bool
    rsi: float
    ema_aligned: bool
    vwap_bullish: bool
    valid: bool
    notes: str = ""

    def to_dict(self):
        """Convert to dictionary for CSV export"""
        return {
            'Date': self.date,
            'Pattern': self.pattern_type,
            'Timeframe': self.timeframe,
            'Entry': round(self.entry, 2),
            'Stop': round(self.stop, 2),
            'Target': round(self.target, 2),
            'Risk_Reward': round(self.risk_reward, 2),
            'Volume_Spike': self.volume_spike,
            'RSI': round(self.rsi, 1) if self.rsi else None,
            'EMA_Aligned': self.ema_aligned,
            'VWAP_Bullish': self.vwap_bullish,
            'Valid': self.valid,
            'Notes': self.notes
        }


class ForceScanner:
    """
    FORCE Pattern Scanner

    Criteria:
    - 3+ consecutive green candles
    - Volume increasing each candle
    - EMA(9) < EMA(21) < Close (strong bullish)
    - Pivot point: recent 5-candle lows not broken
    """

    def __init__(self, min_candles: int = 3, min_risk_reward: float = 1.5):
        self.min_candles = min_candles
        self.min_risk_reward = min_risk_reward
        self.validator = FOUSValidator()

    def scan(self, df: pd.DataFrame, timeframe: str = '1h') -> List[FOUSSetup]:
        """Scan for Force patterns"""
        setups = []

        if len(df) < 50:
            return setups

        for i in range(50, len(df)):
            setup = self._find_force_at_index(df, i, timeframe)
            if setup:
                setups.append(setup)

        return setups

    def _find_force_at_index(self, df: pd.DataFrame, idx: int,
                            timeframe: str) -> Optional[FOUSSetup]:
        """Find Force pattern at index"""

        # 1. Count consecutive green candles
        green_count = self.validator.count_consecutive_green(df, idx - 10, 10)
        if green_count < self.min_candles:
            return None

        # 2. Check volume increasing
        start_idx = idx - green_count + 1
        if not self.validator.is_volume_increasing(df, start_idx, green_count):
            return None

        # 3. Check EMA alignment: EMA(9) < EMA(21) < Close
        is_aligned, ema9, ema21 = self.validator.check_ema_alignment(df, idx, 9, 21)
        if not is_aligned:
            return None

        # 4. Check pivot point (recent lows not broken)
        pivot_holds = self.validator.check_pivot_point(df, idx, 5)
        if not pivot_holds:
            return None

        # Calculate entry, stop, target
        entry = df.iloc[idx]['Close']

        # Stop: below recent pivot low
        recent_low = df.iloc[max(0, idx - 5):idx]['Low'].min()
        stop = recent_low * 0.99  # 1% buffer

        # Target: 2x risk based on momentum
        risk = abs(entry - stop)
        target = entry + (risk * 2.0)

        risk_reward = (target - entry) / risk if risk > 0 else 0

        if risk_reward < self.min_risk_reward:
            return None

        # Calculate RSI
        rsi_series = self.validator.calculate_rsi(df['Close'])
        rsi = rsi_series.iloc[idx] if idx < len(rsi_series) else None

        # Check VWAP
        vwap = self.validator.calculate_vwap(df)
        vwap_bullish = entry > vwap.iloc[idx] if idx < len(vwap) else False

        # Volume spike check
        volume_spike = self.validator.is_volume_spike(df, idx, 1.5, 20)

        # Validity
        valid = is_aligned and pivot_holds and risk_reward >= self.min_risk_reward

        return FOUSSetup(
            date=df.iloc[idx]['Date'] if 'Date' in df.columns else df.index[idx],
            pattern_type='Force',
            timeframe=timeframe,
            entry=entry,
            stop=stop,
            target=target,
            risk_reward=risk_reward,
            volume_spike=volume_spike,
            rsi=rsi,
            ema_aligned=is_aligned,
            vwap_bullish=vwap_bullish,
            valid=valid,
            notes=f"{green_count} green candles, increasing volume"
        )


class SurvivalScanner:
    """
    SURVIVAL Pattern Scanner

    Criteria:
    - 5+ consecutive red candles (downtrend)
    - Volume spike at bottom
    - 3 candles: opens lower, closes higher (Wyckoff)
    - EMA(9) crosses above EMA(21)
    - RSI < 30, rises to 30-45
    """

    def __init__(self, min_red_candles: int = 5, min_risk_reward: float = 1.5):
        self.min_red_candles = min_red_candles
        self.min_risk_reward = min_risk_reward
        self.validator = FOUSValidator()

    def scan(self, df: pd.DataFrame, timeframe: str = '1h') -> List[FOUSSetup]:
        """Scan for Survival patterns"""
        setups = []

        if len(df) < 50:
            return setups

        for i in range(50, len(df)):
            setup = self._find_survival_at_index(df, i, timeframe)
            if setup:
                setups.append(setup)

        return setups

    def _find_survival_at_index(self, df: pd.DataFrame, idx: int,
                                timeframe: str) -> Optional[FOUSSetup]:
        """Find Survival pattern at index"""

        # Need at least 3 candles after downtrend for Wyckoff
        if idx < 50 or idx + 3 > len(df):
            return None

        # 1. Check for previous downtrend (5+ red candles)
        red_count = self.validator.count_consecutive_red(df, idx - 10, 10)
        if red_count < self.min_red_candles:
            return None

        # 2. Check Wyckoff logic (3 candles: opens lower, closes higher)
        wyckoff_idx = idx - red_count + 1
        if not self.validator.has_wickoff_logic(df, wyckoff_idx, 3):
            return None

        # 3. Check EMA crossover (9 crosses above 21)
        ema_cross = self.validator.check_ema_crossover(df, idx, 9, 21)
        if not ema_cross:
            return None

        # 4. Check RSI
        rsi_series = self.validator.calculate_rsi(df['Close'])
        if idx >= len(rsi_series):
            return None

        rsi = rsi_series.iloc[idx]

        # RSI should be recovering from oversold
        # Look for RSI that was < 30 recently and now 30-45
        rsi_was_oversold = False
        for j in range(max(0, idx - 5), idx):
            if rsi_series.iloc[j] < 30:
                rsi_was_oversold = True
                break

        if not (rsi_was_oversold and 30 <= rsi <= 45):
            return None

        # 5. Volume spike check (at bottom)
        volume_spike = self.validator.is_volume_spike(df, idx, 2.0, 20)

        # Calculate entry, stop, target
        entry = df.iloc[idx]['Close']

        # Stop: below Wyckoff bottom
        wyckoff_low = df.iloc[wyckoff_idx:wyckoff_idx + 3]['Low'].min()
        stop = wyckoff_low * 0.98

        # Target: 2x risk (recovery trade)
        risk = abs(entry - stop)
        target = entry + (risk * 2.5)

        risk_reward = (target - entry) / risk if risk > 0 else 0

        if risk_reward < self.min_risk_reward:
            return None

        # VWAP check
        vwap = self.validator.calculate_vwap(df)
        vwap_bullish = entry > vwap.iloc[idx] if idx < len(vwap) else False

        # EMA alignment check
        is_aligned, _, _ = self.validator.check_ema_alignment(df, idx, 9, 21)

        # Validity
        valid = ema_cross and volume_spike and risk_reward >= self.min_risk_reward

        return FOUSSetup(
            date=df.iloc[idx]['Date'] if 'Date' in df.columns else df.index[idx],
            pattern_type='Survival',
            timeframe=timeframe,
            entry=entry,
            stop=stop,
            target=target,
            risk_reward=risk_reward,
            volume_spike=volume_spike,
            rsi=rsi,
            ema_aligned=is_aligned,
            vwap_bullish=vwap_bullish,
            valid=valid,
            notes=f"Recovery from {red_count} red candles, RSI {rsi:.1f}"
        )


class RevivalScanner:
    """
    REVIVAL Pattern Scanner

    Criteria:
    - 2-3 candle bottom pattern
    - Each candle closes above previous
    - Volume spike + next candles 40% higher volume
    - VWAP turns bullish
    - Price breaks above 20-EMA
    """

    def __init__(self, min_risk_reward: float = 1.5):
        self.min_risk_reward = min_risk_reward
        self.validator = FOUSValidator()

    def scan(self, df: pd.DataFrame, timeframe: str = '1h') -> List[FOUSSetup]:
        """Scan for Revival patterns"""
        setups = []

        if len(df) < 50:
            return setups

        for i in range(50, len(df) - 2):  # Need 2 candles ahead
            setup = self._find_revival_at_index(df, i, timeframe)
            if setup:
                setups.append(setup)

        return setups

    def _find_revival_at_index(self, df: pd.DataFrame, idx: int,
                               timeframe: str) -> Optional[FOUSSetup]:
        """Find Revival pattern at index"""

        # 1. Check 2-3 candle bottom (each closes higher)
        pattern_length = 3
        if idx < pattern_length:
            return None

        closes_higher = True
        for i in range(idx - pattern_length + 1, idx):
            if df.iloc[i + 1]['Close'] <= df.iloc[i]['Close']:
                closes_higher = False
                break

        if not closes_higher:
            return None

        # 2. Volume spike
        volume_spike = self.validator.is_volume_spike(df, idx, 1.5, 20)
        if not volume_spike:
            return None

        # 3. Next candles have 40% higher volume
        if idx + 2 >= len(df):
            return None

        avg_recent_vol = df.iloc[idx - 10:idx]['Volume'].mean()
        next_candles_vol = df.iloc[idx + 1:idx + 3]['Volume'].mean()

        high_volume_continues = next_candles_vol >= (avg_recent_vol * 1.4)

        # 4. VWAP turns bullish
        vwap = self.validator.calculate_vwap(df)
        if idx >= len(vwap):
            return None

        # Check if price crossed above VWAP recently
        vwap_bullish = df.iloc[idx]['Close'] > vwap.iloc[idx]

        # 5. Price breaks above 20-EMA
        ema20 = df['Close'].ewm(span=20, adjust=False).mean()
        if idx >= len(ema20):
            return None

        breaks_ema = df.iloc[idx]['Close'] > ema20.iloc[idx]

        # Calculate entry, stop, target
        entry = df.iloc[idx]['Close']

        # Stop: below pattern low
        pattern_low = df.iloc[idx - pattern_length:idx + 1]['Low'].min()
        stop = pattern_low * 0.99

        # Target: 2.5x risk (breakout trade)
        risk = abs(entry - stop)
        target = entry + (risk * 2.5)

        risk_reward = (target - entry) / risk if risk > 0 else 0

        if risk_reward < self.min_risk_reward:
            return None

        # RSI
        rsi_series = self.validator.calculate_rsi(df['Close'])
        rsi = rsi_series.iloc[idx] if idx < len(rsi_series) else None

        # EMA alignment
        is_aligned, _, _ = self.validator.check_ema_alignment(df, idx, 9, 21)

        # Validity
        valid = (volume_spike and vwap_bullish and breaks_ema and
                high_volume_continues and risk_reward >= self.min_risk_reward)

        return FOUSSetup(
            date=df.iloc[idx]['Date'] if 'Date' in df.columns else df.index[idx],
            pattern_type='Revival',
            timeframe=timeframe,
            entry=entry,
            stop=stop,
            target=target,
            risk_reward=risk_reward,
            volume_spike=volume_spike,
            rsi=rsi,
            ema_aligned=is_aligned,
            vwap_bullish=vwap_bullish,
            valid=valid,
            notes=f"{pattern_length}-candle bottom, volume spike, VWAP bullish"
        )


class GoldScanner:
    """
    GOLD Pattern Scanner (Composite)

    Criteria:
    - Force + Revival together, OR
    - Survival + Revival when RSI > 40
    - Volume: 3x average
    - Volatility near historical low
    - Confirmed on 3-5min AND 15min timeframe
    """

    def __init__(self, min_risk_reward: float = 2.0):
        self.min_risk_reward = min_risk_reward
        self.validator = FOUSValidator()
        self.force_scanner = ForceScanner()
        self.survival_scanner = SurvivalScanner()
        self.revival_scanner = RevivalScanner()

    def scan(self, df: pd.DataFrame, timeframe: str = '5m',
            df_15m: pd.DataFrame = None) -> List[FOUSSetup]:
        """Scan for Gold patterns"""
        setups = []

        if len(df) < 100:
            return setups

        # Scan component patterns
        force_setups = self.force_scanner.scan(df, timeframe)
        survival_setups = self.survival_scanner.scan(df, timeframe)
        revival_setups = self.revival_scanner.scan(df, timeframe)

        # Create date lookup for quick matching
        revival_dates = {s.date: s for s in revival_setups}

        # Look for Force + Revival
        for force in force_setups:
            if force.date in revival_dates:
                gold = self._create_gold_setup(force, revival_dates[force.date],
                                              'Force+Revival', df, timeframe)
                if gold:
                    setups.append(gold)

        # Look for Survival + Revival (RSI > 40)
        for survival in survival_setups:
            if survival.date in revival_dates and survival.rsi and survival.rsi > 40:
                gold = self._create_gold_setup(survival, revival_dates[survival.date],
                                              'Survival+Revival', df, timeframe)
                if gold:
                    setups.append(gold)

        return setups

    def _create_gold_setup(self, pattern1: FOUSSetup, pattern2: FOUSSetup,
                          combination: str, df: pd.DataFrame,
                          timeframe: str) -> Optional[FOUSSetup]:
        """Create Gold setup from component patterns"""

        # Find index for this date
        idx = None
        for i, row in df.iterrows():
            date_val = row['Date'] if 'Date' in df.columns else df.index[i]
            if date_val == pattern1.date:
                idx = i
                break

        if idx is None:
            return None

        # Check volume 3x average
        volume_spike = self.validator.is_volume_spike(df, idx, 3.0, 20)
        if not volume_spike:
            return None

        # Check low volatility
        low_vol = self.validator.is_low_volatility(df, idx, 100, 0.2)

        # Use better R:R of the two patterns
        risk_reward = max(pattern1.risk_reward, pattern2.risk_reward)

        if risk_reward < self.min_risk_reward:
            return None

        # Take entry/stop/target from Revival (it's the breakout)
        entry = pattern2.entry
        stop = pattern2.stop
        target = pattern2.target

        # Enhanced target for Gold pattern
        risk = abs(entry - stop)
        target = entry + (risk * 3.0)  # 3x risk for Gold

        risk_reward = (target - entry) / risk if risk > 0 else 0

        # Validity
        valid = (volume_spike and low_vol and pattern1.valid and pattern2.valid and
                risk_reward >= self.min_risk_reward)

        return FOUSSetup(
            date=pattern1.date,
            pattern_type='Gold',
            timeframe=timeframe,
            entry=entry,
            stop=stop,
            target=target,
            risk_reward=risk_reward,
            volume_spike=volume_spike,
            rsi=pattern2.rsi,
            ema_aligned=pattern1.ema_aligned and pattern2.ema_aligned,
            vwap_bullish=pattern2.vwap_bullish,
            valid=valid,
            notes=f"{combination}, 3x volume, low volatility"
        )
