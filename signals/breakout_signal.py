from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_signal import BaseSignal


class BreakoutSignal(BaseSignal):
    def __init__(self):
        super().__init__("BreakoutSignal")

    def generate(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_signal()

        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        reasons = []
        signal_type = "none"
        direction = "neutral"
        strength = 0

        high_20d = float(high.iloc[-20:].max()) if len(high) >= 20 else float(high.max())
        high_60d = float(high.iloc[-60:].max()) if len(high) >= 60 else float(high.max())
        low_20d = float(low.iloc[-20:].min()) if len(low) >= 20 else float(low.min())

        current_close = float(close.iloc[-1])
        current_volume = float(volume.iloc[-1])

        volume_ma5 = float(volume.iloc[-5:].mean()) if len(volume) >= 5 else float(volume.mean())
        volume_ratio = current_volume / volume_ma5 if volume_ma5 > 0 else 1.0

        breakout_20d = current_close > high_20d and volume_ratio > 1.5
        breakout_60d = current_close > high_60d and volume_ratio > 2.0

        close_breakout_20d_pct = self.calc_distance_percent(current_close, high_20d)

        if breakout_60d and close_breakout_20d_pct < 5:
            signal_type = "breakout_60d"
            direction = "bullish"
            strength = min(95, int(70 + volume_ratio * 10 + close_breakout_20d_pct * 2))
            reasons.append(f"突破60日高点 {high_60d:.2f}，涨幅 {close_breakout_20d_pct:.1f}%")
            reasons.append(f"成交量放大 {volume_ratio:.1f}倍")
        elif breakout_20d:
            signal_type = "breakout_20d"
            direction = "bullish"
            strength = min(85, int(55 + volume_ratio * 10 + close_breakout_20d_pct * 3))
            reasons.append(f"突破20日高点 {high_20d:.2f}，涨幅 {close_breakout_20d_pct:.1f}%")
            reasons.append(f"成交量放大 {volume_ratio:.1f}倍")

        volume_breakout = volume_ratio > 2.5
        if volume_breakout and direction == "bullish":
            strength = min(100, strength + 10)
            reasons.append("成交量异常放大")

        if factors and "trend" in factors:
            trend = factors["trend"]
            if trend.get("ma_bullish"):
                strength = min(100, strength + 5)
                reasons.append("均线多头排列支持")

        if signal_type == "none":
            if current_close < low_20d * 1.05:
                signal_type = "near_support"
                direction = "neutral"
                strength = 30
                reasons.append(f"接近20日支撑位 {low_20d:.2f}")

        return self.create_signal(signal_type, direction, strength, reasons, {
            "high_20d": high_20d,
            "high_60d": high_60d,
            "low_20d": low_20d,
            "volume_ratio": volume_ratio,
            "breakout_pct": close_breakout_20d_pct,
        })

    def get_required_columns(self) -> list:
        return ["date", "open", "high", "low", "close", "volume"]

    def _empty_signal(self) -> Dict[str, Any]:
        return self.create_signal("none", "neutral", 0, [])
