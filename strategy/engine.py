"""
模拟交易引擎 - ExecutionOS

模拟交易执行
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging

from .models import Order, Position, Account, TradeRecord

logger = logging.getLogger(__name__)


class ExecutionOS:
    """
    ExecutionOS - 模拟交易引擎

    支持：
    - 市价/限价订单
    - 持仓管理
    - 资金管理
    - 手续费/滑点计算
    """

    COMMISSION_RATE = 0.0003
    STAMP_TAX_RATE = 0.001
    SLIPPAGE_RATE = 0.001

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.account = Account(
            cash=initial_capital,
            total_assets=initial_capital,
            initial_capital=initial_capital
        )
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[TradeRecord] = []
        self.order_counter = 0
        logger.info(f"ExecutionOS 初始化完成（初始资金: {initial_capital}）")

    def execute_buy(
        self,
        code: str,
        quantity: int,
        price: float,
        name: str = "",
        order_type: str = "市价"
    ) -> Dict:
        """
        执行买入

        Args:
            code: 股票代码
            quantity: 买入数量
            price: 当前价格
            name: 股票名称
            order_type: 订单类型

        Returns:
            Dict: 执行结果
        """
        self.order_counter += 1
        order_id = f"B{self.order_counter:06d}"

        if quantity < 100:
            return {
                "success": False,
                "order_id": order_id,
                "message": "买入数量必须 >= 100股"
            }

        slippage_price = price * (1 + self.SLIPPAGE_RATE)
        total_cost = slippage_price * quantity
        commission = total_cost * self.COMMISSION_RATE
        total_amount = total_cost + commission

        if total_amount > self.account.cash:
            return {
                "success": False,
                "order_id": order_id,
                "message": f"资金不足（需要 {total_amount:.2f}, 可用 {self.account.cash:.2f}）"
            }

        self.account.cash -= total_amount
        self.account.commission += commission

        trade_id = f"TR{self.order_counter:06d}"
        trade = TradeRecord(
            trade_id=trade_id,
            code=code,
            side="买入",
            price=slippage_price,
            quantity=quantity,
            amount=slippage_price * quantity,
            commission=commission,
            traded_at=datetime.now()
        )
        self.trades.append(trade)

        self._update_position(code, name, "买入", slippage_price, quantity)

        return {
            "success": True,
            "order_id": order_id,
            "trade_id": trade_id,
            "message": f"买入成功",
            "price": slippage_price,
            "quantity": quantity,
            "commission": commission
        }

    def execute_sell(
        self,
        code: str,
        quantity: int,
        price: float,
        name: str = "",
        order_type: str = "市价"
    ) -> Dict:
        """
        执行卖出

        Args:
            code: 股票代码
            quantity: 卖出数量
            price: 当前价格
            name: 股票名称
            order_type: 订单类型

        Returns:
            Dict: 执行结果
        """
        position = self.positions.get(code)
        if position is None or position.shares < quantity:
            available = position.shares if position else 0
            return {
                "success": False,
                "order_id": None,
                "message": f"持仓不足（可卖 {available}股, 计划卖 {quantity}股）"
            }

        self.order_counter += 1
        order_id = f"S{self.order_counter:06d}"

        slippage_price = price * (1 - self.SLIPPAGE_RATE)
        total_amount = slippage_price * quantity
        commission = total_amount * self.COMMISSION_RATE
        stamp_tax = total_amount * self.STAMP_TAX_RATE
        total_proceeds = total_amount - commission - stamp_tax

        self.account.cash += total_proceeds
        self.account.commission += commission + stamp_tax

        trade_id = f"TR{self.order_counter:06d}"
        trade = TradeRecord(
            trade_id=trade_id,
            code=code,
            side="卖出",
            price=slippage_price,
            quantity=quantity,
            amount=total_amount,
            commission=commission + stamp_tax,
            traded_at=datetime.now()
        )
        self.trades.append(trade)

        self._update_position(code, name, "卖出", slippage_price, quantity)

        return {
            "success": True,
            "order_id": order_id,
            "trade_id": trade_id,
            "message": f"卖出成功",
            "price": slippage_price,
            "quantity": quantity,
            "commission": commission + stamp_tax
        }

    def _update_position(
        self,
        code: str,
        name: str,
        side: str,
        price: float,
        quantity: int
    ):
        """更新持仓"""
        if code not in self.positions:
            self.positions[code] = Position(code=code, name=name)

        position = self.positions[code]

        if side == "买入":
            total_cost = position.avg_cost * position.shares + price * quantity
            position.shares += quantity
            position.avg_cost = total_cost / position.shares
            position.name = name
        else:
            position.shares -= quantity
            if position.shares == 0:
                position.avg_cost = 0.0

        position.current_price = price
        position.market_value = position.shares * price
        position.profit_loss = (price - position.avg_cost) * position.shares
        position.profit_loss_pct = (
            (price - position.avg_cost) / position.avg_cost * 100
            if position.avg_cost > 0 else 0
        )

        self._update_account()

    def _update_account(self):
        """更新账户"""
        self.account.market_value = sum(p.market_value for p in self.positions.values())
        self.account.total_assets = self.account.cash + self.account.market_value
        self.account.profit_loss = self.account.total_assets - self.account.initial_capital
        self.account.profit_loss_pct = (
            self.account.profit_loss / self.account.initial_capital * 100
        )

    def get_account(self) -> Account:
        """获取账户信息"""
        return self.account

    def get_positions(self) -> List[Position]:
        """获取所有持仓"""
        return [p for p in self.positions.values() if p.shares > 0]

    def get_position(self, code: str) -> Optional[Position]:
        """获取指定持仓"""
        return self.positions.get(code)

    def get_trades(self) -> List[TradeRecord]:
        """获取交易记录"""
        return self.trades


_execution_os_instance: Optional[ExecutionOS] = None


def get_execution_os(initial_capital: float = 100000.0) -> ExecutionOS:
    """获取ExecutionOS单例"""
    global _execution_os_instance
    if _execution_os_instance is None:
        _execution_os_instance = ExecutionOS(initial_capital)
    return _execution_os_instance
