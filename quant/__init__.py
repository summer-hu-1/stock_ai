"""
QuantCore - 量化核心层

V10.3 架构核心：唯一计算引擎，只做数学计算，不做AI解释

职责：
1. 因子计算（趋势、量能、波动率、强度、动量）
2. 信号生成（突破、反转、主升、放量）
3. 市场状态分析
4. 综合评分
5. 统一流水线调度

使用示例：
```python
from quant import get_quant_core

quant = get_quant_core()

# 综合量化分析
result = quant.analyze("000002", "cn")

# 单独计算因子
factors = quant.calculate_factors(df)

# 生成信号
signals = quant.generate_signals(df, factors)
```

V10.3 新增：
- DailyPipeline: 统一量化流水线
- StockSnapshot: 统一快照对象模型
"""

from .engine import QuantCore, get_quant_core
from .models import QuantResult, FactorResult, SignalResult, ScoreResult, StateResult
from .snapshot_models import (
    StockSnapshot,
    DailyPipelineResult,
    FactorSnapshot,
    SignalSnapshot,
    MarketContextSnapshot,
    LeaderSnapshot,
    StrategySnapshot,
)
from .daily_pipeline import DailyPipeline, get_daily_pipeline, run_daily_pipeline

__all__ = [
    "QuantCore",
    "get_quant_core",
    "QuantResult",
    "FactorResult",
    "SignalResult",
    "ScoreResult",
    "StateResult",
    "StockSnapshot",
    "DailyPipelineResult",
    "FactorSnapshot",
    "SignalSnapshot",
    "MarketContextSnapshot",
    "LeaderSnapshot",
    "StrategySnapshot",
    "DailyPipeline",
    "get_daily_pipeline",
    "run_daily_pipeline",
]
