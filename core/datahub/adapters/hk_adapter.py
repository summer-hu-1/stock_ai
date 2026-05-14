from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import OHLCV, StockInfo


class HKAdapter:
    def __init__(self):
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            try:
                from core.provider_factory import ProviderFactory
                self._provider = ProviderFactory.get_provider("hk")
            except Exception:
                self._provider = None
        return self._provider

    def get_stock_daily(
        self,
        code: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[OHLCV]:
        try:
            provider = self._get_provider()
            if provider and hasattr(provider, 'get_stock_data'):
                data = provider.get_stock_data(code)
                if data and 'history' in data:
                    return self._parse_history(data['history'], code)
        except Exception as e:
            print(f"获取港股 {code} 日线数据失败: {e}")

        return []

    def get_stock_realtime(self, code: str) -> Optional[OHLCV]:
        try:
            provider = self._get_provider()
            if provider and hasattr(provider, 'get_stock_data'):
                data = provider.get_stock_data(code)
                if data:
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
            print(f"获取港股实时数据 {code} 失败: {e}")

        return None

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            provider = self._get_provider()
            if provider and hasattr(provider, 'get_stock_data'):
                data = provider.get_stock_data(code)
                if data:
                    return StockInfo(
                        code=code,
                        name=data.get("name", code),
                        market="hk",
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
            print(f"获取港股信息 {code} 失败: {e}")

        return None

    def _parse_history(self, history: List[Dict], code: str) -> List[OHLCV]:
        result = []
        for item in history:
            try:
                ohlcv = OHLCV(
                    code=code,
                    date=datetime.strptime(item.get("date", ""), "%Y-%m-%d"),
                    open=float(item.get("open", 0)),
                    high=float(item.get("high", 0)),
                    low=float(item.get("low", 0)),
                    close=float(item.get("close", 0)),
                    volume=float(item.get("volume", 0)),
                    amount=float(item.get("amount", 0)),
                    turnover_rate=float(item.get("turnover_rate", 0)),
                    price_change_pct=float(item.get("change_pct", 0)),
                    amplitude=0.0
                )
                result.append(ohlcv)
            except Exception:
                continue
        return result