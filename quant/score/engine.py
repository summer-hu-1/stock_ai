"""
综合评分引擎 - QuantCore

基于因子和信号计算综合评分
"""

from typing import Dict
import pandas as pd
import numpy as np
from ..models import ScoreResult


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

    def calculate(self, df: pd.DataFrame) -> ScoreResult:
        """
        计算综合评分

        Args:
            df: K线数据

        Returns:
            ScoreResult: 评分结果对象
        """
        from quant.factor.engine import FactorEngine
        from quant.signal.engine import SignalEngine

        factor_engine = FactorEngine()
        signal_engine = SignalEngine()

        factors = factor_engine.calculate(df)
        signals = signal_engine.generate(df)

        return self._calculate_score(factors, signals)

    def _calculate_score(
        self,
        factors: Dict[str, float],
        signals: Dict
    ) -> ScoreResult:
        """计算加权评分，返回 ScoreResult 对象"""
        score = 0.0

        for factor, weight in self.WEIGHTS.items():
            factor_data = factors.get(factor, {})
            if isinstance(factor_data, dict):
                factor_value = factor_data.get("score", 0.5)
            else:
                factor_value = factor_data
            score += factor_value * weight

        signal_direction = signals.get("direction", "neutral")
        if signal_direction == "up":
            score += 0.1
        elif signal_direction == "down":
            score -= 0.1

        strength = signals.get("strength", 0)
        score = score * (1 + strength * 0.2)

        final_score = np.clip(score, 0, 1) * 100
        
        trade_signal = "观望"
        if final_score >= 70:
            trade_signal = "买入"
        elif final_score >= 50:
            trade_signal = "持有"
        elif final_score < 30:
            trade_signal = "卖出"
        
        confidence = min(1.0, abs(score - 0.5) * 2)
        
        risk_level = "中等"
        if final_score >= 70:
            risk_level = "低"
        elif final_score < 30:
            risk_level = "高"
        
        trend_data = factors.get("trend", {})
        momentum_data = factors.get("momentum", {})
        volume_data = factors.get("volume", {})
        volatility_data = factors.get("volatility", {})
        strength_data = factors.get("strength", {})
        
        return ScoreResult(
            final_score=round(final_score, 1),
            signal=trade_signal,
            confidence=round(confidence, 2),
            risk_level=risk_level,
            trend_score=round(trend_data.get("score", 0.5) * 100, 1) if isinstance(trend_data, dict) else 50.0,
            momentum_score=round(momentum_data.get("score", 0.5) * 100, 1) if isinstance(momentum_data, dict) else 50.0,
            volume_score=round(volume_data.get("score", 0.5) * 100, 1) if isinstance(volume_data, dict) else 50.0,
            volatility_score=round(volatility_data.get("score", 0.5) * 100, 1) if isinstance(volatility_data, dict) else 50.0,
            strength_score=round(strength_data.get("score", 0.5) * 100, 1) if isinstance(strength_data, dict) else 50.0,
            leader_bonus=0.0,
            market_state_adj=0.0
        )

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
