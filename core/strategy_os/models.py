"""
StrategyOS - 策略中台

V10 架构：负责策略调度、仓位管理、风险控制

核心原则：
- ❌ 不计算因子/信号/评分（由 QuantCore 负责）
- ❌ 不解释市场（由 AgentOS 负责）
- ✅ 只负责"该怎么打"：仓位、择时、风控

策略调度逻辑：
1. 根据市场状态（冰点/修复/主升/分歧/高潮/退潮）调整权重
2. 根据评分信号决定仓位
3. 根据风险等级调整敞口
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class MarketCycle(Enum):
    """市场周期枚举"""
    ICY = "冰点"      # 极度悲观，抄底机会
    RECOVERY = "修复"  # 情绪修复，布局时机
    RALLY = "主升"    # 趋势上涨，满仓持有
    DIVERGENCE = "分歧"  # 多空分歧，谨慎操作
    PEAK = "高潮"     # 情绪高潮，减仓观望
    RETREAT = "退潮"  # 趋势下跌，空仓避险


class PositionStrategy(Enum):
    """仓位策略枚举"""
    FULL = "满仓"      # 8-10成仓
    HEAVY = "重仓"    # 6-8成仓
    HALF = "半仓"     # 4-6成仓
    LIGHT = "轻仓"    # 2-4成仓
    EMPTY = "空仓"    # 0-2成仓


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "低"        # 可重仓
    MEDIUM = "中"     # 适中仓位
    HIGH = "高"       # 轻仓或空仓


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    market_cycle: MarketCycle
    base_position: PositionStrategy
    trend_weight: float = 0.3
    momentum_weight: float = 0.2
    volume_weight: float = 0.2
    volatility_weight: float = 0.15
    strength_weight: float = 0.15
    max_position: float = 1.0
    min_position: float = 0.0
    stop_loss_pct: float = 7.0
    take_profit_pct: float = 15.0


@dataclass
class Position:
    """仓位信息"""
    code: str
    position_ratio: float  # 仓位比例 0-1
    shares: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0


@dataclass
class StrategyOutput:
    """策略输出"""
    code: str
    date: datetime
    market_cycle: str
    position_strategy: str
    target_position: float  # 目标仓位 0-1
    action: str  # 买入, 持有, 减仓, 清仓
    urgency: str  # 立即执行, 观察, 等待
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_review_date: Optional[str] = None
    confidence: float = 0.5  # 置信度 0-1


@dataclass
class PortfolioOutput:
    """组合输出"""
    date: datetime
    total_position: float  # 总仓位 0-1
    positions: List[Position] = field(default_factory=list)
    total_market_value: float = 0.0
    total_profit_loss: float = 0.0
    daily_return: float = 0.0
    risk_adjusted_return: float = 0.0


@dataclass
class RiskControlOutput:
    """风控输出"""
    date: datetime
    risk_level: str
    position_limit: float  # 仓位上限
    max_drawdown: float = 0.0
    var_95: float = 0.0  # 95% VaR
    stop_loss_triggered: bool = False
    warnings: List[str] = field(default_factory=list)
