"""
因子计算引擎 - QuantCore

支持多种因子计算：
- 趋势因子 (trend)
- 量能因子 (volume)
- 动量因子 (momentum)
- 波动率因子 (volatility)
- 强度因子 (strength)

迁移自旧 factors/ 系统
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np


class FactorEngine:
    """
    因子计算引擎

    计算并返回标准化因子值和详细指标
    """

    def __init__(self):
        self.factors = ["trend", "volume", "momentum", "volatility", "strength"]

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算所有因子

        Args:
            df: K线数据

        Returns:
            Dict: {因子名: 因子详情}
        """
        if df is None or df.empty or len(df) < 20:
            return self._empty_result()

        result = {
            "trend": self._calc_trend(df),
            "volume": self._calc_volume(df),
            "momentum": self._calc_momentum(df),
            "volatility": self._calc_volatility(df),
            "strength": self._calc_strength(df),
        }

        result["summary"] = self._generate_summary(result)

        return result

    def calculate_single(self, df: pd.DataFrame, factor_name: str) -> Dict[str, Any]:
        """
        计算单个因子

        Args:
            df: K线数据
            factor_name: 因子名称

        Returns:
            Dict: 因子详情
        """
        if factor_name not in self.factors:
            return {}

        if df is None or df.empty or len(df) < 20:
            return {}

        methods = {
            "trend": self._calc_trend,
            "volume": self._calc_volume,
            "momentum": self._calc_momentum,
            "volatility": self._calc_volatility,
            "strength": self._calc_strength,
        }

        return methods[factor_name](df)

    def get_factor_names(self) -> List[str]:
        """获取因子名称列表"""
        return self.factors.copy()

    def _calc_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算趋势因子"""
        if not self._validate_data(df, ["close", "high", "low"]):
            return self._empty_trend_result()

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

        # 标准化评分 (0-1)
        normalized_score = trend_strength / 100

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
            "score": normalized_score,
        }

    def _calc_volume(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算量能因子"""
        if not self._validate_data(df, ["volume", "close"]):
            return self._empty_volume_result()

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

        # 标准化评分 (0-1)
        normalized_score = volume_score / 100

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
            "score": normalized_score,
        }

    def _calc_momentum(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算动量因子"""
        if not self._validate_data(df, ["close"]):
            return self._empty_momentum_result()

        close = df["close"].astype(float)

        returns = self._calculate_returns(close, [5, 10, 20, 60])

        momentum_rank = self._calc_momentum_rank(close)

        relative_strength = self._calc_relative_strength(close)

        momentum_score = self._calc_momentum_score(returns)

        acceleration = self._calc_acceleration(close)

        # 标准化评分 (0-1)
        normalized_score = momentum_score / 100

        return {
            "return_5d": returns.get("return_5d", 0),
            "return_10d": returns.get("return_10d", 0),
            "return_20d": returns.get("return_20d", 0),
            "return_60d": returns.get("return_60d", 0),
            "momentum_rank": momentum_rank,
            "relative_strength": relative_strength,
            "momentum_score": momentum_score,
            "acceleration": acceleration,
            "score": normalized_score,
        }

    def _calc_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算波动率因子"""
        if not self._validate_data(df, ["close"]):
            return self._empty_volatility_result()

        close = df["close"].astype(float)
        high = df["high"].astype(float) if "high" in df.columns else close
        low = df["low"].astype(float) if "low" in df.columns else close

        returns = np.diff(close) / close[:-1]

        if len(returns) < 10:
            return self._empty_volatility_result()

        std_20d = np.std(returns[-20:])
        std_60d = np.std(returns[-60:]) if len(returns) >= 60 else std_20d

        avg_true_range = self._calc_atr(high, low, close)

        volatility_score = min(std_20d * 100, 100)

        # 标准化评分 (0-1)
        normalized_score = volatility_score / 100

        return {
            "std_20d": std_20d,
            "std_60d": std_60d,
            "avg_true_range": avg_true_range,
            "volatility_score": int(volatility_score),
            "score": normalized_score,
        }

    def _calc_strength(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算强度因子"""
        if not self._validate_data(df, ["close"]):
            return self._empty_strength_result()

        close = df["close"].astype(float)
        high = df["high"].astype(float) if "high" in df.columns else close
        low = df["low"].astype(float) if "low" in df.columns else close
        opens = df["open"].astype(float) if "open" in df.columns else close

        if len(close) < 5:
            return self._empty_strength_result()

        current_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        current_open = opens.iloc[-1]
        current_high = high.iloc[-1]
        current_low = low.iloc[-1]

        body = abs(current_close - current_open)
        upper_shadow = current_high - max(current_close, current_open)
        lower_shadow = min(current_close, current_open) - current_low

        price_change = (current_close - close.iloc[-5]) / close.iloc[-5] * 100 if close.iloc[-5] != 0 else 0

        body_ratio = body / (current_high - current_low) if (current_high - current_low) != 0 else 0.5

        strength_score = 50
        if price_change > 3:
            strength_score += 20
        elif price_change > 1:
            strength_score += 10
        elif price_change < -3:
            strength_score -= 20
        elif price_change < -1:
            strength_score -= 10

        if body_ratio > 0.7:
            strength_score += 15
        elif body_ratio > 0.5:
            strength_score += 5

        if upper_shadow < body * 0.3:
            strength_score += 10

        strength_score = max(0, min(100, strength_score))

        # 标准化评分 (0-1)
        normalized_score = strength_score / 100

        return {
            "price_change_5d": price_change,
            "body_ratio": body_ratio,
            "upper_shadow": upper_shadow,
            "lower_shadow": lower_shadow,
            "strength_score": strength_score,
            "score": normalized_score,
        }

    def _generate_summary(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """生成因子摘要"""
        summary = {
            "overall_score": 50,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 0,
        }

        if "trend" in factors and "ma_bullish" in factors["trend"]:
            if factors["trend"]["ma_bullish"]:
                summary["bullish_signals"] += 1
            else:
                summary["bearish_signals"] += 1

        if "volume" in factors and "volume_breakout" in factors["volume"]:
            if factors["volume"]["volume_breakout"]:
                summary["bullish_signals"] += 1

        if "momentum" in factors and "return_5d" in factors["momentum"]:
            if factors["momentum"]["return_5d"] > 3:
                summary["bullish_signals"] += 1
            elif factors["momentum"]["return_5d"] < -3:
                summary["bearish_signals"] += 1

        total_signals = summary["bullish_signals"] + summary["bearish_signals"] + summary["neutral_signals"]
        if total_signals > 0:
            summary["overall_score"] = int(
                50 + (summary["bullish_signals"] - summary["bearish_signals"]) * 15
            )
            summary["overall_score"] = max(0, min(100, summary["overall_score"]))

        return summary

    def _empty_result(self) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "trend": self._empty_trend_result(),
            "volume": self._empty_volume_result(),
            "momentum": self._empty_momentum_result(),
            "volatility": self._empty_volatility_result(),
            "strength": self._empty_strength_result(),
            "summary": {
                "overall_score": 50,
                "bullish_signals": 0,
                "bearish_signals": 0,
                "neutral_signals": 0,
            }
        }

    def _empty_trend_result(self) -> Dict[str, Any]:
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
            "score": 0.5,
        }

    def _empty_volume_result(self) -> Dict[str, Any]:
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
            "score": 0.5,
        }

    def _empty_momentum_result(self) -> Dict[str, Any]:
        return {
            "return_5d": 0,
            "return_10d": 0,
            "return_20d": 0,
            "return_60d": 0,
            "momentum_rank": 50,
            "relative_strength": 50,
            "momentum_score": 50,
            "acceleration": "unknown",
            "score": 0.5,
        }

    def _empty_volatility_result(self) -> Dict[str, Any]:
        return {
            "std_20d": 0,
            "std_60d": 0,
            "avg_true_range": 0,
            "volatility_score": 50,
            "score": 0.5,
        }

    def _empty_strength_result(self) -> Dict[str, Any]:
        return {
            "price_change_5d": 0,
            "body_ratio": 0.5,
            "upper_shadow": 0,
            "lower_shadow": 0,
            "strength_score": 50,
            "score": 0.5,
        }

    # Helper methods
    def _validate_data(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """验证数据"""
        return all(col in df.columns for col in required_columns)

    def _calc_ma(self, series: pd.Series, period: int) -> float:
        """计算移动平均"""
        if len(series) < period:
            return None
        ma = series.iloc[-period:].mean()
        return float(ma) if not np.isnan(ma) else None

    def _check_alignment(self, ma5: float, ma10: float, ma20: float, ma60: float) -> str:
        """检查均线排列"""
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
        """计算趋势强度"""
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
        """检测均线交叉"""
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

        return {"golden_cross": golden_cross, "death_cross": death_cross}

    def _calc_distance_pct(self, current: float, ma: float) -> float:
        """计算距离百分比"""
        if ma is None or ma == 0:
            return 0.0
        return float(((current - ma) / ma) * 100)

    def _calc_volume_ratio(self, current: float, ma5: float) -> float:
        """计算量比"""
        if ma5 is None or ma5 == 0:
            return 1.0
        return float(current / ma5)

    def _calc_volume_pulse(self, volume: pd.Series, close: pd.Series) -> float:
        """计算量能脉冲"""
        if len(volume) < 5:
            return 0.0

        recent_vol = volume.iloc[-5:].mean()
        older_vol = volume.iloc[-20:-5].mean() if len(volume) >= 20 else recent_vol

        if older_vol == 0:
            return 0.0

        pulse = (recent_vol - older_vol) / older_vol * 100
        return float(pulse)

    def _calc_volume_continuity(self, volume: pd.Series) -> str:
        """计算量能持续性"""
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
        """计算量能评分"""
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

    def _calculate_returns(self, close: pd.Series, periods: List[int]) -> Dict[str, float]:
        """计算多周期收益率"""
        result = {}
        for period in periods:
            if len(close) >= period:
                ret = (close.iloc[-1] / close.iloc[-period] - 1) * 100
                result[f"return_{period}d"] = float(ret)
            else:
                result[f"return_{period}d"] = 0.0
        return result

    def _calc_momentum_rank(self, close: pd.Series) -> int:
        """计算动量排名"""
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
        """计算相对强度"""
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
        """计算动量评分"""
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
        """计算加速度"""
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

    def _calc_atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> float:
        """计算ATR"""
        if len(high) < 14:
            return 0.0

        tr = []
        for i in range(1, len(high)):
            tr_val = max(
                high.iloc[i] - low.iloc[i],
                abs(high.iloc[i] - close.iloc[i-1]),
                abs(low.iloc[i] - close.iloc[i-1])
            )
            tr.append(tr_val)

        if not tr:
            return 0.0

        return float(np.mean(tr[-14:]))
