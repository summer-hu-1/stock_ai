"""
龙头结果模型

定义龙头识别的结构化输出
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LeaderInfo:
    """龙头股信息"""
    stock_code: str
    stock_name: str
    sector: str
    rank: int  # 在板块中的排名
    strength: float  # 龙头强度 0-100


@dataclass
class LeaderResult:
    """龙头引擎的完整输出"""
    success: bool
    is_leader: bool = False
    leader_score: float = 0.0  # 0-100
    sector: Optional[str] = None
    sector_rank: int = 0
    peer_leaders: List[LeaderInfo] = field(default_factory=list)
    error: Optional[str] = None
