"""
因子结果模型

定义因子计算的结构化输出
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class FactorItem:
    """单个因子的结果"""
    name: str
    value: float
    score: float  # 0-100
    category: str  # 'trend', 'momentum', 'volume', 'volatility', 'quality'
    description: str = ""
    is_positive: bool = True


@dataclass
class FactorSummary:
    """因子计算摘要"""
    overall_score: float  # 0-100
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    volatility_score: float = 0.0
    quality_score: float = 0.0
    strong_factors: List[str] = field(default_factory=list)
    weak_factors: List[str] = field(default_factory=list)


@dataclass
class FactorResult:
    """因子引擎的完整输出"""
    success: bool
    items: List[FactorItem] = field(default_factory=list)
    summary: FactorSummary = field(default_factory=FactorSummary)
    raw_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
