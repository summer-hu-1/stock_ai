"""
QuantCore 数据模型

V10 架构：量化核心数据结构
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LeadersInfo:
    """龙头信息"""
    is_leader: bool = False
    leader_type: str = "None"
    leader_score: float = 0.0


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
    state: Any = None  # StateResult 对象
    score: Any = None  # ScoreResult 对象
    leaders: LeadersInfo = field(default_factory=LeadersInfo)
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
    risk_level: str = "中等"
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    volatility_score: float = 0.0
    strength_score: float = 0.0
    leader_bonus: float = 0.0
    market_state_adj: float = 0.0


@dataclass
class StateResult:
    """市场状态结果"""
    cycle: str = "震荡"
    cycle_stage: str = "中性"
    emotion_score: float = 50.0
    risk_level: str = "中等"
    state: str = "unknown"
    description: str = ""
    sentiment: float = 0.5
    volatility: float = 0.0
    emotion_trend: str = "平稳"  # 添加缺失的属性
    limit_up_count: int = 0  # 添加缺失的属性
    limit_down_count: int = 0  # 添加相关属性
    rise_ratio: float = 0.0  # 添加缺失的属性
    total_volume: float = 0.0  # 添加缺失的属性 - 总成交额(万亿)
    north_money: float = 0.0  # 添加缺失的属性 - 北向资金(亿)
    top_sectors: list = field(default_factory=list)  # 添加缺失的属性 - 热门板块
