from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.datahub import OHLCV, MarketState


@dataclass
class FactorItem:
    """单个因子的结果"""
    name: str
    value: float
    score: float  # 0-100
    category: str  # 'trend', 'momentum', 'volume', 'volatility', 'strength'
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
    strength_score: float = 0.0
    strong_factors: List[str] = field(default_factory=list)
    weak_factors: List[str] = field(default_factory=list)


@dataclass
class FactorOutput:
    """所有因子的统一输出"""
    code: str
    date: datetime
    factors: Dict[str, FactorItem]
    summary: FactorSummary
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class SignalItem:
    """单个信号的结果"""
    name: str
    signal_type: str  # 'buy', 'sell', 'hold', 'warning'
    strength: int  # 0-100
    confidence: float  # 0-1
    description: str = ""
    source: str = ""  # 信号来源


@dataclass
class SignalSummary:
    """信号计算摘要"""
    overall_strength: float = 50.0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    warning_signals: int = 0
    direction: str = "neutral"  # bullish, bearish, neutral


@dataclass
class SignalOutput:
    """所有信号的统一输出"""
    code: str
    date: datetime
    signals: Dict[str, SignalItem]
    summary: SignalSummary
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class StateOutput:
    """市场状态的统一输出（MarketMemory 升级版）"""
    date: datetime
    cycle: str  # 冰点, 修复, 主升, 分歧, 高潮, 退潮
    cycle_stage: str  # early, mid, late
    emotion_score: float  # 0-100
    emotion_trend: str  # 上升, 下降, 平稳
    limit_up_count: int = 0
    limit_down_count: int = 0
    rise_ratio: float = 0.0
    total_volume: float = 0.0
    north_money: float = 0.0
    risk_level: str = "中"  # 低, 中, 高
    top_sectors: List[str] = field(default_factory=list)
    hot_themes: List[str] = field(default_factory=list)
    sector_rotation: Dict[str, Any] = field(default_factory=dict)
    leader_rotation: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class LeaderOutput:
    """龙头识别输出"""
    code: str
    date: datetime
    is_leader: bool = False
    leader_score: float = 0.0  # 0-100
    leader_type: str = ""  # 龙头, 强势股, 普通
    sector_rank: int = 0
    peer_leaders: List[Dict[str, Any]] = field(default_factory=list)
    reason: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class ScoreOutput:
    """综合评分的统一输出（新增 Score Engine）"""
    code: str
    date: datetime
    final_score: float  # 0-100 最终评分
    trend_score: float
    momentum_score: float
    volume_score: float
    volatility_score: float
    strength_score: float
    leader_bonus: float  # 龙头加分
    market_state_adj: float  # 市场状态调整
    signal: str  # 看多, 谨慎看多, 观望, 谨慎看空, 看空
    confidence: float  # 置信度 0-1
    score_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class QuantResult:
    """QuantCore 完整输出"""
    code: str
    date: datetime
    factors: FactorOutput
    signals: SignalOutput
    state: StateOutput
    leaders: LeaderOutput
    score: ScoreOutput
    elapsed_ms: float
    raw_data: Optional[Dict[str, Any]] = None
