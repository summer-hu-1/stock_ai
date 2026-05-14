"""
策略调度引擎 - StrategyEngine

职责：
- 根据量化结果和市场状态生成交易指令
- 协调仓位管理和风险管理
- 决定买入/持有/减仓/清仓

核心算法：
1. 输入：QuantResult（评分、信号、市场状态）
2. 判断市场周期
3. 确定仓位策略
4. 应用风控规则
5. 输出：交易指令
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from core.quant_core.models import QuantResult
from core.strategy_os.models import (
    StrategyOutput, PortfolioOutput, RiskControlOutput
)
from core.strategy_os.position_manager import PositionManager
from core.strategy_os.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    策略调度引擎

    V10 架构核心：
    - 接收 QuantResult
    - 输出交易指令
    - 不做任何计算（由 QuantCore 完成）
    """

    def __init__(self):
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager()

    def generate_trade_decision(
        self,
        quant_result: QuantResult,
        current_positions: Optional[List[Dict]] = None
    ) -> Dict:
        """
        生成交易决策

        Args:
            quant_result: QuantCore 的分析结果
            current_positions: 当前持仓列表（可选）

        Returns:
            Dict: 完整的决策结果
        """
        logger.info(f"🎯 StrategyOS 开始生成交易决策: {quant_result.code}")

        # 1. 计算目标仓位
        strategy_output = self.position_manager.calculate_target_position(quant_result)

        # 2. 更新持仓（如有）
        if current_positions:
            for pos_dict in current_positions:
                self.position_manager.update_position(
                    code=pos_dict['code'],
                    shares=pos_dict.get('shares', 0),
                    avg_cost=pos_dict.get('avg_cost', 0),
                    current_price=pos_dict.get('current_price', 0)
                )

        # 3. 检查风险
        positions = self.position_manager.get_positions()
        total_position = self.position_manager.calculate_total_position()
        risk_output = self.risk_manager.check_risk(
            positions=positions,
            total_position=total_position,
            risk_level=quant_result.state.risk_level,
            market_risk=quant_result.state.risk_level
        )

        # 4. 应用风控规则
        final_decision = self._apply_risk_control(
            strategy_output, risk_output, positions
        )

        # 5. 生成组合状态
        portfolio_output = self._generate_portfolio_status(
            positions, total_position
        )

        logger.info(
            f"✅ 决策完成: {final_decision['action']} "
            f"{final_decision['target_position']*100:.0f}% "
            f"(置信度 {final_decision['confidence']:.0%})"
        )

        return {
            "success": True,
            "strategy": strategy_output,
            "risk": risk_output,
            "portfolio": portfolio_output,
            "final_decision": final_decision
        }

    def _apply_risk_control(
        self,
        strategy: StrategyOutput,
        risk: RiskControlOutput,
        positions: List
    ) -> Dict:
        """
        应用风控规则，修正交易决策

        Args:
            strategy: 策略输出
            risk: 风控输出
            positions: 持仓列表

        Returns:
            Dict: 修正后的最终决策
        """
        final_action = strategy.action
        final_position = strategy.target_position
        warnings = list(strategy.warnings)

        # 1. 如果触发止损，强制清仓
        if risk.stop_loss_triggered:
            final_action = "清仓"
            final_position = 0.0
            warnings.append("🚨 风控触发，强制清仓")

        # 2. 如果仓位超限，降低仓位
        if risk.position_limit < final_position:
            old_position = final_position
            final_position = risk.position_limit
            warnings.append(
                f"⚠️ 仓位从 {old_position*100:.0f}% 降至 {final_position*100:.0f}%（风控限制）"
            )

        # 3. 检查单股止损
        for pos in positions:
            should_stop, reason = self.risk_manager.should_stop_loss(pos)
            if should_stop:
                warnings.append(f"🚨 {pos.code}: {reason}")

        # 4. 确定最终操作
        if final_position > strategy.target_position + 0.1:
            final_action = "买入"
        elif final_position < strategy.target_position - 0.1:
            final_action = "减仓"
        else:
            final_action = "持有"

        return {
            "action": final_action,
            "target_position": final_position,
            "confidence": strategy.confidence,
            "warnings": warnings,
            "stop_loss_triggered": risk.stop_loss_triggered
        }

    def _generate_portfolio_status(
        self,
        positions: List,
        total_position: float
    ) -> PortfolioOutput:
        """
        生成组合状态
        """
        total_market_value = sum(p.market_value for p in positions)
        total_profit_loss = sum(p.profit_loss for p in positions)

        return PortfolioOutput(
            date=datetime.now(),
            total_position=total_position,
            positions=positions,
            total_market_value=total_market_value,
            total_profit_loss=total_profit_loss,
            daily_return=0.0,
            risk_adjusted_return=0.0
        )

    def backtest_strategy(
        self,
        quant_results: List[QuantResult],
        initial_capital: float = 100000.0
    ) -> Dict:
        """
        回测策略表现

        Args:
            quant_results: 历史量化结果列表
            initial_capital: 初始资金

        Returns:
            Dict: 回测结果
        """
        logger.info(f"📊 开始回测，共 {len(quant_results)} 个数据点")

        capital = initial_capital
        position = 0.0
        shares = 0
        trades = []

        for i, qr in enumerate(quant_results):
            strategy = self.position_manager.calculate_target_position(qr)

            # 简单的买入/卖出逻辑
            if strategy.action == "买入" and position < strategy.target_position:
                # 买入
                target_shares = int(capital * strategy.target_position / qr.factors.raw_data.get('close', 0))
                if target_shares > 0 and shares == 0:
                    shares = target_shares
                    position = strategy.target_position
                    trades.append({
                        "date": qr.date,
                        "action": "买入",
                        "price": qr.factors.raw_data.get('close', 0),
                        "shares": shares
                    })

            elif strategy.action == "减仓" and position > strategy.target_position:
                # 卖出
                sell_ratio = position - strategy.target_position
                sell_shares = int(shares * sell_ratio / position)
                if sell_shares > 0:
                    shares -= sell_shares
                    position = strategy.target_position
                    trades.append({
                        "date": qr.date,
                        "action": "卖出",
                        "price": qr.factors.raw_data.get('close', 0),
                        "shares": sell_shares
                    })

        # 计算最终收益
        final_capital = capital + shares * (quant_results[-1].factors.raw_data.get('close', 0) if quant_results else 0)
        total_return = (final_capital - initial_capital) / initial_capital * 100

        return {
            "initial_capital": initial_capital,
            "final_capital": final_capital,
            "total_return": total_return,
            "total_trades": len(trades),
            "trades": trades
        }
