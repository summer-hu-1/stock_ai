"""
信号结果模型

定义信号引擎的结构化输出
"""

from dataclasses import dataclass, field
from typing import List, Optional


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


@dataclass
class SignalResult:
    """信号引擎的完整输出"""
    success: bool
    signals: List[SignalItem] = field(default_factory=list)
    summary: SignalSummary = field(default_factory=SignalSummary)
    error: Optional[str] = None
