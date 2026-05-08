from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class MarketContext:
    """
    统一的市场上下文数据结构
    所有Agent共享此数据，避免重复请求
    """

    stock_code: str
    stock_name: str

    stock_data: Dict[str, Any]

    market_sentiment: Dict[str, Any]

    sectors: List[Dict[str, Any]]

    market_volume: float

    risk_level: str

    # 扩展字段
    hot_stocks: Optional[List[Dict[str, Any]]] = None
    news: Optional[List[Dict[str, Any]]] = None
    fund_flow: Optional[Dict[str, Any]] = None

    def get_stock_price(self) -> float:
        """获取股票当前价格"""
        return self.stock_data.get("price", 0.0)

    def get_market_up_ratio(self) -> float:
        """获取市场上涨比例"""
        up = self.market_sentiment.get("up_count", 0)
        down = self.market_sentiment.get("down_count", 0)
        total = up + down
        return up / total if total > 0 else 0.0
