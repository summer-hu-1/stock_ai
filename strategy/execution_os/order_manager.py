"""
订单管理器 - OrderManager

职责：
- 创建订单
- 执行订单（模拟成交）
- 撤单管理
- 订单历史

核心逻辑：
1. 市价单：立即以当前价成交（模拟）
2. 限价单：检查价格是否满足，满足则成交
3. 成交时计算手续费和滑点
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid
import logging

from .models import (
    Order, OrderType, OrderSide, OrderStatus,
    ExecutionResult, TradeRecord
)

logger = logging.getLogger(__name__)


class OrderManager:
    """
    订单管理器

    模拟交易规则：
    - 手续费：万分之3（单边）
    - 印花税：千分之1（仅卖出）
    - 滑点：千分之1
    """

    COMMISSION_RATE = 0.0003  # 手续费万3
    STAMP_TAX_RATE = 0.001    # 印花税千1（仅卖出）
    SLIPPAGE_RATE = 0.001      # 滑点千1

    def __init__(self):
        self.pending_orders: Dict[str, Order] = {}
        self.filled_orders: Dict[str, Order] = {}
        self.cancelled_orders: Dict[str, Order] = {}
        self.trade_history: List[TradeRecord] = []
        self.order_counter = 0

    def create_market_order(
        self,
        code: str,
        side: str,
        quantity: int,
        current_price: float
    ) -> Order:
        """
        创建市价单

        Args:
            code: 股票代码
            side: 买入/卖出
            quantity: 数量
            current_price: 当前价格

        Returns:
            Order: 创建的订单
        """
        self.order_counter += 1
        order_id = f"MKT{self.order_counter:06d}{int(datetime.now().timestamp())}"

        order = Order(
            order_id=order_id,
            code=code,
            side=side,
            order_type="市价",
            price=current_price,
            quantity=quantity,
            status="待成交"
        )

        self.pending_orders[order_id] = order
        logger.info(f"📝 创建市价单: {order_id} {side} {code} {quantity}股 @{current_price}")

        return order

    def create_limit_order(
        self,
        code: str,
        side: str,
        price: float,
        quantity: int
    ) -> Order:
        """
        创建限价单

        Args:
            code: 股票代码
            side: 买入/卖出
            price: 限价
            quantity: 数量

        Returns:
            Order: 创建的订单
        """
        self.order_counter += 1
        order_id = f"LMT{self.order_counter:06d}{int(datetime.now().timestamp())}"

        order = Order(
            order_id=order_id,
            code=code,
            side=side,
            order_type="限价",
            price=price,
            quantity=quantity,
            status="待成交"
        )

        self.pending_orders[order_id] = order
        logger.info(f"📝 创建限价单: {order_id} {side} {code} {quantity}股 @{price}")

        return order

    def execute_order(
        self,
        order: Order,
        current_price: float,
        name: str = ""
    ) -> ExecutionResult:
        """
        执行订单（模拟成交）

        Args:
            order: 订单
            current_price: 当前价格
            name: 股票名称

        Returns:
            ExecutionResult: 执行结果
        """
        # 市价单以当前价成交
        if order.order_type == "市价":
            filled_price = current_price
        else:
            # 限价单：买入时价格必须<=限价，卖出时价格必须>=限价
            if order.side == "买入" and current_price > order.price:
                return ExecutionResult(
                    order_id=order.order_id,
                    success=False,
                    filled_price=0,
                    filled_quantity=0,
                    filled_at=datetime.now(),
                    commission=0,
                    message=f"价格不满足：当前价{current_price} > 限价{order.price}"
                )
            elif order.side == "卖出" and current_price < order.price:
                return ExecutionResult(
                    order_id=order.order_id,
                    success=False,
                    filled_price=0,
                    filled_quantity=0,
                    filled_at=datetime.now(),
                    commission=0,
                    message=f"价格不满足：当前价{current_price} < 限价{order.price}"
                )
            filled_price = current_price

        # 计算滑点
        slippage = filled_price * self.SLIPPAGE_RATE
        if order.side == "买入":
            filled_price_with_slippage = filled_price * (1 + self.SLIPPAGE_RATE)
        else:
            filled_price_with_slippage = filled_price * (1 - self.SLIPPAGE_RATE)

        # 计算手续费
        amount = filled_price_with_slippage * order.quantity
        commission = amount * self.COMMISSION_RATE

        # 卖出时加印花税
        if order.side == "卖出":
            commission += amount * self.STAMP_TAX_RATE

        # 更新订单状态
        order.filled_quantity = order.quantity
        order.status = "已成交"
        order.filled_at = datetime.now()
        order.updated_at = datetime.now()
        order.commission = commission

        # 移动到已完成
        self.pending_orders.pop(order.order_id, None)
        self.filled_orders[order.order_id] = order

        # 添加交易记录
        trade_record = TradeRecord(
            trade_id=f"TR{len(self.trade_history) + 1:08d}",
            code=order.code,
            name=name,
            side=order.side,
            price=filled_price_with_slippage,
            quantity=order.quantity,
            amount=filled_price_with_slippage * order.quantity,
            commission=commission,
            traded_at=datetime.now(),
            order_id=order.order_id
        )
        self.trade_history.append(trade_record)

        logger.info(
            f"✅ 成交: {order.order_id} {order.side} {order.code} "
            f"{order.quantity}股 @{filled_price_with_slippage:.2f} "
            f"手续费 {commission:.2f}"
        )

        return ExecutionResult(
            order_id=order.order_id,
            success=True,
            filled_price=filled_price_with_slippage,
            filled_quantity=order.quantity,
            filled_at=datetime.now(),
            commission=commission,
            slippage=slippage
        )

    def cancel_order(self, order_id: str) -> bool:
        """
        撤销订单

        Args:
            order_id: 订单ID

        Returns:
            bool: 是否成功撤销
        """
        order = self.pending_orders.get(order_id)
        if not order:
            logger.warning(f"⚠️ 订单不存在或已成交: {order_id}")
            return False

        order.status = "已撤销"
        order.updated_at = datetime.now()

        self.pending_orders.pop(order_id, None)
        self.cancelled_orders[order_id] = order

        logger.info(f"🚫 撤销订单: {order_id}")
        return True

    def get_pending_orders(self) -> List[Order]:
        """获取待成交订单"""
        return list(self.pending_orders.values())

    def get_filled_orders(self) -> List[Order]:
        """获取已成交订单"""
        return list(self.filled_orders.values())

    def get_today_trades(self) -> List[TradeRecord]:
        """获取今日交易记录"""
        today = datetime.now().date()
        return [
            t for t in self.trade_history
            if t.traded_at.date() == today
        ]

    def get_trade_history(self, days: int = 30) -> List[TradeRecord]:
        """
        获取交易历史

        Args:
            days: 获取最近N天的记录

        Returns:
            List[TradeRecord]: 交易记录列表
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        return [
            t for t in self.trade_history
            if t.traded_at >= cutoff
        ]

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        return (
            self.pending_orders.get(order_id) or
            self.filled_orders.get(order_id) or
            self.cancelled_orders.get(order_id)
        )
