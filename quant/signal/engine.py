"""
信号生成引擎 - QuantCore

支持多种信号：
- 突破信号 (breakout)
- 趋势信号 (trend)
- 反转信号 (reversal)
- 量能信号 (volume)

迁移自旧 signals/ 系统
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np


class SignalEngine:
    """
    信号生成引擎

    生成标准化的交易信号
    """

    def __init__(self):
        self.signal_types = ["breakout", "trend", "reversal", "volume"]

    def generate(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成所有信号

        Args:
            df: K线数据
            factors: 因子数据（可选）

        Returns:
            Dict: 信号结果
        """
        if df is None or df.empty or len(df) < 20:
            return self._empty_result()

        result = {
            "breakout": self._detect_breakout(df, factors),
            "trend": self._detect_trend(df, factors),
            "reversal": self._detect_reversal(df, factors),
            "volume": self._detect_volume(df, factors),
        }

        result["summary"] = self._generate_summary(result)

        return result

    def generate_single(self, df: pd.DataFrame, signal_name: str, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成单个信号

        Args:
            df: K线数据
            signal_name: 信号名称
            factors: 因子数据（可选）

        Returns:
            Dict: 信号结果
        """
        if signal_name not in self.signal_types:
            return {}

        methods = {
            "breakout": self._detect_breakout,
            "trend": self._detect_trend,
            "reversal": self._detect_reversal,
            "volume": self._detect_volume,
        }

        return methods[signal_name](df, factors)

    def get_signal_names(self) -> List[str]:
        """获取信号名称列表"""
        return self.signal_types.copy()

    def _detect_breakout(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测突破信号"""
        if not self._validate_data(df, ["close", "high", "low", "volume"]):
            return self._empty_breakout_result()

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

        close_breakout_20d_pct = self._calc_distance_percent(current_close, high_20d)

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

        return {
            "signal": signal_type,
            "direction": direction,
            "strength": strength,
            "reasons": reasons,
            "details": {
                "high_20d": high_20d,
                "high_60d": high_60d,
                "low_20d": low_20d,
                "volume_ratio": volume_ratio,
                "breakout_pct": close_breakout_20d_pct,
            }
        }

    def _detect_trend(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测趋势信号"""
        if not self._validate_data(df, ["close"]):
            return self._empty_trend_result()

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
                distance = self._calc_distance_percent(current_close, ma60)
                strength = min(95, 70 + int(distance / 2))
                reasons.append("均线多头排列（Ma5>Ma10>Ma20>Ma60）")
                reasons.append(f"价格距MA60上涨 {distance:.1f}%")

            elif ma5 < ma10 < ma20 < ma60:
                signal_type = "strong_downtrend"
                direction = "bearish"
                distance = self._calc_distance_percent(current_close, ma60)
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

        return {
            "signal": signal_type,
            "direction": direction,
            "strength": strength,
            "reasons": reasons,
            "details": {
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "ma60": ma60,
                "current_close": current_close,
            }
        }

    def _detect_reversal(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测反转信号"""
        if not self._validate_data(df, ["close", "high", "low", "volume"]):
            return self._empty_reversal_result()

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
                reasons.append(f"价格较60日均线下跌 {abs(self._calc_distance_percent(current_close, ma60)):.1f}%")

            elif downtrend_20d and today_change > 5:
                signal_type = "rebound_20d"
                direction = "bullish"
                strength = min(85, int(45 + today_change * 4))
                reasons.append(f"20日调整后反弹，今日涨幅 {today_change:.1f}%")

        if len(df) >= 5:
            prev_4_close = close.iloc[-5:-1]
            if len(prev_4_close) >= 4:
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

        return {
            "signal": signal_type,
            "direction": direction,
            "strength": strength,
            "reasons": reasons,
            "details": {
                "today_change": today_change,
                "volume_ratio": vol_ratio,
                "lower_shadow_pct": lower_shadow_pct,
                "upper_shadow_pct": upper_shadow_pct,
            }
        }

    def _detect_volume(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测量能信号"""
        if not self._validate_data(df, ["close", "volume"]):
            return self._empty_volume_result()

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

        return {
            "signal": signal_type,
            "direction": direction,
            "strength": strength,
            "reasons": reasons,
            "details": {
                "volume_ratio": volume_ratio,
                "volume_ratio_10": volume_ratio_10,
                "price_change": price_change,
                "vol_ma5": vol_ma5,
                "vol_ma20": vol_ma20,
            }
        }

    def _generate_summary(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """生成信号摘要"""
        summary = {
            "overall_direction": "neutral",
            "overall_strength": 50,
            "bullish_signals": [],
            "bearish_signals": [],
            "neutral_signals": [],
            "signal_count": 0,
        }

        for name, data in signals.items():
            if name == "summary" or name == "error":
                continue

            if "direction" not in data:
                continue

            summary["signal_count"] += 1
            signal_type = data.get("signal", "unknown")
            strength = data.get("strength", 50)

            if data["direction"] == "bullish" and strength >= 55:
                summary["bullish_signals"].append({
                    "type": name,
                    "signal": signal_type,
                    "strength": strength
                })
            elif data["direction"] == "bearish" and strength >= 55:
                summary["bearish_signals"].append({
                    "type": name,
                    "signal": signal_type,
                    "strength": strength
                })
            else:
                summary["neutral_signals"].append({
                    "type": name,
                    "signal": signal_type,
                    "strength": strength
                })

        bullish_count = len(summary["bullish_signals"])
        bearish_count = len(summary["bearish_signals"])

        if bullish_count > bearish_count:
            summary["overall_direction"] = "bullish"
            summary["overall_strength"] = min(95, 50 + (bullish_count - bearish_count) * 15)
        elif bearish_count > bullish_count:
            summary["overall_direction"] = "bearish"
            summary["overall_strength"] = min(95, 50 + (bearish_count - bullish_count) * 15)
        else:
            summary["overall_direction"] = "neutral"
            summary["overall_strength"] = 50

        return summary

    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "breakout": self._empty_breakout_result(),
            "trend": self._empty_trend_result(),
            "reversal": self._empty_reversal_result(),
            "volume": self._empty_volume_result(),
            "summary": {
                "overall_direction": "neutral",
                "overall_strength": 50,
                "bullish_signals": [],
                "bearish_signals": [],
                "neutral_signals": [],
                "signal_count": 0,
            }
        }

    def _empty_breakout_result(self) -> Dict[str, Any]:
        return {
            "signal": "none",
            "direction": "neutral",
            "strength": 0,
            "reasons": [],
            "details": {}
        }

    def _empty_trend_result(self) -> Dict[str, Any]:
        return {
            "signal": "none",
            "direction": "neutral",
            "strength": 50,
            "reasons": [],
            "details": {}
        }

    def _empty_reversal_result(self) -> Dict[str, Any]:
        return {
            "signal": "none",
            "direction": "neutral",
            "strength": 0,
            "reasons": [],
            "details": {}
        }

    def _empty_volume_result(self) -> Dict[str, Any]:
        return {
            "signal": "none",
            "direction": "neutral",
            "strength": 50,
            "reasons": [],
            "details": {}
        }

    # Helper methods
    def _validate_data(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """验证数据"""
        return all(col in df.columns for col in required_columns)

    def _calc_distance_percent(self, current: float, reference: float) -> float:
        """计算距离百分比"""
        if reference == 0:
            return 0.0
        return ((current - reference) / reference) * 100

    def _calc_volume_trend(self, volume: pd.Series) -> str:
        """计算量能趋势"""
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
