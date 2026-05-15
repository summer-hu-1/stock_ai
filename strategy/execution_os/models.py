"""
ExecutionOS - 执行层

V10 架构：负责订单执行、持仓同步、模拟交易

核心职责：
- 模拟交易执行（不连接真实券商）
- 订单管理（下单/撤单）
- 持仓同步
- 成交记录
- 资金管理

⚠️ 注意：
- 当前版本仅支持模拟交易
- 实盘对接需要额外开发券商接口

核心流程：
1. StrategyOS 生成交易指令（买入/持有/减仓/清仓）
2. ExecutionOS 接收指令，创建订单
3. 订单管理器执行订单（模拟成交）
4. 持仓同步器更新持仓
5. 生成执行报告
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class OrderType(Enum):
    """订单类型"""
    MARKET = "市价"      # 市价单
    LIMIT = "限价"      # 限价单


class OrderSide(Enum):
    """订单方向"""
    BUY = "买入"
    SELL = "卖出"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "待成交"    # 等待成交
    FILLED = "已成交"     # 完全成交
    PARTIAL = "部分成交"  # 部分成交
    CANCELLED = "已撤销"  # 已撤销
    REJECTED = "已拒绝"   # 拒绝


class PositionStatus(Enum):
    """持仓状态"""
    OPEN = "持仓中"
    CLOSED = "已平仓"
    PENDING = "待买入"


@dataclass
class Order:
    """订单信息"""
    order_id: str
    code: str
    side: str  # 买入/卖出
    order_type: str  # 市价/限价
    price: float  # 限价单价
    quantity: int  # 数量（股）
    filled_quantity: int = 0  # 已成交数量
    status: str = "待成交"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    commission: float = 0.0  # 手续费


@dataclass
class ExecutionResult:
    """订单执行结果"""
    order_id: str
    success: bool
    filled_price: float
    filled_quantity: int
    filled_at: datetime
    commission: float
    slippage: float = 0.0  # 滑点
    message: str = ""


@dataclass
class Position:
    """持仓信息"""
    code: str
    name: str = ""
    shares: int = 0
    avg_cost: float = 0.0  # 平均成本
    current_price: float = 0.0
    market_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    today_profit_loss: float = 0.0
    today_buy_quantity: int = 0
    today_sell_quantity: int = 0
    status: str = "持仓中"
    opened_at: Optional[datetime] = None


@dataclass
class Account:
    """账户信息"""
    cash: float = 100000.0  # 可用资金
    market_value: float = 0.0  # 市值
    total_assets: float = 100000.0  # 总资产
    frozen: float = 0.0  # 冻结资金
    commission: float = 0.0  # 累计手续费
    profit_loss: float = 0.0  # 累计盈亏
    profit_loss_pct: float = 0.0  # 累计收益率
    initial_capital: float = 100000.0  # 初始资金


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str
    code: str
    side: str  # 买入/卖出
    price: float
    quantity: int
    amount: float  # 成交金额
    commission: float
    traded_at: datetime
    name: str = ""
    order_id: str = ""


@dataclass
class ExecutionReport:
    """执行报告"""
    date: datetime
    orders: List[Order] = field(default_factory=list)
    trades: List[TradeRecord] = field(default_factory=list)
    positions: List[Position] = field(default_factory=list)
    account: Optional[Account] = None
    daily_pnl: float = 0.0
    daily_return: float = 0.0
    success_count: int = 0
    fail_count: int = 0
    message: str = ""
