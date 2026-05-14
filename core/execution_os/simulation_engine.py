"""
模拟交易引擎 - SimulationEngine

职责：
- 接收交易指令
- 执行模拟交易
- 生成执行报告
- 管理模拟时间

核心流程：
1. 接收 StrategyOS 的交易指令（买入/持有/减仓/清仓）
2. 根据指令创建订单
3. 执行订单（模拟成交）
4. 更新持仓
5. 生成执行报告
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from core.execution_os.models import (
    ExecutionReport, Order, TradeRecord, Account
)
from core.execution_os.order_manager import OrderManager
from core.execution_os.position_tracker import PositionTracker

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    模拟交易引擎

    使用示例：
    ```python
    engine = SimulationEngine(initial_capital=100000)

    # 买入信号
    result = engine.execute_buy("000002", 1000, current_price=10.5)

    # 卖出信号
    result = engine.execute_sell("000002", 500, current_price=11.0)

    # 获取账户状态
    account = engine.get_account()
    positions = engine.get_positions()
    ```
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.order_manager = OrderManager()
        self.position_tracker = PositionTracker(initial_capital)
        self.initial_capital = initial_capital

    def execute_buy(
        self,
        code: str,
        quantity: int,
        current_price: float,
        name: str = "",
        order_type: str = "市价"
    ) -> Dict:
        """
        执行买入

        Args:
            code: 股票代码
            quantity: 买入数量
            current_price: 当前价格
            name: 股票名称
            order_type: 订单类型（市价/限价）

        Returns:
            Dict: 执行结果
        """
        logger.info(f"📈 买入信号: {code} x {quantity}股 @{current_price}")

        # 检查资金是否足够
        estimated_cost = current_price * quantity * 1.002  # 包含手续费估算
        account = self.position_tracker.get_account()

        if account.cash < estimated_cost:
            # 资金不足，按最大可买量计算
            max_quantity = int(account.cash / (current_price * 1.002))
            if max_quantity < 100:
                logger.warning(f"⚠️ 资金不足，无法买入 {code}")
                return {
                    "success": False,
                    "message": f"资金不足：需要 {estimated_cost:.2f}，可用 {account.cash:.2f}",
                    "order": None,
                    "trade": None
                }
            quantity = max_quantity
            logger.warning(f"⚠️ 资金不足，调整买入数量为 {quantity}")

        # 创建订单
        if order_type == "限价":
            order = self.order_manager.create_limit_order(code, "买入", current_price, quantity)
        else:
            order = self.order_manager.create_market_order(code, "买入", quantity, current_price)

        # 执行订单
        exec_result = self.order_manager.execute_order(order, current_price, name)

        if exec_result.success:
            # 更新持仓
            trade = TradeRecord(
                trade_id=f"TR{len(self.order_manager.trade_history)}",
                code=code,
                name=name,
                side="买入",
                price=exec_result.filled_price,
                quantity=exec_result.filled_quantity,
                amount=exec_result.filled_price * exec_result.filled_quantity,
                commission=exec_result.commission,
                traded_at=exec_result.filled_at,
                order_id=order.order_id
            )
            self.position_tracker.update_position_from_trade(trade, current_price)

            logger.info(
                f"✅ 买入成功: {code} {exec_result.filled_quantity}股 @ {exec_result.filled_price:.2f}"
            )

            return {
                "success": True,
                "message": f"买入成功 {exec_result.filled_quantity}股",
                "order": order,
                "trade": trade,
                "execution": exec_result
            }
        else:
            return {
                "success": False,
                "message": exec_result.message,
                "order": order,
                "trade": None,
                "execution": exec_result
            }

    def execute_sell(
        self,
        code: str,
        quantity: int,
        current_price: float,
        name: str = "",
        order_type: str = "市价"
    ) -> Dict:
        """
        执行卖出

        Args:
            code: 股票代码
            quantity: 卖出数量
            current_price: 当前价格
            name: 股票名称
            order_type: 订单类型

        Returns:
            Dict: 执行结果
        """
        logger.info(f"📉 卖出信号: {code} x {quantity}股 @{current_price}")

        # 检查持仓
        position = self.position_tracker.get_position(code)
        if not position:
            logger.warning(f"⚠️ 没有持仓，无法卖出 {code}")
            return {
                "success": False,
                "message": f"没有持仓 {code}",
                "order": None,
                "trade": None
            }

        # 调整卖出数量（不能超过持仓）
        if quantity > position.shares:
            quantity = position.shares
            logger.warning(f"⚠️ 卖出数量超过持仓，调整为 {quantity}")

        # 创建订单
        if order_type == "限价":
            order = self.order_manager.create_limit_order(code, "卖出", current_price, quantity)
        else:
            order = self.order_manager.create_market_order(code, "卖出", quantity, current_price)

        # 执行订单
        exec_result = self.order_manager.execute_order(order, current_price, name)

        if exec_result.success:
            # 更新持仓
            trade = TradeRecord(
                trade_id=f"TR{len(self.order_manager.trade_history)}",
                code=code,
                name=name,
                side="卖出",
                price=exec_result.filled_price,
                quantity=exec_result.filled_quantity,
                amount=exec_result.filled_price * exec_result.filled_quantity,
                commission=exec_result.commission,
                traded_at=exec_result.filled_at,
                order_id=order.order_id
            )
            self.position_tracker.update_position_from_trade(trade, current_price)

            logger.info(
                f"✅ 卖出成功: {code} {exec_result.filled_quantity}股 @ {exec_result.filled_price:.2f}"
            )

            return {
                "success": True,
                "message": f"卖出成功 {exec_result.filled_quantity}股",
                "order": order,
                "trade": trade,
                "execution": exec_result
            }
        else:
            return {
                "success": False,
                "message": exec_result.message,
                "order": order,
                "trade": None,
                "execution": exec_result
            }

    def adjust_position(
        self,
        code: str,
        target_ratio: float,
        current_price: float,
        name: str = ""
    ) -> Dict:
        """
        根据目标仓位调整持仓

        Args:
            code: 股票代码
            target_ratio: 目标仓位比例（0-1）
            current_price: 当前价格
            name: 股票名称

        Returns:
            Dict: 执行结果
        """
        account = self.position_tracker.get_account()
        current_ratio = self.position_tracker.get_total_position_ratio()
        position = self.position_tracker.get_position(code)

        current_position_value = position.market_value if position else 0
        target_position_value = account.total_assets * target_ratio
        diff_value = target_position_value - current_position_value

        logger.info(
            f"📊 仓位调整: {code} "
            f"当前 {current_position_value:.2f} -> 目标 {target_position_value:.2f} "
            f"(差 {diff_value:+.2f})"
        )

        if diff_value > 100:  # 差异大于100元，买入
            quantity = int(diff_value / current_price / 100) * 100  # 按手计算
            if quantity > 0:
                return self.execute_buy(code, quantity, current_price, name)
            else:
                return {"success": True, "message": "买入数量为0", "order": None, "trade": None}

        elif diff_value < -100:  # 差异大于100元，卖出
            quantity = int(-diff_value / current_price / 100) * 100
            if quantity > 0 and position:
                return self.execute_sell(code, quantity, current_price, name)
            else:
                return {"success": True, "message": "卖出数量为0", "order": None, "trade": None}

        else:
            return {"success": True, "message": "仓位无需调整", "order": None, "trade": None}

    def get_account(self) -> Account:
        """获取账户信息"""
        return self.position_tracker.get_account()

    def get_positions(self) -> List:
        """获取所有持仓"""
        return self.position_tracker.get_all_positions()

    def get_position(self, code: str):
        """获取指定持仓"""
        return self.position_tracker.get_position(code)

    def get_today_trades(self) -> List[TradeRecord]:
        """获取今日交易记录"""
        return self.order_manager.get_today_trades()

    def get_pending_orders(self) -> List[Order]:
        """获取待成交订单"""
        return self.order_manager.get_pending_orders()

    def generate_report(self) -> ExecutionReport:
        """
        生成执行报告

        Returns:
            ExecutionReport: 执行报告
        """
        account = self.position_tracker.get_account()
        positions = self.position_tracker.get_all_positions()
        today_trades = self.order_manager.get_today_trades()

        # 计算今日盈亏（简化版：使用持仓盈亏变化）
        daily_pnl = sum(p.today_profit_loss for p in positions)

        report = ExecutionReport(
            date=datetime.now(),
            orders=self.order_manager.get_pending_orders(),
            trades=today_trades,
            positions=positions,
            account=account,
            daily_pnl=daily_pnl,
            daily_return=daily_pnl / self.initial_capital * 100 if self.initial_capital > 0 else 0,
            success_count=len([o for o in self.order_manager.filled_orders.values() if o.created_at.date() == datetime.now().date()]),
            fail_count=0,
            message="执行完成"
        )

        return report

    def reset(self):
        """重置模拟账户"""
        self.order_manager = OrderManager()
        self.position_tracker.reset()
        logger.info("🔄 模拟账户已重置")
