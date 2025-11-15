"""
Fibonacci calculation module for pattern scanning
"""

class FibonacciCalculator:
    """Calculate Fibonacci retracements and extensions"""

    # Standard Fibonacci levels
    RETRACEMENT_LEVELS = {
        '382': 0.382,
        '500': 0.500,
        '618': 0.618,
        '786': 0.786
    }

    EXTENSION_LEVELS = {
        '-272': -0.272,
        '000': 0.000,
        '618': 0.618,
        '1000': 1.000
    }

    @staticmethod
    def calculate_retracement(high: float, low: float, level: float) -> float:
        """
        Calculate Fibonacci retracement level

        Args:
            high: Impulse high point
            low: Impulse low point
            level: Fibonacci level (e.g., 0.618)

        Returns:
            Price at retracement level
        """
        impulse_range = high - low
        return high - (impulse_range * level)

    @staticmethod
    def calculate_extension(high: float, low: float, level: float) -> float:
        """
        Calculate Fibonacci extension level

        Args:
            high: Impulse high point
            low: Impulse low point
            level: Fibonacci extension level (e.g., -0.272)

        Returns:
            Price at extension level
        """
        impulse_range = high - low
        return high + (impulse_range * abs(level))

    @staticmethod
    def get_retracement_pct(impulse_high: float, impulse_low: float,
                           correction_level: float) -> float:
        """
        Calculate what percentage of impulse was retraced

        Args:
            impulse_high: High of impulse move
            impulse_low: Low of impulse move
            correction_level: Current correction price level

        Returns:
            Percentage retraced (0.0 to 1.0+)
        """
        impulse_range = impulse_high - impulse_low
        if impulse_range == 0:
            return 0.0

        retracement = impulse_high - correction_level
        return retracement / impulse_range

    @classmethod
    def is_valid_correction(cls, impulse_high: float, impulse_low: float,
                           correction_low: float, min_level: float = 0.382,
                           max_level: float = 0.786) -> bool:
        """
        Validate if correction is within acceptable Fibonacci range

        Args:
            impulse_high: High of bullish impulse
            impulse_low: Low of bullish impulse
            correction_low: Low of correction
            min_level: Minimum acceptable retracement (default 0.382)
            max_level: Maximum acceptable retracement (default 0.786)

        Returns:
            True if correction is valid
        """
        retracement_pct = cls.get_retracement_pct(impulse_high, impulse_low, correction_low)
        return min_level <= retracement_pct <= max_level

    @classmethod
    def calculate_target(cls, impulse_high: float, impulse_low: float,
                        extension_level: float = -0.272) -> float:
        """
        Calculate price target using extension level

        Args:
            impulse_high: High of impulse
            impulse_low: Low of impulse
            extension_level: Extension level (default -0.272)

        Returns:
            Target price
        """
        return cls.calculate_extension(impulse_high, impulse_low, extension_level)
