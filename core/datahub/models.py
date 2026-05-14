from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class OHLCV:
    code: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    turnover_rate: float = 0.0
    price_change_pct: float = 0.0
    amplitude: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any], code: str = "") -> "OHLCV":
        return cls(
            code=code or data.get("code", ""),
            date=data.get("date", datetime.now()),
            open=float(data.get("open", 0)),
            high=float(data.get("high", 0)),
            low=float(data.get("low", 0)),
            close=float(data.get("close", 0)),
            volume=float(data.get("volume", 0)),
            amount=float(data.get("amount", 0)),
            turnover_rate=float(data.get("turnover_rate", 0)),
            price_change_pct=float(data.get("price_change_pct", 0)),
            amplitude=float(data.get("amplitude", 0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "date": self.date.isoformat() if isinstance(self.date, datetime) else self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "turnover_rate": self.turnover_rate,
            "price_change_pct": self.price_change_pct,
            "amplitude": self.amplitude
        }


@dataclass
class MarketState:
    date: datetime
    cycle: str
    cycle_stage: str
    emotion_score: float
    emotion_trend: str
    limit_up_count: int = 0
    limit_down_count: int = 0
    rise_ratio: float = 0.0
    total_volume: float = 0.0
    north_money: float = 0.0
    risk_level: str = "中"
    top_sectors: List[str] = field(default_factory=list)
    hot_themes: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketState":
        return cls(
            date=data.get("date", datetime.now()),
            cycle=data.get("cycle", "未知"),
            cycle_stage=data.get("cycle_stage", "未知"),
            emotion_score=float(data.get("emotion_score", 50)),
            emotion_trend=data.get("emotion_trend", "平稳"),
            limit_up_count=int(data.get("limit_up_count", 0)),
            limit_down_count=int(data.get("limit_down_count", 0)),
            rise_ratio=float(data.get("rise_ratio", 0)),
            total_volume=float(data.get("total_volume", 0)),
            north_money=float(data.get("north_money", 0)),
            risk_level=data.get("risk_level", "中"),
            top_sectors=data.get("top_sectors", []),
            hot_themes=data.get("hot_themes", [])
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat() if isinstance(self.date, datetime) else self.date,
            "cycle": self.cycle,
            "cycle_stage": self.cycle_stage,
            "emotion_score": self.emotion_score,
            "emotion_trend": self.emotion_trend,
            "limit_up_count": self.limit_up_count,
            "limit_down_count": self.limit_down_count,
            "rise_ratio": self.rise_ratio,
            "total_volume": self.total_volume,
            "north_money": self.north_money,
            "risk_level": self.risk_level,
            "top_sectors": self.top_sectors,
            "hot_themes": self.hot_themes
        }


@dataclass
class Sector:
    name: str
    change_pct: float
    leader_stocks: List[str] = field(default_factory=list)
    strength_score: float = 50.0
    stock_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "change_pct": self.change_pct,
            "leader_stocks": self.leader_stocks,
            "strength_score": self.strength_score,
            "stock_count": self.stock_count
        }


@dataclass
class StockInfo:
    code: str
    name: str
    market: str
    sector: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    volume_ratio: float = 0.0
    turnover: float = 0.0
    amplitude: float = 0.0
    total_value: float = 0.0
    float_value: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "market": self.market,
            "sector": self.sector,
            "price": self.price,
            "change_pct": self.change_pct,
            "volume_ratio": self.volume_ratio,
            "turnover": self.turnover,
            "amplitude": self.amplitude,
            "total_value": self.total_value,
            "float_value": self.float_value
        }


@dataclass
class FundFlow:
    code: str
    date: datetime
    north_money: float = 0.0
    north_money_5d: float = 0.0
    north_money_10d: float = 0.0
    main_inflow: float = 0.0
    main_inflow_pct: float = 0.0
    retail_inflow: float = 0.0
    retail_inflow_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "date": self.date.isoformat() if isinstance(self.date, datetime) else self.date,
            "north_money": self.north_money,
            "north_money_5d": self.north_money_5d,
            "north_money_10d": self.north_money_10d,
            "main_inflow": self.main_inflow,
            "main_inflow_pct": self.main_inflow_pct,
            "retail_inflow": self.retail_inflow,
            "retail_inflow_pct": self.retail_inflow_pct
        }


@dataclass
class News:
    title: str
    content: str
    publish_time: datetime
    source: str = ""
    url: str = ""
    sentiment: str = "neutral"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "publish_time": self.publish_time.isoformat() if isinstance(self.publish_time, datetime) else self.publish_time,
            "source": self.source,
            "url": self.url,
            "sentiment": self.sentiment
        }


@dataclass
class IndexData:
    code: str
    name: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    change_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "date": self.date.isoformat() if isinstance(self.date, datetime) else self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "amount": self.amount,
            "change_pct": self.change_pct
        }


MARKET_CYCLE_STAGES = ["冰点", "修复", "主升", "分歧", "高潮", "退潮"]
RISK_LEVELS = ["低", "中", "高"]
EMOTION_TRENDS = ["上升", "下降", "平稳"]