from typing import Dict, Any
from datetime import datetime
import logging

from core.quant_core.models import FactorOutput, SignalOutput, StateOutput, LeaderOutput, ScoreOutput


logger = logging.getLogger(__name__)


class ScoreEngine:
    """
    综合评分引擎

    核心算法：
        1. 因子加权：trend(0.25) + momentum(0.20) + volume(0.20) + volatility(0.15) + strength(0.20)
        2. 信号调整：bullish +10, bearish -10
        3. 市场状态调整：
            - 主升期：+15
            - 冰点期：-10
            - 退潮期：-15
        4. 龙头加分：is_leader +10
        5. 最终映射到 0-100

    职责：
        输入：factors, signals, state, leader_score
        输出：ScoreOutput
    """

    # 权重配置
    WEIGHTS = {
        'trend': 0.25,
        'momentum': 0.20,
        'volume': 0.20,
        'volatility': 0.15,
        'strength': 0.20
    }

    # 市场状态调整值
    MARKET_STATE_ADJ = {
        '冰点': -10,
        '修复': 0,
        '主升': +15,
        '分歧': -5,
        '高潮': +10,
        '退潮': -15
    }

    # 信号强度调整
    SIGNAL_BUY_ADJ = 10
    SIGNAL_SELL_ADJ = -10
    SIGNAL_HOLD_ADJ = 0

    # 龙头加分
    LEADER_BONUS = 10
    LEADER_STRONG_BONUS = 15

    def __init__(self):
        pass

    def calculate(
        self,
        code: str,
        factors: FactorOutput,
        signals: SignalOutput,
        state: StateOutput,
        leader_output: LeaderOutput
    ) -> ScoreOutput:
        """
        核心评分计算函数
        """
        date = datetime.now()

        # 1. 因子加权基础分
        base_score = self._calculate_factor_base(factors)

        # 2. 信号调整
        signal_adj = self._calculate_signal_adj(signals)

        # 3. 市场状态调整
        market_adj = self._calculate_market_adj(state)

        # 4. 龙头加分
        leader_bonus = self._calculate_leader_bonus(leader_output)

        # 5. 综合计算
        final_score = base_score + signal_adj + market_adj + leader_bonus
        final_score = max(0, min(100, final_score))  # 限制在 0-100

        # 6. 生成信号
        signal, confidence = self._generate_trading_signal(final_score, state, signals)

        # 7. 构建分数分解
        score_breakdown = {
            'base_factor': base_score,
            'signal': signal_adj,
            'market_state': market_adj,
            'leader': leader_bonus,
            'final': final_score
        }

        return ScoreOutput(
            code=code,
            date=date,
            final_score=final_score,
            trend_score=factors.summary.trend_score,
            momentum_score=factors.summary.momentum_score,
            volume_score=factors.summary.volume_score,
            volatility_score=factors.summary.volatility_score,
            strength_score=factors.summary.strength_score,
            leader_bonus=leader_bonus,
            market_state_adj=market_adj,
            signal=signal,
            confidence=confidence,
            score_breakdown=score_breakdown
        )

    def _calculate_factor_base(self, factors: FactorOutput) -> float:
        """
        计算因子基础分
        """
        summary = factors.summary

        base_score = (
            summary.trend_score * self.WEIGHTS['trend'] +
            summary.momentum_score * self.WEIGHTS['momentum'] +
            summary.volume_score * self.WEIGHTS['volume'] +
            summary.volatility_score * self.WEIGHTS['volatility'] +
            summary.strength_score * self.WEIGHTS['strength']
        )

        return base_score

    def _calculate_signal_adj(self, signals: SignalOutput) -> float:
        """
        计算信号调整值
        """
        summary = signals.summary

        if summary.direction == "bullish":
            return self.SIGNAL_BUY_ADJ
        elif summary.direction == "bearish":
            return self.SIGNAL_SELL_ADJ
        else:
            return self.SIGNAL_HOLD_ADJ

    def _calculate_market_adj(self, state: StateOutput) -> float:
        """
        计算市场状态调整值
        """
        cycle = state.cycle
        adj = self.MARKET_STATE_ADJ.get(cycle, 0)

        # 如果是退潮期且有风险警告，额外扣分
        if cycle == "退潮" and state.risk_level == "高":
            adj -= 10

        # 如果是主升期且情绪上升，额外加分
        if cycle == "主升" and state.emotion_trend == "上升":
            adj += 5

        return adj

    def _calculate_leader_bonus(self, leader_output: LeaderOutput) -> float:
        """
        计算龙头加分
        """
        if not leader_output.is_leader:
            return 0

        if leader_output.leader_type == "龙头":
            if leader_output.leader_score >= 80:
                return self.LEADER_STRONG_BONUS
            return self.LEADER_BONUS

        return self.LEADER_BONUS * 0.5

    def _generate_trading_signal(
        self,
        score: float,
        state: StateOutput,
        signals: SignalOutput
    ) -> tuple[str, float]:
        """
        根据综合分生成交易信号
        """
        if score >= 80:
            signal = "看多"
            confidence = 0.85
        elif score >= 65:
            signal = "谨慎看多"
            confidence = 0.70
        elif score >= 45:
            signal = "观望"
            confidence = 0.50
        elif score >= 30:
            signal = "谨慎看空"
            confidence = 0.70
        else:
            signal = "看空"
            confidence = 0.85

        # 市场状态调整置信度
        if state.cycle == "主升" and signal in ["看多", "谨慎看多"]:
            confidence = min(0.95, confidence + 0.1)
        elif state.cycle == "退潮" and signal in ["看空", "谨慎看空"]:
            confidence = min(0.95, confidence + 0.1)
        elif state.cycle == "冰点" and signal in ["看空"]:
            confidence = max(0.5, confidence - 0.1)

        return signal, confidence

    def get_dynamic_weights(self, state: StateOutput) -> Dict[str, float]:
        """
        根据市场状态返回动态权重（供外部使用）
        """
        cycle = state.cycle
        weights = self.WEIGHTS.copy()

        if cycle == "主升":
            # 主升期：更重视趋势和动量
            weights['trend'] = 0.30
            weights['momentum'] = 0.25
            weights['volatility'] = 0.10
        elif cycle == "退潮":
            # 退潮期：更重视风险和成交量
            weights['volatility'] = 0.25
            weights['volume'] = 0.25
            weights['trend'] = 0.15
            weights['momentum'] = 0.15
        elif cycle == "冰点":
            # 冰点期：更重视超跌反弹
            weights['strength'] = 0.25
            weights['momentum'] = 0.25
            weights['trend'] = 0.20
            weights['volume'] = 0.20
            weights['volatility'] = 0.10

        return weights
