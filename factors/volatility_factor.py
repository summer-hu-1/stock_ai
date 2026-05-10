from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_factor import BaseFactor


class VolatilityFactor(BaseFactor):
    def __init__(self):
        super().__init__("VolatilityFactor")

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_result()

        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        atr = self._calc_atr(df, period=14)
        daily_volatility = self._calc_daily_volatility(close)
        amplitude = self._calc_amplitude(high, low, close)
        atr_percent = self._calc_atr_percent(atr, close)

        volatility_rank = self._calc_volatility_rank(daily_volatility)

        volatility_score = self._calc_volatility_score(atr_percent, amplitude)

        return {
            "atr": atr,
            "atr_percent": atr_percent,
            "daily_volatility": daily_volatility,
            "amplitude": amplitude,
            "volatility_rank": volatility_rank,
            "volatility_score": volatility_score,
        }

    def _calc_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        if len(df) < period + 1:
            return None

        tr_list = []
        for i in range(1, len(df)):
            high_low = high.iloc[i] - low.iloc[i]
            high_close = abs(high.iloc[i] - close.iloc[i - 1])
            low_close = abs(low.iloc[i] - close.iloc[i - 1])
            tr = max(high_low, high_close, low_close)
            tr_list.append(tr)

        if len(tr_list) < period:
            return None

        atr = np.mean(tr_list[-period:])
        return float(atr) if not np.isnan(atr) else None

    def _calc_daily_volatility(self, close: pd.Series, period: int = 20) -> float:
        if len(close) < period:
            return 0.0

        returns = close.pct_change().dropna()
        if len(returns) < period:
            return 0.0

        volatility = returns.iloc[-period:].std() * np.sqrt(252) * 100
        return float(volatility) if not np.isnan(volatility) else 0.0

    def _calc_amplitude(self, high: pd.Series, low: pd.Series, close: pd.Series) -> float:
        if len(high) < 1:
            return 0.0

        today_high = float(high.iloc[-1])
        today_low = float(low.iloc[-1])
        today_close = float(close.iloc[-1])

        amplitude = ((today_high - today_low) / today_close) * 100 if today_close != 0 else 0.0
        return float(amplitude)

    def _calc_atr_percent(self, atr: float, close: pd.Series) -> float:
        if atr is None or len(close) < 1:
            return 0.0

        current_close = float(close.iloc[-1])
        if current_close == 0:
            return 0.0

        return float((atr / current_close) * 100)

    def _calc_volatility_rank(self, daily_volatility: float) -> int:
        if daily_volatility > 50:
            return 90
        elif daily_volatility > 35:
            return 80
        elif daily_volatility > 25:
            return 70
        elif daily_volatility > 20:
            return 60
        elif daily_volatility > 15:
            return 50
        elif daily_volatility > 10:
            return 40
        elif daily_volatility > 5:
            return 30
        else:
            return 20

    def _calc_volatility_score(self, atr_percent: float, amplitude: float) -> int:
        score = 50

        if atr_percent > 5:
            score += 20
        elif atr_percent > 3:
            score += 15
        elif atr_percent > 2:
            score += 10
        elif atr_percent < 1:
            score -= 15
        elif atr_percent < 1.5:
            score -= 10
        else:
            score -= 5

        if amplitude > 8:
            score += 15
        elif amplitude > 5:
            score += 10
        elif amplitude > 3:
            score += 5
        elif amplitude < 1.5:
            score -= 10
        elif amplitude < 2:
            score -= 5

        return max(0, min(100, int(score)))

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "atr": None,
            "atr_percent": 0.0,
            "daily_volatility": 0.0,
            "amplitude": 0.0,
            "volatility_rank": 50,
            "volatility_score": 50,
        }
