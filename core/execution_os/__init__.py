"""
Core ExecutionOS - 向后兼容模块

V10.1 已将 ExecutionOS 移至 strategy.execution_os
此模块保留用于向后兼容
"""

from strategy.execution_os import ExecutionOS, get_execution_os
from strategy.execution_os.models import Account, Position
from strategy.execution_os.simulation_engine import SimulationEngine
from strategy.execution_os.order_manager import OrderManager
from strategy.execution_os.position_tracker import PositionTracker

__all__ = [
    "ExecutionOS",
    "get_execution_os",
    "Account",
    "Position",
    "SimulationEngine",
    "OrderManager",
    "PositionTracker",
]
