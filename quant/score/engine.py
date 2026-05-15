"""
综合评分引擎 - QuantCore

基于因子和信号计算综合评分
"""

from typing import Dict
import pandas as pd
import numpy as np


class ScoreEngine:
    """
    综合评分引擎

    权重配置：
    - trend: 30%
    - momentum: 20%
    - volume: 20%
    - volatility: 15%
    - strength: 15%
    """

    WEIGHTS = {
        "trend": 0.30,
        "momentum": 0.20,
        "volume": 0.20,
        "volatility": 0.15,
        "strength": 0.15,
    }

    def calculate(self, df: pd.DataFrame) -> float:
        """
        计算综合评分

        Args:
            df: K线数据

        Returns:
            float: 0-1评分
        """
        from quant.factor.engine import FactorEngine
        from quant.signal.engine import SignalEngine

        factor_engine = FactorEngine()
        signal_engine = SignalEngine()

        factors = factor_engine.calculate(df)
        signals = signal_engine.generate(df)

        score = self._calculate_score(factors, signals)
        return round(score, 4)

    def _calculate_score(
        self,
        factors: Dict[str, float],
        signals: Dict
    ) -> float:
        """计算加权评分"""
        score = 0.0

        for factor, weight in self.WEIGHTS.items():
            factor_value = factors.get(factor, 0.5)
            score += factor_value * weight

        if signals.get("direction") == "up":
            score += 0.1
        elif signals.get("direction") == "down":
            score -= 0.1

        strength = signals.get("strength", 0)
        score = score * (1 + strength * 0.2)

        return np.clip(score, 0, 1)

    def calculate_with_weights(
        self,
        factors: Dict[str, float],
        signals: Dict,
        weights: Dict[str, float]
    ) -> float:
        """
        使用自定义权重计算评分

        Args:
            factors: 因子字典
            signals: 信号字典
            weights: 自定义权重

        Returns:
            float: 评分
        """
        score = 0.0
        for factor, weight in weights.items():
            factor_value = factors.get(factor, 0.5)
            score += factor_value * weight

        return np.clip(score, 0, 1)
