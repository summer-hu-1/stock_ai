from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseProvider(ABC):
    """
    Provider 基类 - 定义统一的数据源接口
    所有市场 Provider 必须实现这些方法
    """

    @abstractmethod
    def get_stock_data(self, code: str) -> Dict[str, Any]:
        """获取个股数据"""
        pass

    @abstractmethod
    def get_market_sentiment(self) -> Dict[str, Any]:
        """获取市场情绪数据"""
        pass

    @abstractmethod
    def get_sectors(self) -> List[Dict[str, Any]]:
        """获取板块数据"""
        pass

    @abstractmethod
    def get_market_volume(self) -> float:
        """获取全市场成交额"""
        pass
