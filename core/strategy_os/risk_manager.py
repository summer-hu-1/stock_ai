"""
风险管理器 - RiskManager

职责：
- 实时监控风险敞口
- 设置止损止盈
- 控制最大回撤
- 生成风险警告

风控原则：
- 永远不让单只股票亏损超过 10%
- 总仓位不超过风险等级上限
- 回撤超过 15% 时触发强减仓
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from core.strategy_os.models import RiskControlOutput, Position

logger = logging.getLogger(__name__)


class RiskManager:
    """
    风险管理器

    风控规则：
    1. 单股止损线：亏损 7% 警告，亏损 10% 强平
    2. 总仓位上限：低风险 100%，中风险 80%，高风险 50%
    3. 最大回撤：15% 触发减仓警告
    4. VaR 监控：95% 置信度下的最大日损失
    """

    # 单股止损阈值
    STOP_LOSS_WARNING = 0.07   # 7% 警告
    STOP_LOSS_MANDATORY = 0.10  # 10% 强平

    # 仓位上限
    POSITION_LIMITS = {
        "低": 1.0,
        "中": 0.8,
        "高": 0.5
    }

    # 回撤阈值
    DRAWDOWN_WARNING = 0.10   # 10% 警告
    DRAWDOWN_MANDATORY = 0.15  # 15% 强减仓

    def __init__(self):
        self.daily_pnl_history: List[float] = []
        self.peak_value = 100000.0  # 初始峰值
        self.current_value = 100000.0  # 当前总值

    def check_risk(
        self,
        positions: List[Position],
        total_position: float,
        risk_level: str,
        market_risk: str = "中"
    ) -> RiskControlOutput:
        """
        检查整体风险

        Args:
            positions: 持仓列表
            total_position: 总仓位比例
            risk_level: 风险等级（低/中/高）
            market_risk: 市场风险等级

        Returns:
            RiskControlOutput: 风控结果
        """
        warnings = []
        stop_loss_triggered = False

        # 1. 检查单股止损
        for pos in positions:
            pnl_pct = pos.profit_loss_pct / 100.0

            if pnl_pct <= -self.STOP_LOSS_MANDATORY:
                warnings.append(
                    f"🚨 {pos.code} 亏损 {abs(pnl_pct)*100:.1f}%，触发强平线！"
                )
                stop_loss_triggered = True
            elif pnl_pct <= -self.STOP_LOSS_WARNING:
                warnings.append(
                    f"⚠️ {pos.code} 亏损 {abs(pnl_pct)*100:.1f}%，注意止损"
                )

        # 2. 检查总仓位上限
        position_limit = self.POSITION_LIMITS.get(risk_level, 0.8)
        if total_position > position_limit:
            warnings.append(
                f"⚠️ 当前仓位 {total_position*100:.1f}% 超过上限 {position_limit*100:.1f}%"
            )

        # 3. 检查最大回撤
        max_drawdown = self._calculate_max_drawdown()
        if max_drawdown >= self.DRAWDOWN_MANDATORY:
            warnings.append(
                f"🚨 最大回撤 {max_drawdown*100:.1f}%，触发强减仓！"
            )
            stop_loss_triggered = True
        elif max_drawdown >= self.DRAWDOWN_WARNING:
            warnings.append(
                f"⚠️ 最大回撤 {max_drawdown*100:.1f}%，注意控制风险"
            )

        # 4. 计算 VaR (简化版)
        var_95 = self._calculate_var_95()

        # 5. 检查市场风险
        if market_risk == "高":
            warnings.append("⚠️ 市场风险等级高，建议降低整体仓位")

        return RiskControlOutput(
            date=datetime.now(),
            risk_level=risk_level,
            max_drawdown=max_drawdown,
            var_95=var_95,
            position_limit=position_limit,
            stop_loss_triggered=stop_loss_triggered,
            warnings=warnings
        )

    def _calculate_max_drawdown(self) -> float:
        """
        计算当前最大回撤
        """
        if self.peak_value <= 0:
            return 0.0

        drawdown = (self.peak_value - self.current_value) / self.peak_value
        return max(0.0, drawdown)

    def _calculate_var_95(self) -> float:
        """
        计算 95% VaR（简化版，使用历史波动率）

        Returns:
            float: 95% 置信度下的最大损失比例
        """
        if len(self.daily_pnl_history) < 2:
            return 0.0

        import statistics
        if len(self.daily_pnl_history) >= 2:
            std_dev = statistics.stdev(self.daily_pnl_history)
            mean = statistics.mean(self.daily_pnl_history)
            # 简化 VaR 估算：mean - 1.65 * std_dev
            var = abs(mean - 1.65 * std_dev)
            return max(0.0, var / self.current_value if self.current_value > 0 else 0.0)

        return 0.0

    def update_value(self, current_value: float):
        """
        更新当前市值

        Args:
            current_value: 当前总市值
        """
        self.current_value = current_value
        if current_value > self.peak_value:
            self.peak_value = current_value

    def record_daily_pnl(self, pnl: float):
        """
        记录每日盈亏

        Args:
            pnl: 当日盈亏金额
        """
        self.daily_pnl_history.append(pnl)
        # 只保留最近 252 个交易日
        if len(self.daily_pnl_history) > 252:
            self.daily_pnl_history.pop(0)

    def should_stop_loss(
        self,
        position: Position,
        force: bool = False
    ) -> tuple[bool, str]:
        """
        判断是否应该止损

        Args:
            position: 持仓信息
            force: 是否强制检查

        Returns:
            (should_stop, reason)
        """
        pnl_pct = position.profit_loss_pct / 100.0

        if pnl_pct <= -self.STOP_LOSS_MANDATORY:
            return True, f"亏损 {abs(pnl_pct)*100:.1f}%，触发强平线"

        if force and pnl_pct <= -self.STOP_LOSS_WARNING:
            return True, f"亏损 {abs(pnl_pct)*100:.1f}%，触发警告线"

        return False, ""

    def should_take_profit(
        self,
        position: Position,
        take_profit_pct: float = 0.15
    ) -> tuple[bool, str]:
        """
        判断是否应该止盈

        Args:
            position: 持仓信息
            take_profit_pct: 止盈阈值

        Returns:
            (should_stop, reason)
        """
        pnl_pct = position.profit_loss_pct / 100.0

        if pnl_pct >= take_profit_pct:
            return True, f"盈利 {pnl_pct*100:.1f}%，达到止盈线"

        return False, ""

    def get_position_limit(self, risk_level: str) -> float:
        """
        获取指定风险等级下的仓位上限
        """
        return self.POSITION_LIMITS.get(risk_level, 0.8)
