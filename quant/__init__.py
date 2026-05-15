"""
QuantCore - 量化核心层

V10 架构核心：唯一计算引擎，只做数学计算，不做AI解释

职责：
1. 因子计算（趋势、量能、波动率、强度、动量）
2. 信号生成（突破、反转、主升、放量）
3. 市场状态分析
4. 综合评分

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
"""

from .engine import QuantCore, get_quant_core
from .models import QuantResult, FactorResult, SignalResult, ScoreResult

__all__ = [
    "QuantCore",
    "get_quant_core",
    "QuantResult",
    "FactorResult",
    "SignalResult",
    "ScoreResult",
]
