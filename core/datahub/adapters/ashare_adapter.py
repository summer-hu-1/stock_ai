from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Sector, FundFlow, News, IndexData, StockInfo


class AShareAdapter:
    def __init__(self):
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            try:
                from core.provider_factory import ProviderFactory
                self._provider = ProviderFactory.get_provider("cn")
            except Exception:
                self._provider = None
        return self._provider

    def get_market_sentiment(self) -> Dict[str, Any]:
        try:
            provider = self._get_provider()
            if provider:
                return provider.get_market_sentiment()
        except Exception as e:
            print(f"获取市场情绪失败: {e}")

        return {
            "up_count": 0,
            "down_count": 0,
            "limit_up_count": 0,
            "limit_down_count": 0,
            "rise_ratio": 0.0,
            "emotion_score": 50,
            "timestamp": datetime.now()
        }

    def get_sector(self, sector_name: str) -> Optional[Sector]:
        try:
            provider = self._get_provider()
            if provider:
                sectors = provider.get_sectors()
                for s in sectors:
                    if sector_name in s.get("name", ""):
                        return Sector(
                            name=s.get("name", sector_name),
                            change_pct=float(s.get("change_pct", 0)),
                            leader_stocks=s.get("leader_stocks", []),
                            strength_score=float(s.get("strength_score", 50)),
                            stock_count=int(s.get("stock_count", 0))
                        )
        except Exception as e:
            print(f"获取板块 {sector_name} 失败: {e}")

        return None

    def get_hot_sectors(self, top_n: int = 10) -> List[Sector]:
        try:
            provider = self._get_provider()
            if provider:
                sectors = provider.get_sectors()
                sectors_sorted = sorted(
                    [s for s in sectors if s.get("change_pct", 0) > 0],
                    key=lambda x: x.get("change_pct", 0),
                    reverse=True
                )[:top_n]

                return [
                    Sector(
                        name=s.get("name", ""),
                        change_pct=float(s.get("change_pct", 0)),
                        leader_stocks=s.get("leader_stocks", []),
                        strength_score=float(s.get("strength_score", 50)),
                        stock_count=int(s.get("stock_count", 0))
                    )
                    for s in sectors_sorted
                ]
        except Exception as e:
            print(f"获取热门板块失败: {e}")

        return []

    def get_index_daily(self, index_code: str, days: int = 30) -> List[IndexData]:
        try:
            provider = self._get_provider()
            if provider and hasattr(provider, "get_index_data"):
                df = provider.get_index_data(index_code, days)
                if df is not None and not df.empty:
                    return [
                        IndexData(
                            code=index_code,
                            name=index_code,
                            date=row.get("date", datetime.now()),
                            open=float(row.get("open", 0)),
                            high=float(row.get("high", 0)),
                            low=float(row.get("low", 0)),
                            close=float(row.get("close", 0)),
                            volume=float(row.get("volume", 0)),
                            amount=float(row.get("amount", 0)),
                            change_pct=float(row.get("change_pct", 0))
                        )
                        for _, row in df.iterrows()
                    ]
        except Exception as e:
            print(f"获取指数数据 {index_code} 失败: {e}")

        return []

    def get_fund_flow(self, code: str) -> Optional[FundFlow]:
        try:
            provider = self._get_provider()
            if provider and hasattr(provider, "get_fund_flow"):
                data = provider.get_fund_flow(code)
                if data:
                    return FundFlow(
                        code=code,
                        date=datetime.now(),
                        north_money=float(data.get("north_money", 0)),
                        north_money_5d=float(data.get("north_money_5d", 0)),
                        north_money_10d=float(data.get("north_money_10d", 0)),
                        main_inflow=float(data.get("main_inflow", 0)),
                        main_inflow_pct=float(data.get("main_inflow_pct", 0)),
                        retail_inflow=float(data.get("retail_inflow", 0)),
                        retail_inflow_pct=float(data.get("retail_inflow_pct", 0))
                    )
        except Exception as e:
            print(f"获取资金流 {code} 失败: {e}")

        return None

    def get_news(self, code: str = None, limit: int = 10) -> List[News]:
        try:
            provider = self._get_provider()
            if provider and hasattr(provider, "get_news"):
                news_list = provider.get_news(code, limit)
                return [
                    News(
                        title=n.get("title", ""),
                        content=n.get("content", ""),
                        publish_time=n.get("publish_time", datetime.now()),
                        source=n.get("source", ""),
                        url=n.get("url", ""),
                        sentiment=n.get("sentiment", "neutral")
                    )
                    for n in news_list
                ]
        except Exception as e:
            print(f"获取新闻失败: {e}")

        return []

    def search_stocks(self, keyword: str) -> List[StockInfo]:
        try:
            from core.symbol_resolver import SymbolResolver
            from core.market_registry import MARKETS

            cn_config = MARKETS.get("A股", {})
            resolver = SymbolResolver(cn_config)

            results = resolver.search(keyword)
            return [
                StockInfo(
                    code=r.get("code", ""),
                    name=r.get("name", ""),
                    market="cn",
                    sector=r.get("sector", ""),
                    price=float(r.get("price", 0)),
                    change_pct=float(r.get("change_pct", 0))
                )
                for r in results
            ]
        except Exception as e:
            print(f"搜索股票 {keyword} 失败: {e}")
            return []