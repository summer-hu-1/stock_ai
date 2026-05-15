"""
持仓同步器 - PositionTracker

职责：
- 同步持仓信息
- 计算浮动盈亏
- 更新持仓成本
- 追踪持仓状态

核心逻辑：
1. 买入成交时，增加持仓
2. 卖出成交时，减少持仓
3. 每日根据最新价格更新盈亏
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from .models import (
    Position, Account, PositionStatus, TradeRecord
)

logger = logging.getLogger(__name__)


class PositionTracker:
    """
    持仓同步器

    持仓同步规则：
    1. 买入成交：增加持仓（计算新的平均成本）
    2. 卖出成交：减少持仓（计算剩余持仓的平均成本不变）
    3. 每日收盘：根据最新价格更新市值和盈亏
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.positions: Dict[str, Position] = {}  # code -> Position
        self.account = Account(
            cash=initial_capital,
            total_assets=initial_capital,
            initial_capital=initial_capital
        )
        self.initial_capital = initial_capital

    def update_position_from_trade(
        self,
        trade: TradeRecord,
        current_price: float
    ) -> Position:
        """
        根据交易记录更新持仓

        Args:
            trade: 交易记录
            current_price: 当前价格

        Returns:
            Position: 更新后的持仓
        """
        code = trade.code

        if trade.side == "买入":
            return self._add_position(trade, current_price)
        else:
            return self._reduce_position(trade, current_price)

    def _add_position(
        self,
        trade: TradeRecord,
        current_price: float
    ) -> Position:
        """
        增加持仓（买入）

        平均成本 = (原持仓成本 + 新买入金额) / 总股数
        """
        code = trade.code

        if code not in self.positions:
            # 新建持仓
            position = Position(
                code=code,
                name=trade.name,
                shares=trade.quantity,
                avg_cost=trade.price,
                current_price=current_price,
                market_value=trade.price * trade.quantity,
                profit_loss=0,
                profit_loss_pct=0,
                today_buy_quantity=trade.quantity,
                status="持仓中",
                opened_at=datetime.now()
            )
            self.positions[code] = position
        else:
            # 追加持仓
            position = self.positions[code]
            old_shares = position.shares
            old_cost = position.avg_cost * old_shares
            new_cost = trade.price * trade.quantity

            total_shares = old_shares + trade.quantity
            total_cost = old_cost + new_cost
            new_avg_cost = total_cost / total_shares

            position.shares = total_shares
            position.avg_cost = new_avg_cost
            position.current_price = current_price
            position.market_value = current_price * total_shares
            position.today_buy_quantity += trade.quantity

            # 更新账户资金
            self.account.cash -= (new_cost + trade.commission)

        self._update_position_profit_loss(position, current_price)
        self._update_account()

        logger.info(
            f"📈 买入 {code} {trade.quantity}股 @ {trade.price:.2f}, "
            f"持仓: {position.shares}股, 均价: {position.avg_cost:.2f}"
        )

        return position

    def _reduce_position(
        self,
        trade: TradeRecord,
        current_price: float
    ) -> Position:
        """
        减少持仓（卖出）

        卖出后剩余股数的平均成本不变
        """
        code = trade.code

        if code not in self.positions:
            logger.warning(f"⚠️ 尝试卖出不存在的持仓: {code}")
            return None

        position = self.positions[code]

        # 卖出
        sell_amount = trade.price * trade.quantity
        position.shares -= trade.quantity
        position.today_sell_quantity += trade.quantity

        # 更新账户资金（扣除手续费）
        self.account.cash += (sell_amount - trade.commission)

        # 检查是否完全卖出
        if position.shares == 0:
            position.status = "已平仓"
            position.market_value = 0
            del self.positions[code]
            logger.info(f"📤 卖出 {code} {trade.quantity}股 @ {trade.price:.2f}, 已完全平仓")
        else:
            self._update_position_profit_loss(position, current_price)
            logger.info(
                f"📤 卖出 {code} {trade.quantity}股 @ {trade.price:.2f}, "
                f"剩余: {position.shares}股"
            )

        self._update_account()

        return position

    def update_prices(self, price_map: Dict[str, float]):
        """
        批量更新持仓价格

        Args:
            price_map: {code: current_price}
        """
        for code, price in price_map.items():
            if code in self.positions:
                position = self.positions[code]
                position.current_price = price
                self._update_position_profit_loss(position, price)

        self._update_account()

    def _update_position_profit_loss(
        self,
        position: Position,
        current_price: float
    ):
        """更新持仓盈亏"""
        position.current_price = current_price
        position.market_value = current_price * position.shares
        position.profit_loss = (current_price - position.avg_cost) * position.shares
        position.profit_loss_pct = (
            (current_price - position.avg_cost) / position.avg_cost * 100
            if position.avg_cost > 0 else 0
        )

    def _update_account(self):
        """更新账户信息"""
        # 计算总市值
        self.account.market_value = sum(
            p.market_value for p in self.positions.values()
        )

        # 总资产 = 现金 + 市值
        self.account.total_assets = self.account.cash + self.account.market_value

        # 累计盈亏
        self.account.profit_loss = self.account.total_assets - self.initial_capital
        self.account.profit_loss_pct = (
            self.account.profit_loss / self.initial_capital * 100
        )

        # 累计手续费（从交易记录中计算，这里简化处理）
        # self.account.commission 已有的不重复计算

    def get_position(self, code: str) -> Optional[Position]:
        """获取指定持仓"""
        return self.positions.get(code)

    def get_all_positions(self) -> List[Position]:
        """获取所有持仓"""
        return list(self.positions.values())

    def get_account(self) -> Account:
        """获取账户信息"""
        return self.account

    def get_total_position_ratio(self) -> float:
        """获取总仓位比例"""
        return self.account.market_value / self.account.total_assets if self.account.total_assets > 0 else 0

    def reset(self):
        """重置账户（用于新模拟）"""
        self.positions.clear()
        self.account = Account(
            cash=self.initial_capital,
            total_assets=self.initial_capital,
            initial_capital=self.initial_capital
        )
        logger.info(f"🔄 账户已重置，初始资金: {self.initial_capital}")
