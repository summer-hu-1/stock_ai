"""
StrategyOS - 策略中台

V10 架构：负责策略调度、仓位管理、风险控制

核心入口：
- get_strategy_os(): 获取单例

使用示例：
```python
from core.strategy_os import get_strategy_os

strategy_os = get_strategy_os()

# 生成交易决策
decision = strategy_os.generate_trade_decision(quant_result)

print(f"操作: {decision['final_decision']['action']}")
print(f"目标仓位: {decision['final_decision']['target_position']*100:.0f}%")
```
"""

from typing import Optional
import logging

from core.strategy_os.strategy_engine import StrategyEngine
from core.quant_core.models import QuantResult

logger = logging.getLogger(__name__)


class StrategyOS:
    """
    StrategyOS - 策略中台统一入口

    职责：
    1. 接收 QuantResult
    2. 生成交易决策
    3. 管理仓位
    4. 控制风险
    """

    def __init__(self):
        logger.info("🔧 初始化 StrategyOS...")
        self.strategy_engine = StrategyEngine()
        logger.info("✅ StrategyOS 初始化完成")

    def generate_trade_decision(
        self,
        quant_result: QuantResult,
        current_positions: Optional[list] = None
    ) -> dict:
        """
        生成交易决策

        Args:
            quant_result: QuantCore 的量化结果
            current_positions: 当前持仓列表（可选）

        Returns:
            dict: 包含 strategy, risk, portfolio, final_decision
        """
        return self.strategy_engine.generate_trade_decision(
            quant_result, current_positions
        )

    def analyze_and_decide(
        self,
        stock_code: str,
        market: str = "cn"
    ) -> dict:
        """
        完整分析+决策流程

        内部调用 QuantCore + StrategyOS

        Args:
            stock_code: 股票代码
            market: 市场

        Returns:
            dict: 完整的分析和决策结果
        """
        from core.quant_core import get_quant_core

        logger.info(f"🎯 StrategyOS 完整流程: {stock_code}")

        # 1. QuantCore 分析
        quant_core = get_quant_core()
        quant_result = quant_core.analyze(stock_code, market)

        # 2. StrategyOS 决策
        decision = self.generate_trade_decision(quant_result)

        return {
            "success": True,
            "stock_code": stock_code,
            "market": market,
            "quant_result": quant_result,
            "strategy_decision": decision,
            "summary": {
                "final_score": quant_result.score.final_score,
                "signal": quant_result.score.signal,
                "action": decision['final_decision']['action'],
                "target_position": decision['final_decision']['target_position'],
                "confidence": decision['final_decision']['confidence'],
                "warnings": decision['final_decision']['warnings']
            }
        }


_strategy_os_instance: Optional[StrategyOS] = None


def get_strategy_os() -> StrategyOS:
    """
    获取 StrategyOS 单例
    """
    global _strategy_os_instance
    if _strategy_os_instance is None:
        _strategy_os_instance = StrategyOS()
    return _strategy_os_instance
