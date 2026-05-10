from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_signal import BaseSignal


class ReversalSignal(BaseSignal):
    def __init__(self):
        super().__init__("ReversalSignal")

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

        current_close = float(close.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) >= 2 else current_close

        current_high = float(high.iloc[-1])
        current_low = float(low.iloc[-1])
        prev_high = float(high.iloc[-2]) if len(high) >= 2 else current_high
        prev_low = float(low.iloc[-2]) if len(low) >= 2 else current_low

        today_change = ((current_close / prev_close) - 1) * 100 if prev_close != 0 else 0

        if len(close) >= 20:
            ma20 = float(close.iloc[-20:].mean())
            ma60 = float(close.iloc[-60:].mean()) if len(close) >= 60 else ma20

            downtrend_20d = current_close < ma20 * 0.9
            downtrend_60d = current_close < ma60 * 0.85

            if downtrend_60d and today_change > 3:
                signal_type = "bottom_reversal"
                direction = "bullish"
                strength = min(90, int(50 + today_change * 3))
                reasons.append(f"长期下跌后底部反弹，今日涨幅 {today_change:.1f}%")
                reasons.append(f"价格较60日均线下跌 {abs(self.calc_distance_percent(current_close, ma60)):.1f}%")

            elif downtrend_20d and today_change > 5:
                signal_type = "rebound_20d"
                direction = "bullish"
                strength = min(85, int(45 + today_change * 4))
                reasons.append(f"20日调整后反弹，今日涨幅 {today_change:.1f}%")

        if len(df) >= 5:
            prev_4_close = close.iloc[-5:-1]
            prev_4_avg = float(prev_4_close.mean())
            continuous_decline = all(prev_4_close.iloc[i] < prev_4_close.iloc[i-1] for i in range(1, 4))

            if continuous_decline and today_change > 4:
                signal_type = "reversal_after_decline"
                direction = "bullish"
                strength = min(88, int(40 + today_change * 5))
                reasons.append("连续4日下跌后反弹")
                reasons.append(f"今日涨幅 {today_change:.1f}%")

        current_volume = float(volume.iloc[-1])
        vol_ma5 = float(volume.iloc[-5:].mean()) if len(volume) >= 5 else current_volume
        vol_ratio = current_volume / vol_ma5 if vol_ma5 > 0 else 1.0

        lower_shadow_pct = (current_close - current_low) / (current_high - current_low) * 100 if (current_high - current_low) > 0 else 50
        upper_shadow_pct = (current_high - current_close) / (current_high - current_low) * 100 if (current_high - current_low) > 0 else 50

        if lower_shadow_pct > 60 and today_change > 2:
            signal_type = "hammer_reversal"
            direction = "bullish"
            strength = min(80, int(50 + lower_shadow_pct / 2 + today_change * 3))
            reasons.append(f"长下影线（下影占比 {lower_shadow_pct:.0f}%）")
            reasons.append(f"今日涨幅 {today_change:.1f}%")

        elif upper_shadow_pct > 60 and today_change < -2:
            signal_type = "shooting_star_reversal"
            direction = "bearish"
            strength = min(80, int(50 + upper_shadow_pct / 2 + abs(today_change) * 3))
            reasons.append(f"长上影线（上影占比 {upper_shadow_pct:.0f}%）")
            reasons.append(f"今日跌幅 {abs(today_change):.1f}%")

        if signal_type == "none":
            if abs(today_change) < 1:
                signal_type = "low_volatility"
                direction = "neutral"
                strength = 30
                reasons.append("波动较小，无明显反转信号")

        return self.create_signal(signal_type, direction, strength, reasons, {
            "today_change": today_change,
            "volume_ratio": vol_ratio,
            "lower_shadow_pct": lower_shadow_pct,
            "upper_shadow_pct": upper_shadow_pct,
        })

    def get_required_columns(self) -> list:
        return ["date", "open", "high", "low", "close", "volume"]

    def _empty_signal(self) -> Dict[str, Any]:
        return self.create_signal("none", "neutral", 0, [])
