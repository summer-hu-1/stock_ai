from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_factor import BaseFactor


class MomentumFactor(BaseFactor):
    def __init__(self):
        super().__init__("MomentumFactor")

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_result()

        close = df["close"].astype(float)

        returns = self.calculate_returns(close, [5, 10, 20, 60])

        momentum_rank = self._calc_momentum_rank(close)

        relative_strength = self._calc_relative_strength(close)

        momentum_score = self._calc_momentum_score(returns)

        acceleration = self._calc_acceleration(close)

        return {
            "return_5d": returns.get("return_5d", 0),
            "return_10d": returns.get("return_10d", 0),
            "return_20d": returns.get("return_20d", 0),
            "return_60d": returns.get("return_60d", 0),
            "momentum_rank": momentum_rank,
            "relative_strength": relative_strength,
            "momentum_score": momentum_score,
            "acceleration": acceleration,
        }

    def _calc_momentum_rank(self, close: pd.Series) -> int:
        if len(close) < 60:
            return 50

        returns_60d = []
        for i in range(60, len(close)):
            ret = (close.iloc[i] / close.iloc[i - 60] - 1) * 100
            returns_60d.append(ret)

        if not returns_60d:
            return 50

        current_return = (close.iloc[-1] / close.iloc[-60] - 1) * 100

        rank = sum(1 for r in returns_60d if r < current_return) / len(returns_60d) * 100

        return max(0, min(100, int(rank)))

    def _calc_relative_strength(self, close: pd.Series) -> int:
        if len(close) < 20:
            return 50

        stock_return = (close.iloc[-1] / close.iloc[-20] - 1) * 100

        if stock_return > 20:
            return 90
        elif stock_return > 15:
            return 80
        elif stock_return > 10:
            return 70
        elif stock_return > 5:
            return 60
        elif stock_return > 0:
            return 55
        elif stock_return > -5:
            return 45
        elif stock_return > -10:
            return 35
        elif stock_return > -15:
            return 25
        else:
            return 15

    def _calc_momentum_score(self, returns: Dict[str, float]) -> int:
        r5 = returns.get("return_5d", 0)
        r20 = returns.get("return_20d", 0)
        r60 = returns.get("return_60d", 0)

        score = 50

        if r5 > 5:
            score += 15
        elif r5 > 2:
            score += 10
        elif r5 > 0:
            score += 5
        elif r5 < -5:
            score -= 15
        elif r5 < -2:
            score -= 10
        else:
            score -= 5

        if r20 > 20:
            score += 20
        elif r20 > 10:
            score += 15
        elif r20 > 5:
            score += 10
        elif r20 < -10:
            score -= 20
        elif r20 < -5:
            score -= 10

        score += min(max(int(r60 / 2), -15), 15)

        return max(0, min(100, int(score)))

    def _calc_acceleration(self, close: pd.Series) -> str:
        if len(close) < 20:
            return "unknown"

        recent_5 = (close.iloc[-1] / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0
        prev_5 = (close.iloc[-5] / close.iloc[-10] - 1) * 100 if len(close) >= 10 else 0

        diff = recent_5 - prev_5

        if diff > 3:
            return "accelerating"
        elif diff < -3:
            return "decelerating"
        else:
            return "stable"

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "return_5d": 0,
            "return_10d": 0,
            "return_20d": 0,
            "return_60d": 0,
            "momentum_rank": 50,
            "relative_strength": 50,
            "momentum_score": 50,
            "acceleration": "unknown",
        }
