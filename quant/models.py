"""
QuantCore 数据模型

V10 架构：量化核心数据结构
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QuantResult:
    """
    量化分析结果

    包含因子、信号、市场状态和评分
    """
    code: str
    market: str = "cn"
    factors: Dict[str, Any] = field(default_factory=dict)
    signals: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    leaders: Dict[str, Any] = field(default_factory=dict)
    date: datetime = field(default_factory=datetime.now)
    elapsed_ms: float = 0.0

    @property
    def raw_data(self) -> Dict[str, Any]:
        """返回原始数据字典"""
        return {
            "factors": self.factors,
            "signals": self.signals,
            "state": self.state,
            "score": self.score,
            "leaders": self.leaders,
        }


@dataclass
class FactorResult:
    """因子计算结果"""
    trend: float = 0.0
    momentum: float = 0.0
    volume: float = 0.0
    volatility: float = 0.0
    strength: float = 0.0


@dataclass
class SignalResult:
    """信号生成结果"""
    direction: str = "neutral"
    strength: float = 0.0
    signal_type: str = ""
    reasons: list = field(default_factory=list)


@dataclass
class ScoreResult:
    """评分结果"""
    final_score: float = 0.0
    signal: str = "观望"
    confidence: float = 0.0
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    volatility_score: float = 0.0
    strength_score: float = 0.0
    leader_bonus: float = 0.0
    market_state_adj: float = 0.0
