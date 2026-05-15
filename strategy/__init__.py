"""
StrategyOS - 策略层

V10.1 架构核心：策略调度 + 风控 + 模拟执行

职责：
1. 策略调度
2. 风险控制
3. 模拟执行
4. 仓位管理
"""

from .engine import ExecutionOS, get_execution_os
from .models import (
    Order,
    Position,
    Account,
    TradeRecord,
    ExecutionResult,
)

__all__ = [
    "ExecutionOS",
    "get_execution_os",
    "Order",
    "Position",
    "Account",
    "TradeRecord",
    "ExecutionResult",
]

def get_strategy_os(initial_capital: float = 100000.0) -> ExecutionOS:
    """获取StrategyOS单例（别名）"""
    return get_execution_os(initial_capital)