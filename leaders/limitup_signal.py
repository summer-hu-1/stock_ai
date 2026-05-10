from typing import Dict, Any, List
import pandas as pd
import numpy as np
from .base_leader import BaseLeader


class LimitUpSignal(BaseLeader):
    def __init__(self):
        super().__init__("LimitUpSignal")
        self.limit_threshold = 9.5

    def detect(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.validate_data(df):
            return self._empty_result()

        price_change = df["price_change_pct"].astype(float)
        volume = df["volume"].astype(float)
        turnover_rate = df["turnover_rate"].astype(float)
        close = df["close"].astype(float)

        reasons = []
        metadata = {}

        is_limit_up_today = self._check_limit_up(price_change.iloc[-1]) if len(price_change) > 0 else False
        metadata["is_limit_up_today"] = is_limit_up_today

        limit_up_count = self._count_limit_up_streak(price_change)
        metadata["consecutive_limit_ups"] = limit_up_count

        limit_down_count = self._count_limit_down_streak(price_change)
        metadata["consecutive_limit_downs"] = limit_down_count

        if limit_up_count >= 3:
            signal_type = "continuous_limit_up"
            direction = "bullish"
            strength = min(100, 85 + limit_up_count * 5)
            reasons.append(f"连续涨停 {limit_up_count} 天")
            reasons.append("市场焦点股")

        elif limit_up_count == 2:
            signal_type = "second_limit_up"
            direction = "bullish"
            strength = 80
            reasons.append("连续涨停第二天")
            reasons.append("强势延续")

        elif limit_up_count == 1:
            signal_type = "single_limit_up"
            direction = "bullish"
            strength = 70
            reasons.append("今日涨停")
            reasons.append("封板强度待观察")

        elif is_limit_up_today:
            signal_type = "limit_up_today"
            direction = "bullish"
            strength = 75
            reasons.append("今日涨停")

        elif limit_down_count >= 1:
            signal_type = "limit_down"
            direction = "bearish"
            strength = min(90, 70 + limit_down_count * 10)
            reasons.append(f"连续跌停 {limit_down_count} 天")
            reasons.append("规避风险")

        else:
            change_today = float(price_change.iloc[-1]) if len(price_change) > 0 else 0

            if change_today >= 7:
                signal_type = "near_limit_up"
                direction = "bullish"
                strength = 60
                reasons.append(f"逼近涨停，涨幅 {change_today:.1f}%")

            elif change_today >= 5:
                signal_type = "strong_rise"
                direction = "bullish"
                strength = 55
                reasons.append(f"强势上涨 {change_today:.1f}%")

            elif change_today <= -7:
                signal_type = "near_limit_down"
                direction = "bearish"
                strength = 65
                reasons.append(f"逼近跌停，跌幅 {abs(change_today):.1f}%")

            elif change_today <= -5:
                signal_type = "strong_fall"
                direction = "bearish"
                strength = 55
                reasons.append(f"大幅下跌 {abs(change_today):.1f}%")

            else:
                signal_type = "normal"
                direction = "neutral"
                strength = 50
                reasons.append("涨跌正常")

        if signals and "volume" in signals:
            vol_signal = signals["volume"]
            vol_ratio = vol_signal.get("metadata", {}).get("volume_ratio", 1.0)
            if vol_ratio > 2 and direction == "bullish":
                strength = min(100, strength + 10)
                reasons.append("成交量配合")

        if signals and "trend" in signals:
            trend_signal = signals["trend"]
            if trend_signal.get("direction") == "bullish":
                strength = min(100, strength + 5)
                reasons.append("趋势向上")

        limit_up_info = self._analyze_limit_up_pattern(price_change, volume, turnover_rate)
        metadata.update(limit_up_info)

        is_leader = limit_up_count >= 2 or (is_limit_up_today and limit_up_count >= 1)

        return self.create_leader_result(
            is_leader=is_leader,
            leader_score=strength,
            leader_type=signal_type,
            reasons=reasons,
            metadata=metadata
        )

    def _check_limit_up(self, price_change: float, threshold: float = None) -> bool:
        threshold = threshold or self.limit_threshold
        return price_change >= threshold

    def _count_limit_up_streak(self, price_change: pd.Series) -> int:
        count = 0
        for i in range(len(price_change) - 1, -1, -1):
            if self._check_limit_up(price_change.iloc[i]):
                count += 1
            else:
                break
        return count

    def _count_limit_down_streak(self, price_change: pd.Series, threshold: float = -9.5) -> int:
        count = 0
        for i in range(len(price_change) - 1, -1, -1):
            if price_change.iloc[i] <= threshold:
                count += 1
            else:
                break
        return count

    def _analyze_limit_up_pattern(
        self,
        price_change: pd.Series,
        volume: pd.Series,
        turnover_rate: pd.Series
    ) -> Dict[str, Any]:
        info = {
            "limit_up_days": 0,
            "limit_up_rate": 0.0,
            "avg_turnover_after_limit_up": 0.0,
        }

        if len(price_change) < 5:
            return info

        limit_ups = (price_change >= self.limit_threshold).sum()
        info["limit_up_days"] = int(limit_ups)

        info["limit_up_rate"] = float(limit_ups / len(price_change) * 100)

        return info

    def get_required_columns(self) -> List[str]:
        return ["date", "close", "volume", "price_change_pct", "turnover_rate"]

    def _empty_result(self) -> Dict[str, Any]:
        return self.create_leader_result(
            is_leader=False,
            leader_score=50,
            leader_type="normal",
            reasons=["数据不足"],
            metadata={}
        )
