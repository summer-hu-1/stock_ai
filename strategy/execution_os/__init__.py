"""
ExecutionOS - 执行层

V10 架构：负责订单执行、持仓同步、模拟交易

核心入口：
- get_execution_os(): 获取单例

使用示例：
```python
from strategy.execution_os import get_execution_os

execution_os = get_execution_os()

# 执行买入
result = execution_os.execute_buy("000002", 1000, 10.5)

# 执行卖出
result = execution_os.execute_sell("000002", 500, 11.0)

# 根据策略执行
result = execution_os.execute_from_strategy(
    strategy_decision,  # StrategyOS 的决策结果
    current_price=10.5
)

# 获取账户状态
account = execution_os.get_account()
positions = execution_os.get_positions()
```
"""

from typing import Optional, Dict
import logging

from .simulation_engine import SimulationEngine
from .models import Account, Position

logger = logging.getLogger(__name__)


class ExecutionOS:
    """
    ExecutionOS - 执行层统一入口

    职责：
    1. 接收交易指令并执行
    2. 管理模拟交易账户
    3. 生成执行报告
    """

    def __init__(self, initial_capital: float = 100000.0):
        logger.info("🔧 初始化 ExecutionOS...")
        self.simulation_engine = SimulationEngine(initial_capital)
        self.initial_capital = initial_capital
        logger.info(f"✅ ExecutionOS 初始化完成（初始资金: {initial_capital}）")

    def execute_buy(
        self,
        code: str,
        quantity: int,
        current_price: float,
        name: str = ""
    ) -> Dict:
        """
        执行买入

        Args:
            code: 股票代码
            quantity: 买入数量（股）
            current_price: 当前价格
            name: 股票名称

        Returns:
            Dict: 执行结果
        """
        return self.simulation_engine.execute_buy(
            code, quantity, current_price, name
        )

    def execute_sell(
        self,
        code: str,
        quantity: int,
        current_price: float,
        name: str = ""
    ) -> Dict:
        """
        执行卖出

        Args:
            code: 股票代码
            quantity: 卖出数量（股）
            current_price: 当前价格
            name: 股票名称

        Returns:
            Dict: 执行结果
        """
        return self.simulation_engine.execute_sell(
            code, quantity, current_price, name
        )

    def execute_from_strategy(
        self,
        strategy_decision: Dict,
        current_price: float,
        name: str = ""
    ) -> Dict:
        """
        根据策略决策执行交易

        Args:
            strategy_decision: StrategyOS 的决策结果
            current_price: 当前价格
            name: 股票名称

        Returns:
            Dict: 执行结果
        """
        code = strategy_decision.get("stock_code", strategy_decision.get("code", ""))
        action = strategy_decision.get("final_decision", {}).get("action", "持有")
        target_position = strategy_decision.get("final_decision", {}).get("target_position", 0)
        quant_result = strategy_decision.get("quant_result")

        if not code:
            return {
                "success": False,
                "message": "缺少股票代码",
                "order": None,
                "trade": None
            }

        logger.info(f"🎯 ExecutionOS 执行策略: {code} {action} (目标仓位 {target_position*100:.0f}%)")

        current_position = self.simulation_engine.get_position(code)
        account = self.simulation_engine.get_account()

        if action == "买入":
            target_value = account.total_assets * target_position
            current_value = current_position.market_value if current_position else 0
            need_value = target_value - current_value

            if need_value > 0:
                quantity = int(need_value / current_price / 100) * 100
                if quantity >= 100:
                    return self.execute_buy(code, quantity, current_price, name)

            return {
                "success": True,
                "message": "无需买入",
                "order": None,
                "trade": None
            }

        elif action == "卖出":
            if current_position and current_position.shares > 0:
                target_value = account.total_assets * target_position
                current_value = current_position.market_value
                need_sell_value = current_value - target_value

                if need_sell_value > 0:
                    quantity = int(need_sell_value / current_price / 100) * 100
                    if quantity >= 100:
                        return self.execute_sell(code, quantity, current_price, name)

            return {
                "success": True,
                "message": "无需卖出",
                "order": None,
                "trade": None
            }

        elif action == "清仓":
            if current_position and current_position.shares > 0:
                return self.execute_sell(
                    code,
                    current_position.shares,
                    current_price,
                    name
                )

            return {
                "success": True,
                "message": "无需清仓",
                "order": None,
                "trade": None
            }

        else:
            return {
                "success": True,
                "message": "持有",
                "order": None,
                "trade": None
            }

    def get_account(self) -> Account:
        """获取账户信息"""
        return self.simulation_engine.get_account()

    def get_positions(self) -> list:
        """获取所有持仓"""
        return self.simulation_engine.get_positions()

    def get_position(self, code: str) -> Optional[Position]:
        """获取指定持仓"""
        return self.simulation_engine.get_position(code)

    def get_today_trades(self) -> list:
        """获取今日交易记录"""
        return self.simulation_engine.get_today_trades()

    def get_pending_orders(self) -> list:
        """获取待成交订单"""
        return self.simulation_engine.get_pending_orders()

    def generate_report(self):
        """生成执行报告"""
        return self.simulation_engine.generate_report()

    def update_prices(self, price_map: Dict[str, float]):
        """
        批量更新持仓价格

        Args:
            price_map: {code: current_price}
        """
        self.simulation_engine.position_tracker.update_prices(price_map)

    def reset(self):
        """重置模拟账户"""
        self.simulation_engine.reset()
        logger.info("🔄 ExecutionOS 已重置")


_execution_os_instance: Optional[ExecutionOS] = None


def get_execution_os(initial_capital: float = 100000.0) -> ExecutionOS:
    """
    获取 ExecutionOS 单例

    Args:
        initial_capital: 初始资金（仅第一次有效）

    Returns:
        ExecutionOS: 执行层实例
    """
    global _execution_os_instance
    if _execution_os_instance is None:
        _execution_os_instance = ExecutionOS(initial_capital)
    return _execution_os_instance
