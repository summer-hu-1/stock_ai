from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_factor import BaseFactor


class StrengthFactor(BaseFactor):
    def __init__(self):
        super().__init__("StrengthFactor")

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_result()

        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)

        price_strength = self._calc_price_strength(close, high, low)

        volume_strength = self._calc_volume_strength(volume, close)

        combined_strength = self._calc_combined_strength(price_strength, volume_strength)

        strength_direction = self._calc_strength_direction(close)

        return {
            "price_strength": price_strength,
            "volume_strength": volume_strength,
            "combined_strength": combined_strength,
            "strength_direction": strength_direction,
        }

    def _calc_price_strength(self, close: pd.Series, high: pd.Series, low: pd.Series) -> int:
        if len(close) < 20:
            return 50

        current_close = float(close.iloc[-1])
        high_20d = float(high.iloc[-20:].max())
        low_20d = float(low.iloc[-20:].min())

        position = (current_close - low_20d) / (high_20d - low_20d) * 100 if high_20d != low_20d else 50

        return max(0, min(100, int(position)))

    def _calc_volume_strength(self, volume: pd.Series, close: pd.Series) -> int:
        if len(volume) < 20:
            return 50

        avg_vol = float(volume.iloc[-20:].mean())
        current_vol = float(volume.iloc[-1])

        if current_vol > avg_vol * 2:
            return 90
        elif current_vol > avg_vol * 1.5:
            return 75
        elif current_vol > avg_vol * 1.2:
            return 60
        elif current_vol > avg_vol * 0.8:
            return 50
        elif current_vol > avg_vol * 0.5:
            return 35
        else:
            return 20

    def _calc_combined_strength(self, price_strength: int, volume_strength: int) -> int:
        return int(price_strength * 0.6 + volume_strength * 0.4)

    def _calc_strength_direction(self, close: pd.Series) -> str:
        if len(close) < 5:
            return "neutral"

        recent_5 = close.iloc[-5:].values
        trend = np.polyfit(range(5), recent_5, 1)[0]

        if trend > 0:
            return "strengthening"
        elif trend < 0:
            return "weakening"
        else:
            return "neutral"

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "price_strength": 50,
            "volume_strength": 50,
            "combined_strength": 50,
            "strength_direction": "neutral",
        }
