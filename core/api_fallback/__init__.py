"""
API自动降级框架

集中管理所有API的降级策略，支持不同数据类型、运行模式和市场
"""

from .manager import (
    APIFallbackManager,
    get_fallback_manager,
    MarketType,
    DataType,
    RunMode,
    APIEndpoint,
    FallbackResult,
    api_fallback
)

from .registry import (
    register_default_apis,
    get_stock_data_with_fallback,
    get_market_sentiment_with_fallback,
    get_sectors_with_fallback,
    get_stock_list_with_fallback
)

__all__ = [
    'APIFallbackManager',
    'get_fallback_manager',
    'MarketType',
    'DataType',
    'RunMode',
    'APIEndpoint',
    'FallbackResult',
    'api_fallback',
    'register_default_apis',
    'get_stock_data_with_fallback',
    'get_market_sentiment_with_fallback',
    'get_sectors_with_fallback',
    'get_stock_list_with_fallback',
]
