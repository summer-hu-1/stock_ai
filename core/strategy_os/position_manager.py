"""
仓位管理器 - PositionManager

职责：
- 计算目标仓位
- 管理持仓信息
- 计算浮动盈亏

核心逻辑：
1. 根据 QuantResult 的评分和市场状态计算目标仓位
2. 根据风险等级调整仓位
3. 管理持仓浮盈浮亏
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from core.quant_core.models import QuantResult, ScoreOutput
from core.strategy_os.models import (
    Position, PositionStrategy, RiskLevel,
    StrategyOutput
)

logger = logging.getLogger(__name__)


class PositionManager:
    """
    仓位管理器

    决策逻辑：
    - 高评分 + 主升期 → 满仓/重仓
    - 中评分 + 修复期 → 半仓
    - 低评分 + 冰点/退潮期 → 轻仓/空仓
    """

    # 评分到仓位的映射（基准）
    SCORE_TO_POSITION = {
        (80, 100): ("满仓", 1.0),
        (65, 80): ("重仓", 0.7),
        (45, 65): ("半仓", 0.5),
        (30, 45): ("轻仓", 0.3),
        (0, 30): ("空仓", 0.1)
    }

    # 市场周期到仓位系数
    CYCLE_ADJUSTMENT = {
        "主升": 1.2,
        "修复": 1.0,
        "分歧": 0.8,
        "高潮": 0.9,
        "冰点": 0.7,
        "退潮": 0.5
    }

    # 风险等级到仓位系数
    RISK_ADJUSTMENT = {
        "低": 1.0,
        "中": 0.8,
        "高": 0.5
    }

    def __init__(self):
        self.current_positions: Dict[str, Position] = {}
        self.total_capital: float = 100000.0  # 默认总资金

    def calculate_target_position(
        self,
        quant_result: QuantResult
    ) -> StrategyOutput:
        """
        根据量化结果计算目标仓位

        Args:
            quant_result: QuantCore 的分析结果

        Returns:
            StrategyOutput: 策略输出
        """
        score = quant_result.score
        state = quant_result.state

        # 1. 根据评分确定基准仓位
        base_position, base_ratio = self._get_base_position(score.final_score)

        # 2. 根据市场周期调整
        cycle_adj = self.CYCLE_ADJUSTMENT.get(state.cycle, 1.0)

        # 3. 根据风险等级调整
        risk_adj = self.RISK_ADJUSTMENT.get(state.risk_level, 0.8)

        # 4. 计算最终仓位
        target_ratio = base_ratio * cycle_adj * risk_adj
        target_ratio = max(0.0, min(1.0, target_ratio))

        # 5. 确定操作信号
        action, urgency = self._determine_action(
            target_ratio,
            quant_result.leaders.is_leader,
            state.risk_level
        )

        # 6. 生成原因列表
        reasons = self._generate_reasons(
            score, state, base_position, cycle_adj, risk_adj
        )

        # 7. 生成警告列表
        warnings = self._generate_warnings(state, score)

        return StrategyOutput(
            code=quant_result.code,
            date=datetime.now(),
            market_cycle=state.cycle,
            position_strategy=base_position,
            target_position=target_ratio,
            action=action,
            urgency=urgency,
            reasons=reasons,
            warnings=warnings,
            confidence=score.confidence
        )

    def _get_base_position(self, score: float) -> tuple:
        """
        根据评分获取基准仓位
        """
        for (low, high), (strategy, ratio) in self.SCORE_TO_POSITION.items():
            if low <= score < high:
                return strategy, ratio
        return ("半仓", 0.5)

    def _determine_action(
        self,
        target_ratio: float,
        is_leader: bool,
        risk_level: str
    ) -> tuple:
        """
        确定操作信号

        Returns:
            (action, urgency)
        """
        if target_ratio >= 0.7:
            if is_leader:
                return "买入", "立即执行"
            else:
                return "持有", "观察"
        elif target_ratio >= 0.4:
            return "持有", "观察"
        elif target_ratio >= 0.2:
            return "减仓", "观察"
        else:
            return "清仓", "立即执行"

    def _generate_reasons(
        self,
        score: ScoreOutput,
        state,
        base_position: str,
        cycle_adj: float,
        risk_adj: float
    ) -> List[str]:
        """
        生成策略原因列表
        """
        reasons = []

        reasons.append(f"综合评分 {score.final_score:.1f}，建议 {base_position}")

        if score.final_score >= 65:
            reasons.append("评分偏正面，可适当加仓")
        elif score.final_score <= 35:
            reasons.append("评分偏负面，建议控制仓位")

        if cycle_adj > 1.0:
            reasons.append(f"市场处于{state.cycle}期，仓位系数 ×{cycle_adj}")
        elif cycle_adj < 1.0:
            reasons.append(f"市场处于{state.cycle}期，仓位系数 ×{cycle_adj}")

        if risk_adj < 1.0:
            reasons.append(f"风险等级{state.risk_level}，仓位系数 ×{risk_adj}")

        if score.signal != "观望":
            reasons.append(f"信号: {score.signal}（置信度 {score.confidence:.0%}）")

        return reasons

    def _generate_warnings(
        self,
        state,
        score: ScoreOutput
    ) -> List[str]:
        """
        生成警告列表
        """
        warnings = []

        if state.risk_level == "高":
            warnings.append("⚠️ 当前风险等级较高，注意控制仓位")

        if state.cycle == "退潮":
            warnings.append("⚠️ 市场退潮期，建议谨慎")

        if state.cycle == "冰点":
            warnings.append("⚠️ 市场冰点期，可能存在机会但风险较大")

        if score.confidence < 0.6:
            warnings.append("⚠️ 信号置信度较低，建议等待更明确信号")

        if state.limit_up_count < 20:
            warnings.append(f"⚠️ 涨停家数较少（{state.limit_up_count}家），市场情绪偏弱")

        return warnings

    def update_position(
        self,
        code: str,
        shares: int,
        avg_cost: float,
        current_price: float
    ) -> Position:
        """
        更新持仓信息

        Args:
            code: 股票代码
            shares: 持股数量
            avg_cost: 平均成本
            current_price: 当前价格

        Returns:
            Position: 更新后的持仓信息
        """
        market_value = shares * current_price
        profit_loss = (current_price - avg_cost) * shares
        profit_loss_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0

        position = Position(
            code=code,
            position_ratio=0,  # 稍后计算
            shares=shares,
            avg_cost=avg_cost,
            current_price=current_price,
            market_value=market_value,
            profit_loss=profit_loss,
            profit_loss_pct=profit_loss_pct
        )

        position.position_ratio = market_value / self.total_capital
        self.current_positions[code] = position

        return position

    def calculate_total_position(self) -> float:
        """
        计算总仓位
        """
        total_market_value = sum(
            p.market_value for p in self.current_positions.values()
        )
        return total_market_value / self.total_capital

    def get_positions(self) -> List[Position]:
        """
        获取所有持仓
        """
        return list(self.current_positions.values())

    def set_total_capital(self, capital: float):
        """
        设置总资金
        """
        self.total_capital = capital
