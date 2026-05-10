from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_factor import BaseFactor


class TrendFactor(BaseFactor):
    def __init__(self):
        super().__init__("TrendFactor")

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_result()

        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)

        ma5 = self._calc_ma(close, 5)
        ma10 = self._calc_ma(close, 10)
        ma20 = self._calc_ma(close, 20)
        ma60 = self._calc_ma(close, 60)

        current_close = float(close.iloc[-1])

        ma_alignment = self._check_alignment(ma5, ma10, ma20, ma60)
        close_above_ma20 = current_close > ma20 if ma20 else False
        close_above_ma60 = current_close > ma60 if ma60 else False

        high_20d = float(high.iloc[-20:].max()) if len(high) >= 20 else float(high.max())
        high_60d = float(high.iloc[-60:].max()) if len(high) >= 60 else float(high.max())
        low_20d = float(low.iloc[-20:].min()) if len(low) >= 20 else float(low.min())

        new_high_20d = current_close >= high_20d
        new_high_60d = current_close >= high_60d

        trend_strength = self._calc_trend_strength(ma5, ma10, ma20, ma60, close)

        ma_crossover = self._detect_ma_crossover(df)

        return {
            "ma5": ma5,
            "ma10": ma10,
            "ma20": ma20,
            "ma60": ma60,
            "close_above_ma20": close_above_ma20,
            "close_above_ma60": close_above_ma60,
            "ma_alignment": ma_alignment,
            "ma_bullish": ma_alignment in ["strong_bull", "moderate_bull"],
            "new_high_20d": new_high_20d,
            "new_high_60d": new_high_60d,
            "high_20d": high_20d,
            "high_60d": high_60d,
            "low_20d": low_20d,
            "trend_strength": trend_strength,
            "ma_crossover": ma_crossover,
            "distance_to_ma20_pct": self._calc_distance_pct(current_close, ma20),
            "distance_to_ma60_pct": self._calc_distance_pct(current_close, ma60),
        }

    def _calc_ma(self, close: pd.Series, period: int) -> float:
        if len(close) < period:
            return None
        ma = close.iloc[-period:].mean()
        return float(ma) if not np.isnan(ma) else None

    def _check_alignment(self, ma5: float, ma10: float, ma20: float, ma60: float) -> str:
        if None in [ma5, ma10, ma20, ma60]:
            return "unknown"

        if ma5 > ma10 > ma20 > ma60:
            return "strong_bull"
        elif ma5 > ma10 > ma20:
            return "moderate_bull"
        elif ma5 < ma10 < ma20 < ma60:
            return "strong_bear"
        elif ma5 < ma10 < ma20:
            return "moderate_bear"
        elif ma5 > ma20 and ma10 > ma20:
            return "mixed_bull"
        elif ma5 < ma20 and ma10 < ma20:
            return "mixed_bear"
        else:
            return "neutral"

    def _calc_trend_strength(self, ma5: float, ma10: float, ma20: float, ma60: float, close: pd.Series) -> int:
        if None in [ma5, ma10, ma20, ma60]:
            return 50

        current_close = float(close.iloc[-1])

        close_vs_ma = (current_close / ma20 - 1) * 100 if ma20 else 0

        ma_slope_20 = ((ma5 - ma20) / ma20) * 100 if ma20 else 0

        score = 50
        score += 10 if ma5 > ma10 else -10
        score += 10 if ma10 > ma20 else -10
        score += 10 if ma20 > ma60 else -10
        score += min(max(close_vs_ma * 2, -20), 20)
        score += min(max(ma_slope_20, -15), 15)

        return max(0, min(100, int(score)))

    def _detect_ma_crossover(self, df: pd.DataFrame) -> Dict[str, bool]:
        if len(df) < 5:
            return {"golden_cross": False, "death_cross": False}

        close = df["close"].astype(float)
        ma5_series = close.rolling(5).mean()
        ma10_series = close.rolling(10).mean()

        ma5_current = float(ma5_series.iloc[-1])
        ma10_current = float(ma10_series.iloc[-1])
        ma5_prev = float(ma5_series.iloc[-2])
        ma10_prev = float(ma10_series.iloc[-2])

        golden_cross = ma5_prev <= ma10_prev and ma5_current > ma10_current
        death_cross = ma5_prev >= ma10_prev and ma5_current < ma10_current

        return {
            "golden_cross": golden_cross,
            "death_cross": death_cross
        }

    def _calc_distance_pct(self, current: float, ma: float) -> float:
        if ma is None or ma == 0:
            return 0.0
        return float(((current - ma) / ma) * 100)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "ma5": None,
            "ma10": None,
            "ma20": None,
            "ma60": None,
            "close_above_ma20": False,
            "close_above_ma60": False,
            "ma_alignment": "unknown",
            "ma_bullish": False,
            "new_high_20d": False,
            "new_high_60d": False,
            "high_20d": None,
            "high_60d": None,
            "low_20d": None,
            "trend_strength": 50,
            "ma_crossover": {"golden_cross": False, "death_cross": False},
            "distance_to_ma20_pct": 0.0,
            "distance_to_ma60_pct": 0.0,
        }
