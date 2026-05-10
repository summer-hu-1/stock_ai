from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_factor import BaseFactor


class VolumeFactor(BaseFactor):
    def __init__(self):
        super().__init__("VolumeFactor")

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_result()

        volume = df["volume"].astype(float)
        close = df["close"].astype(float)

        volume_ma5 = self._calc_ma(volume, 5)
        volume_ma10 = self._calc_ma(volume, 10)
        volume_ma20 = self._calc_ma(volume, 20)

        current_volume = float(volume.iloc[-1])

        volume_ratio = self._calc_volume_ratio(current_volume, volume_ma5)

        volume_breakout = current_volume > volume_ma5 * 2 if volume_ma5 else False
        shrink_volume = current_volume < volume_ma5 * 0.5 if volume_ma5 else False

        volume_pulse = self._calc_volume_pulse(volume, close)

        volume_continuity = self._calc_volume_continuity(volume)

        volume_score = self._calc_volume_score(volume_ratio, volume_breakout, shrink_volume, volume_continuity)

        return {
            "volume_ma5": volume_ma5,
            "volume_ma10": volume_ma10,
            "volume_ma20": volume_ma20,
            "volume_ratio": volume_ratio,
            "volume_breakout": volume_breakout,
            "shrink_volume": shrink_volume,
            "volume_pulse": volume_pulse,
            "volume_continuity": volume_continuity,
            "volume_score": volume_score,
            "current_volume": current_volume,
        }

    def _calc_ma(self, series: pd.Series, period: int) -> float:
        if len(series) < period:
            return None
        ma = series.iloc[-period:].mean()
        return float(ma) if not np.isnan(ma) else None

    def _calc_volume_ratio(self, current: float, ma5: float) -> float:
        if ma5 is None or ma5 == 0:
            return 1.0
        return float(current / ma5)

    def _calc_volume_pulse(self, volume: pd.Series, close: pd.Series) -> float:
        if len(volume) < 5:
            return 0.0

        recent_vol = volume.iloc[-5:].mean()
        older_vol = volume.iloc[-20:-5].mean() if len(volume) >= 20 else recent_vol

        if older_vol == 0:
            return 0.0

        pulse = (recent_vol - older_vol) / older_vol * 100
        return float(pulse)

    def _calc_volume_continuity(self, volume: pd.Series) -> str:
        if len(volume) < 5:
            return "unknown"

        recent = volume.iloc[-5:]
        avg_recent = recent.mean()
        counts_above = (recent > avg_recent).sum()

        if counts_above >= 4:
            return "increasing"
        elif counts_above <= 1:
            return "decreasing"
        else:
            return "stable"

    def _calc_volume_score(self, ratio: float, breakout: bool, shrink: bool, continuity: str) -> int:
        score = 50

        if ratio > 3:
            score += 25
        elif ratio > 2:
            score += 15
        elif ratio > 1.5:
            score += 10
        elif ratio < 0.5:
            score -= 15
        elif ratio < 0.8:
            score -= 5

        if breakout:
            score += 15

        if shrink:
            score -= 10

        if continuity == "increasing":
            score += 10
        elif continuity == "decreasing":
            score -= 10

        return max(0, min(100, int(score)))

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "volume_ma5": None,
            "volume_ma10": None,
            "volume_ma20": None,
            "volume_ratio": 1.0,
            "volume_breakout": False,
            "shrink_volume": False,
            "volume_pulse": 0.0,
            "volume_continuity": "unknown",
            "volume_score": 50,
            "current_volume": 0,
        }
