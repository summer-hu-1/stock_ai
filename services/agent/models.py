"""
Agent数据模型

定义Agent层的数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime


@dataclass
class AnalysisReport:
    """分析报告"""
    code: str
    name: str
    market: str
    report: str
    confidence: float = 0.5
    key_points: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradingInsight:
    """交易洞察"""
    code: str
    action: str
    reason: str
    target_price: float = 0.0
    stop_loss: float = 0.0
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketNarrative:
    """市场叙事"""
    period: str
    narrative: str
    key_events: List[str] = field(default_factory=list)
    sentiment_trend: str = "neutral"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskAssessment:
    """风险评估"""
    level: str
    factors: List[str] = field(default_factory=list)
    mitigation: List[str] = field(default_factory=list)
    score: float = 0.5
