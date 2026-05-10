from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_signal import BaseSignal


class VolumeSignal(BaseSignal):
    def __init__(self):
        super().__init__("VolumeSignal")

    def generate(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.validate_data(df, self.get_required_columns()):
            return self._empty_signal()

        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        reasons = []
        signal_type = "none"
        direction = "neutral"
        strength = 0

        current_volume = float(volume.iloc[-1])
        vol_ma5 = float(volume.iloc[-5:].mean()) if len(volume) >= 5 else float(volume.mean())
        vol_ma10 = float(volume.iloc[-10:].mean()) if len(volume) >= 10 else vol_ma5
        vol_ma20 = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else vol_ma5

        volume_ratio = current_volume / vol_ma5 if vol_ma5 > 0 else 1.0
        volume_ratio_10 = current_volume / vol_ma10 if vol_ma10 > 0 else 1.0

        current_close = float(close.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) >= 2 else current_close
        price_change = ((current_close / prev_close) - 1) * 100 if prev_close != 0 else 0

        volume_increasing = volume_ratio > 1.5
        volume_decreasing = volume_ratio < 0.5
        volume_extreme = volume_ratio > 3.0

        if volume_extreme and price_change > 3:
            signal_type = "volume_price_surge"
            direction = "bullish"
            strength = min(95, int(60 + volume_ratio * 10 + price_change * 2))
            reasons.append(f"成交量暴增 {volume_ratio:.1f}倍")
            reasons.append(f"价格大幅上涨 {price_change:.1f}%")
            reasons.append("量价齐升，强势信号")

        elif volume_extreme and price_change < -3:
            signal_type = "volume_price_crash"
            direction = "bearish"
            strength = min(95, int(60 + volume_ratio * 10 + abs(price_change) * 2))
            reasons.append(f"成交量暴增 {volume_ratio:.1f}倍")
            reasons.append(f"价格大幅下跌 {abs(price_change):.1f}%")
            reasons.append("放量下跌，警惕风险")

        elif volume_increasing and price_change > 2:
            signal_type = "volume_support_up"
            direction = "bullish"
            strength = min(80, int(50 + volume_ratio * 8 + price_change * 3))
            reasons.append(f"成交量放大 {volume_ratio:.1f}倍")
            reasons.append(f"价格上涨 {price_change:.1f}% 配合")

        elif volume_increasing and price_change < -2:
            signal_type = "volume_warning_down"
            direction = "bearish"
            strength = min(80, int(50 + volume_ratio * 8 + abs(price_change) * 3))
            reasons.append(f"成交量放大 {volume_ratio:.1f}倍")
            reasons.append(f"价格下跌 {abs(price_change):.1f}% 配合")

        elif volume_decreasing:
            if abs(price_change) < 1:
                signal_type = "quiet_consolidation"
                direction = "neutral"
                strength = 40
                reasons.append("缩量盘整，观望为主")
            else:
                signal_type = "volume_shrink_trend"
                direction = "neutral"
                strength = 35
                reasons.append("缩量调整，动能减弱")

        if factors and "momentum" in factors:
            mom = factors["momentum"]
            acceleration = mom.get("acceleration", "unknown")
            if acceleration == "accelerating" and direction == "bullish":
                strength = min(100, strength + 10)
                reasons.append("动量加速中")
            elif acceleration == "decelerating" and direction == "bearish":
                strength = min(100, strength + 10)
                reasons.append("动量衰减中")

        vol_trend = self._calc_volume_trend(volume)
        if vol_trend == "increasing" and direction == "bullish":
            strength = min(100, strength + 5)
            reasons.append("成交量持续放大")
        elif vol_trend == "decreasing" and direction == "bearish":
            strength = min(100, strength + 5)
            reasons.append("成交量持续萎缩")

        if signal_type == "none":
            signal_type = "normal_volume"
            direction = "neutral"
            strength = 50
            reasons.append("成交量正常，无明显信号")

        return self.create_signal(signal_type, direction, strength, reasons, {
            "volume_ratio": volume_ratio,
            "volume_ratio_10": volume_ratio_10,
            "price_change": price_change,
            "vol_ma5": vol_ma5,
            "vol_ma20": vol_ma20,
        })

    def _calc_volume_trend(self, volume: pd.Series) -> str:
        if len(volume) < 10:
            return "stable"

        recent_5 = volume.iloc[-5:].mean()
        prev_5 = volume.iloc[-10:-5].mean()

        if recent_5 > prev_5 * 1.3:
            return "increasing"
        elif recent_5 < prev_5 * 0.7:
            return "decreasing"
        else:
            return "stable"

    def get_required_columns(self) -> list:
        return ["date", "open", "high", "low", "close", "volume"]

    def _empty_signal(self) -> Dict[str, Any]:
        return self.create_signal("none", "neutral", 50, [])
