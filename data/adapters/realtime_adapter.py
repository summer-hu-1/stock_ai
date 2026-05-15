from typing import Optional, Dict, Any
from datetime import datetime

from ..models import OHLCV, StockInfo


class RealtimeAdapter:
    def __init__(self):
        self._provider = None
        self._market_data_module = None

    def _get_provider(self):
        if self._provider is None:
            from core.data_provider import DataProvider
            self._provider = DataProvider()
        return self._provider

    def _get_market_data_module(self):
        if self._market_data_module is None:
            from modules import market_data
            self._market_data_module = market_data
        return self._market_data_module

    def get_stock_realtime(self, code: str, market: str = None) -> Optional[OHLCV]:
        try:
            md = self._get_market_data_module()
            data = md.get_stock_data(code, market or "cn")

            if not data:
                return None

            return OHLCV(
                code=code,
                date=datetime.now(),
                open=float(data.get("open", 0)),
                high=float(data.get("high", 0)),
                low=float(data.get("low", 0)),
                close=float(data.get("price", 0)),
                volume=float(data.get("volume", 0)),
                amount=float(data.get("amount", 0)),
                turnover_rate=float(data.get("turnover_rate", 0)),
                price_change_pct=float(data.get("change_pct", 0)),
                amplitude=float(data.get("amplitude", 0))
            )
        except Exception as e:
            print(f"获取实时数据失败 {code}: {e}")
            return None

    def get_stock_info(self, code: str, market: str = None) -> Optional[StockInfo]:
        try:
            md = self._get_market_data_module()
            data = md.get_stock_data(code, market or "cn")

            if not data:
                return None

            return StockInfo(
                code=code,
                name=data.get("name", code),
                market=market or "cn",
                sector=data.get("sector", ""),
                price=float(data.get("price", 0)),
                change_pct=float(data.get("change_pct", 0)),
                volume_ratio=float(data.get("volume_ratio", 0)),
                turnover=float(data.get("turnover", 0)),
                amplitude=float(data.get("amplitude", 0)),
                total_value=float(data.get("market_cap", 0)),
                float_value=float(data.get("float_cap", 0))
            )
        except Exception as e:
            print(f"获取股票信息失败 {code}: {e}")
            return None

    def get_market_summary(self, market: str = "cn") -> Dict[str, Any]:
        try:
            md = self._get_market_data_module()
            sentiment = md.get_market_sentiment(market)

            hot_stocks = md.get_hot_stocks() if hasattr(md, 'get_hot_stocks') else []

            return {
                "sentiment": sentiment,
                "hot_stocks": hot_stocks,
                "timestamp": datetime.now()
            }
        except Exception as e:
            print(f"获取市场摘要失败: {e}")
            return {"sentiment": {}, "hot_stocks": [], "timestamp": datetime.now()}