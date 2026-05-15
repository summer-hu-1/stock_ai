"""
执行层数据模型
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Order:
    """订单"""
    order_id: str
    code: str
    side: str
    order_type: str
    price: float
    quantity: int
    filled_quantity: int = 0
    status: str = "待成交"
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    commission: float = 0.0


@dataclass
class Position:
    """持仓"""
    code: str
    name: str = ""
    shares: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0


@dataclass
class Account:
    """账户"""
    cash: float = 100000.0
    market_value: float = 0.0
    total_assets: float = 100000.0
    frozen: float = 0.0
    commission: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    initial_capital: float = 100000.0


@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str
    code: str
    side: str
    price: float
    quantity: int
    amount: float
    commission: float
    traded_at: datetime


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    order_id: str
    trade_id: str = ""
    message: str = ""
