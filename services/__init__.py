"""
Services Module - 服务层

V9 Service Layer 模块，提供统一的业务接口：
1. AnalysisService - 分析服务
2. SignalService - 信号服务
3. MarketService - 市场服务
4. SyncService - 同步服务
5. UserService - 用户服务

核心原则：
- UI 不直接调用 Engine 层，通过 Service Layer 访问
- 统一错误处理和日志记录
- 提供清晰的 API 接口
"""

from .analysis_service import AnalysisService, get_analysis_service
from .signal_service import SignalService, get_signal_service
from .market_service import MarketService, get_market_service
from .sync_service import SyncService, get_sync_service
from .user_service import UserService, get_user_service

__all__ = [
    'AnalysisService',
    'get_analysis_service',
    'SignalService',
    'get_signal_service',
    'MarketService',
    'get_market_service',
    'SyncService',
    'get_sync_service',
    'UserService',
    'get_user_service'
]
