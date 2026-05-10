from typing import Dict, Any, List
import pandas as pd
import numpy as np
from .base_leader import BaseLeader


class LeaderDetector(BaseLeader):
    def __init__(self):
        super().__init__("LeaderDetector")

    def detect(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.validate_data(df):
            return self._empty_result()

        close = df["close"].astype(float)
        volume = df["volume"].astype(float)
        price_change = df["price_change_pct"].astype(float)
        turnover_rate = df["turnover_rate"].astype(float)

        reasons = []
        metadata = {}

        limit_up_count = self._calc_limit_up_count(price_change)
        limit_up_score = self._calc_limit_up_score(limit_up_count, price_change)
        metadata["limit_up_count"] = limit_up_count

        momentum_score = self._calc_momentum_score(close, price_change)
        metadata["momentum_score"] = momentum_score

        volume_score = self._calc_volume_score(volume)
        metadata["volume_score"] = volume_score

        turnover_score = self._calc_turnover_score(turnover_rate)
        metadata["turnover_score"] = turnover_score

        strength_score = self._calc_strength_score(factors)
        metadata["strength_score"] = strength_score

        leader_score = int(
            limit_up_score * 0.30 +
            momentum_score * 0.25 +
            volume_score * 0.20 +
            turnover_score * 0.15 +
            strength_score * 0.10
        )

        is_leader, leader_type = self._determine_leader_type(leader_score, limit_up_count, momentum_score)

        if is_leader:
            if limit_up_count >= 3:
                reasons.append(f"连续涨停 {limit_up_count} 天")
            if momentum_score >= 80:
                reasons.append("超强动量")
            if volume_score >= 80:
                reasons.append("成交额异常放大")
            if turnover_score >= 75:
                reasons.append("高换手率")
            if leader_type == "龙头":
                reasons.append("市场核心领涨股")
            elif leader_type == "强势股":
                reasons.append("板块强势股")

        return self.create_leader_result(is_leader, leader_score, leader_type, reasons, metadata)

    def _calc_limit_up_count(self, price_change: pd.Series, threshold: float = 9.5) -> int:
        limit_ups = (price_change >= threshold).astype(int)
        count = 0
        for i in range(len(limit_ups) - 1, -1, -1):
            if limit_ups.iloc[i] == 1:
                count += 1
            else:
                break
        return count

    def _calc_limit_up_score(self, limit_up_count: int, price_change: pd.Series) -> int:
        if limit_up_count >= 5:
            return 100
        elif limit_up_count >= 3:
            return 90
        elif limit_up_count >= 2:
            return 80
        elif limit_up_count == 1:
            today_change = float(price_change.iloc[-1]) if len(price_change) > 0 else 0
            if today_change >= 9.5:
                return 75
            elif today_change >= 5:
                return 60
            else:
                return 40
        else:
            today_change = float(price_change.iloc[-1]) if len(price_change) > 0 else 0
            if today_change >= 7:
                return 50
            elif today_change >= 5:
                return 40
            else:
                return 20

    def _calc_momentum_score(self, close: pd.Series, price_change: pd.Series) -> int:
        if len(close) < 5:
            return 50

        current_close = float(close.iloc[-1])
        ma5 = float(close.iloc[-5:].mean())

        ma_distance = ((current_close / ma5) - 1) * 100 if ma5 > 0 else 0

        recent_change = float(price_change.iloc[-5:].sum()) if len(price_change) >= 5 else 0

        score = 50

        if ma_distance > 20:
            score += 30
        elif ma_distance > 15:
            score += 25
        elif ma_distance > 10:
            score += 20
        elif ma_distance > 5:
            score += 15
        elif ma_distance > 0:
            score += 10
        else:
            score -= 20

        if recent_change > 30:
            score += 20
        elif recent_change > 20:
            score += 15
        elif recent_change > 10:
            score += 10
        elif recent_change > 5:
            score += 5
        elif recent_change < -10:
            score -= 15

        return max(0, min(100, int(score)))

    def _calc_volume_score(self, volume: pd.Series) -> int:
        if len(volume) < 20:
            return 50

        current_volume = float(volume.iloc[-1])
        vol_ma20 = float(volume.iloc[-20:].mean())

        vol_ratio = current_volume / vol_ma20 if vol_ma20 > 0 else 1.0

        if vol_ratio > 5:
            return 95
        elif vol_ratio > 3:
            return 85
        elif vol_ratio > 2:
            return 75
        elif vol_ratio > 1.5:
            return 65
        elif vol_ratio > 1:
            return 55
        elif vol_ratio > 0.5:
            return 45
        else:
            return 35

    def _calc_turnover_score(self, turnover_rate: pd.Series) -> int:
        if len(turnover_rate) < 1:
            return 50

        current_turnover = float(turnover_rate.iloc[-1])

        if current_turnover > 30:
            return 95
        elif current_turnover > 20:
            return 85
        elif current_turnover > 15:
            return 75
        elif current_turnover > 10:
            return 65
        elif current_turnover > 5:
            return 55
        elif current_turnover > 2:
            return 45
        else:
            return 35

    def _calc_strength_score(self, factors: Dict[str, Any] = None) -> int:
        if factors is None:
            return 50

        score = 50

        if "strength" in factors:
            strength = factors["strength"]
            combined_strength = strength.get("combined_strength", 50)
            score = (score * 0.5 + combined_strength * 0.5)

        if "trend" in factors:
            trend = factors["trend"]
            trend_strength = trend.get("trend_strength", 50)
            score = (score * 0.7 + trend_strength * 0.3)

        return max(0, min(100, int(score)))

    def _determine_leader_type(self, leader_score: int, limit_up_count: int, momentum_score: int) -> tuple:
        if leader_score >= 85 and limit_up_count >= 2:
            return True, "龙头"
        elif leader_score >= 75 and momentum_score >= 70:
            return True, "强势股"
        elif leader_score >= 65 and limit_up_count >= 1:
            return True, "活跃股"
        elif leader_score >= 60:
            return True, "潜力股"
        else:
            return False, "普通"

    def _empty_result(self) -> Dict[str, Any]:
        return self.create_leader_result(False, 0, "普通", [], {})
