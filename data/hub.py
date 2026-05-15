from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import pandas as pd
import os

from .models import OHLCV, MarketState, Sector, StockInfo, FundFlow, News, IndexData
from .cache import get_cache


class DataHub:
    """
    统一数据入口 - 所有模块只能从这里拿数据

    职责：
        1. 统一数据获取接口
        2. 多数据源自动路由
        3. 缓存管理
        4. 数据格式标准化

    禁止：
        - pd.read_csv() 散落调用
        - 直接实例化 CSVProvider / DataProvider / providers/*

    允许：
        datahub.get_stock_daily("000001")
        datahub.get_market_state()
        datahub.get_sector("半导体")
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._cache = get_cache()
        self._initialized = True
        self._adapters = {}
        self._init_adapters()

    def _init_adapters(self):
        from .adapters.csv_adapter import CSVAdapter
        from .adapters.realtime_adapter import RealtimeAdapter
        from .adapters.ashare_adapter import AShareAdapter
        from .adapters.memory_adapter import MemoryAdapter
        from .adapters.hk_adapter import HKAdapter
        from .adapters.us_adapter import USAdapter

        self._adapters["csv"] = CSVAdapter()
        self._adapters["realtime"] = RealtimeAdapter()
        self._adapters["ashare"] = AShareAdapter()
        self._adapters["memory"] = MemoryAdapter()
        self._adapters["hk"] = HKAdapter()
        self._adapters["us"] = USAdapter()

    def _detect_market(self, code: str) -> str:
        if code.endswith(".SH") or code.endswith(".SZ"):
            return "cn"
        if code.endswith(".HK"):
            return "hk"
        if len(code) == 5 or code.isalpha():
            return "us"
        if code.startswith("6") or code.startswith("0") or code.startswith("3"):
            return "cn"
        return "cn"

    def get_stock_daily(
        self,
        code: str,
        market: str = None,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        use_cache: bool = True
    ) -> List[OHLCV]:
        cache_key = f"daily_{market}_{code}_{start_date}_{end_date}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        market = market or self._detect_market(code)
        data = self._adapters["csv"].get_stock_daily(code, market, start_date, end_date)

        if use_cache:
            self._cache.set(cache_key, data, ttl=3600)

        return data

    def get_stock_realtime(self, code: str, market: str = None) -> Optional[OHLCV]:
        cache_key = f"realtime_{market}_{code}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        market = market or self._detect_market(code)
        data = self._adapters["realtime"].get_stock_realtime(code, market)

        if data is not None:
            self._cache.set(cache_key, data, ttl=60)

        return data

    def get_stock_info(self, code: str, market: str = None) -> Optional[StockInfo]:
        cache_key = f"info_{market}_{code}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        market = market or self._detect_market(code)
        data = self._adapters["realtime"].get_stock_info(code, market)

        if data is not None:
            self._cache.set(cache_key, data, ttl=3600)

        return data

    def get_market_state(self, date: Union[str, datetime] = None) -> Optional[MarketState]:
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")

        cache_key = f"state_{date.strftime('%Y%m%d')}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["memory"].get_market_state(date)

        if data is not None:
            self._cache.set(cache_key, data, ttl=300)

        return data

    def get_market_state_history(self, days: int = 30) -> List[MarketState]:
        cache_key = f"state_history_{days}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["memory"].get_market_state_history(days)

        self._cache.set(cache_key, data, ttl=300)

        return data

    def get_market_sentiment(self, market: str = "cn") -> Dict[str, Any]:
        cache_key = f"sentiment_{market}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].get_market_sentiment()

        self._cache.set(cache_key, data, ttl=300)

        return data

    def get_sector(self, sector_name: str, market: str = "cn") -> Optional[Sector]:
        cache_key = f"sector_{sector_name}_{market}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].get_sector(sector_name)

        if data is not None:
            self._cache.set(cache_key, data, ttl=300)

        return data

    def get_hot_sectors(self, top_n: int = 10, market: str = "cn") -> List[Sector]:
        cache_key = f"hot_sectors_{top_n}_{market}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].get_hot_sectors(top_n)

        self._cache.set(cache_key, data, ttl=300)

        return data

    def get_index_daily(
        self,
        index_code: str,
        days: int = 30,
        market: str = "cn"
    ) -> List[IndexData]:
        cache_key = f"index_{index_code}_{days}_{market}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].get_index_daily(index_code, days)

        self._cache.set(cache_key, data, ttl=300)

        return data

    def get_fund_flow(self, code: str, market: str = None) -> Optional[FundFlow]:
        market = market or self._detect_market(code)
        cache_key = f"fund_flow_{market}_{code}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].get_fund_flow(code)

        if data is not None:
            self._cache.set(cache_key, data, ttl=300)

        return data

    def get_news(self, code: str = None, limit: int = 10) -> List[News]:
        cache_key = f"news_{code}_{limit}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].get_news(code, limit)

        self._cache.set(cache_key, data, ttl=300)

        return data

    def search_stocks(self, keyword: str, market: str = "cn") -> List[StockInfo]:
        cache_key = f"search_{market}_{keyword}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._adapters["ashare"].search_stocks(keyword)

        self._cache.set(cache_key, data, ttl=3600)

        return data

    def get_ohlcv_dataframe(
        self,
        code: str,
        market: str = None,
        days: int = 250,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None
    ) -> pd.DataFrame:
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=days)

        ohlcv_list = self.get_stock_daily(code, market, start_date, end_date)

        if not ohlcv_list:
            return pd.DataFrame()

        return pd.DataFrame([o.to_dict() for o in ohlcv_list])

    def invalidate(self, pattern: str) -> int:
        return self._cache.invalidate(pattern)

    def clear_cache(self) -> int:
        return self._cache.clear()

    def cache_stats(self) -> Dict[str, Any]:
        return self._cache.stats()


_datahub_instance: Optional[DataHub] = None


def get_datahub() -> DataHub:
    global _datahub_instance
    if _datahub_instance is None:
        _datahub_instance = DataHub()
    return _datahub_instance