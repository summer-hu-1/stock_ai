"""
Provider 工厂类
根据市场名称或股票代码自动选择对应的数据源 Provider

核心设计：
1. 根据市场名称直接选择 Provider（用于 UI 选择）
2. 根据股票代码自动检测市场（用于 API 调用）
"""

from providers.ashare_provider import AShareProvider
from providers.hk_provider import HKProvider
from providers.us_provider import USProvider

from core.base_provider import BaseProvider


class ProviderFactory:
    """
    Provider 工厂类
    
    支持两种调用方式：
    1. 根据市场名称获取 Provider（推荐用于 UI）
    2. 根据股票代码自动检测市场并获取 Provider（用于 API）
    """

    @staticmethod
    def get_provider(market: str) -> BaseProvider:
        """
        根据市场名称获取对应的 Provider
        
        Args:
            market: 市场名称，如 "A股", "港股", "美股"
            
        Returns:
            BaseProvider: 对应的数据源 Provider
        """
        market_lower = market.strip()
        
        # A股
        if market_lower == "A股":
            return AShareProvider()
        
        # 港股
        elif market_lower == "港股":
            return HKProvider()
        
        # 美股
        elif market_lower == "美股":
            return USProvider()
        
        # 默认返回 A股 Provider
        return AShareProvider()

    @staticmethod
    def get_provider_by_code(code: str) -> BaseProvider:
        """
        根据股票代码自动检测市场并获取 Provider
        
        Args:
            code: 股票代码，支持多种格式
                  A股: 601360.SH, 000002.SZ
                  港股: 00700.HK
                  美股: AAPL, MSFT
        
        Returns:
            BaseProvider: 对应的数据源 Provider
        """
        code_upper = code.upper().strip()
        
        # A股 - 以 .SZ 或 .SH 结尾
        if code_upper.endswith(".SZ") or code_upper.endswith(".SH"):
            return AShareProvider()
        
        # 港股 - 以 .HK 结尾
        elif code_upper.endswith(".HK"):
            return HKProvider()
        
        # 美股 - 默认返回美股 Provider
        else:
            return USProvider()

    @staticmethod
    def detect_market(code: str) -> str:
        """
        根据股票代码检测市场类型
        
        Returns:
            str: A股/港股/美股
        """
        code_upper = code.upper().strip()
        
        if code_upper.endswith(".SZ") or code_upper.endswith(".SH"):
            return "A股"
        elif code_upper.endswith(".HK"):
            return "港股"
        else:
            return "美股"
