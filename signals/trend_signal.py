from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_signal import BaseSignal


class TrendSignal(BaseSignal):
    def __init__(self):
        super().__init__("TrendSignal")

    def generate(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_signal()

        close = df["close"].astype(float)

        reasons = []
        signal_type = "none"
        direction = "neutral"
        strength = 50

        ma5 = float(close.iloc[-5:].mean()) if len(close) >= 5 else None
        ma10 = float(close.iloc[-10:].mean()) if len(close) >= 10 else None
        ma20 = float(close.iloc[-20:].mean()) if len(close) >= 20 else None
        ma60 = float(close.iloc[-60:].mean()) if len(close) >= 60 else None

        current_close = float(close.iloc[-1])

        if None not in [ma5, ma10, ma20, ma60]:
            if ma5 > ma10 > ma20 > ma60:
                signal_type = "strong_uptrend"
                direction = "bullish"
                distance = self.calc_distance_percent(current_close, ma60)
                strength = min(95, 70 + int(distance / 2))
                reasons.append("均线多头排列（Ma5>Ma10>Ma20>Ma60）")
                reasons.append(f"价格距MA60上涨 {distance:.1f}%")

            elif ma5 < ma10 < ma20 < ma60:
                signal_type = "strong_downtrend"
                direction = "bearish"
                distance = self.calc_distance_percent(current_close, ma60)
                strength = min(95, 70 + int(abs(distance) / 2))
                reasons.append("均线空头排列（Ma5<Ma10<Ma20<Ma60）")
                reasons.append(f"价格距MA60下跌 {abs(distance):.1f}%")

            elif ma5 > ma10 > ma20:
                signal_type = "moderate_uptrend"
                direction = "bullish"
                strength = 65
                reasons.append("短期均线上行")

            elif ma5 < ma10 < ma20:
                signal_type = "moderate_downtrend"
                direction = "bearish"
                strength = 65
                reasons.append("短期均线下行")

            elif current_close > ma20 and ma5 > ma20:
                signal_type = "ma20_recovery"
                direction = "bullish"
                strength = 55
                reasons.append("价格站上20日线，短期反弹")

            elif current_close < ma20 and ma5 < ma20:
                signal_type = "ma20_rejection"
                direction = "bearish"
                strength = 55
                reasons.append("价格跌破20日线，短期调整")

        if factors and "trend" in factors:
            trend = factors["trend"]
            ma_crossover = trend.get("ma_crossover", {})
            if ma_crossover.get("golden_cross"):
                signal_type = "golden_cross"
                direction = "bullish"
                strength = min(90, strength + 20)
                reasons.append("MA5上穿MA10，金叉形成")
            elif ma_crossover.get("death_cross"):
                signal_type = "death_cross"
                direction = "bearish"
                strength = min(90, strength + 20)
                reasons.append("MA5下穿MA10，死叉形成")

        if signal_type == "none":
            signal_type = "no_trend"
            direction = "neutral"
            strength = 50
            reasons.append("无明显趋势方向")

        return self.create_signal(signal_type, direction, strength, reasons, {
            "ma5": ma5,
            "ma10": ma10,
            "ma20": ma20,
            "ma60": ma60,
            "current_close": current_close,
        })

    def get_required_columns(self) -> list:
        return ["date", "open", "high", "low", "close", "volume"]

    def _empty_signal(self) -> Dict[str, Any]:
        return self.create_signal("none", "neutral", 50, [])
