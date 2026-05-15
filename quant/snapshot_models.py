"""
统一快照对象模型

这是 V10.3 核心升级：
- 从"散表系统"收敛为"统一 StockSnapshot 对象"
- 所有计算结果统一封装
- 形成单向数据流水线
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MarketCycle(Enum):
    """市场周期"""
    BULL = "牛市"
    BEAR = "熊市"
    CONSOLIDATION = "震荡市"
    UNKNOWN = "未知"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    EXTREME = "极端风险"


class TradeAction(Enum):
    """交易信号"""
    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"
    WATCH = "观察"


@dataclass
class FactorSnapshot:
    """因子快照"""
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    volatility_score: float = 0.0
    strength_score: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "trend": self.trend_score,
            "momentum": self.momentum_score,
            "volume": self.volume_score,
            "volatility": self.volatility_score,
            "strength": self.strength_score,
        }


@dataclass
class SignalSnapshot:
    """信号快照"""
    breakout: int = 0
    reversal: int = 0
    main_rise: int = 0
    volume_surge: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "breakout": self.breakout,
            "reversal": self.reversal,
            "main_rise": self.main_rise,
            "volume_surge": self.volume_surge,
        }


@dataclass
class MarketContextSnapshot:
    """市场上下文快照"""
    cycle: str = "UNKNOWN"
    sentiment_score: float = 50.0
    risk_level: str = "MEDIUM"
    hot_sector: str = ""
    limit_up_count: int = 0
    limit_down_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "sentiment": self.sentiment_score,
            "risk_level": self.risk_level,
            "hot_sector": self.hot_sector,
            "limit_up": self.limit_up_count,
            "limit_down": self.limit_down_count,
        }


@dataclass
class LeaderSnapshot:
    """龙头快照"""
    is_leader: bool = False
    sector: str = ""
    leader_score: float = 0.0
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_leader": self.is_leader,
            "sector": self.sector,
            "leader_score": self.leader_score,
            "rank": self.rank,
        }


@dataclass
class StrategySnapshot:
    """策略快照"""
    action: str = "HOLD"
    target_position: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target_position": self.target_position,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "confidence": self.confidence,
        }


@dataclass
class StockSnapshot:
    """
    统一股票快照对象

    这是系统的核心数据单元：
    - code: 股票代码
    - market: 市场代码
    - date: 快照日期

    - factors: 因子计算结果
    - signals: 信号生成结果
    - market_context: 市场上下文
    - leaders: 龙头识别结果
    - strategy: 策略决策结果

    - total_score: 综合评分 (0-100)
    - trade_signal: 交易信号 (BUY/SELL/HOLD/WATCH)
    - reason: 决策原因

    特点：
    1. 单一数据单元包含所有信息
    2. 单向数据流，无循环依赖
    3. 所有计算结果可追溯
    4. 便于存储、查询、分析
    """

    code: str
    market: str
    date: str

    factors: FactorSnapshot = field(default_factory=FactorSnapshot)
    signals: SignalSnapshot = field(default_factory=SignalSnapshot)
    market_context: MarketContextSnapshot = field(default_factory=MarketContextSnapshot)
    leaders: LeaderSnapshot = field(default_factory=LeaderSnapshot)
    strategy: StrategySnapshot = field(default_factory=StrategySnapshot)

    total_score: float = 50.0
    trade_signal: str = "HOLD"
    reason: str = ""

    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "market": self.market,
            "date": self.date,

            "factors": self.factors.to_dict(),
            "signals": self.signals.to_dict(),
            "market_context": self.market_context.to_dict(),
            "leaders": self.leaders.to_dict(),
            "strategy": self.strategy.to_dict(),

            "total_score": self.total_score,
            "trade_signal": self.trade_signal,
            "reason": self.reason,

            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockSnapshot":
        """从字典创建"""
        factors = FactorSnapshot(**data.get("factors", {}))
        signals = SignalSnapshot(**data.get("signals", {}))
        market_context = MarketContextSnapshot(**data.get("market_context", {}))
        leaders = LeaderSnapshot(**data.get("leaders", {}))
        strategy = StrategySnapshot(**data.get("strategy", {}))

        return cls(
            code=data["code"],
            market=data["market"],
            date=data["date"],
            factors=factors,
            signals=signals,
            market_context=market_context,
            leaders=leaders,
            strategy=strategy,
            total_score=data.get("total_score", 50.0),
            trade_signal=data.get("trade_signal", "HOLD"),
            reason=data.get("reason", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass
class DailyPipelineResult:
    """
    每日流水线执行结果

    包含：
    - market_state: 市场整体状态
    - stock_snapshots: 所有股票的快照列表
    - sector_rankings: 板块排名
    - leader_stocks: 龙头股票列表
    - execution_summary: 执行摘要
    """

    date: str
    market_state: MarketContextSnapshot
    stock_snapshots: List[StockSnapshot] = field(default_factory=list)
    sector_rankings: List[Dict[str, Any]] = field(default_factory=list)
    leader_stocks: List[StockSnapshot] = field(default_factory=list)
    execution_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "market_state": self.market_state.to_dict(),
            "stock_count": len(self.stock_snapshots),
            "sector_rankings": self.sector_rankings,
            "leader_count": len(self.leader_stocks),
            "execution_summary": self.execution_summary,
        }
