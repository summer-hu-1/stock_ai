"""
API降级策略管理中心

集中管理所有API的降级策略，支持：
1. 不同数据类型（情绪数据、周期数据、个股数据等）
2. 不同运行模式（极速/标准/正常模式）
3. 不同市场（A股/港股/美股等）
4. 自动降级与日志记录
"""

import time
import logging
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketType(Enum):
    """市场类型"""
    A_STOCK = "A"  # A股
    HK_STOCK = "HK"  # 港股
    US_STOCK = "US"  # 美股


class RunMode(Enum):
    """运行模式"""
    FAST = "fast"  # 极速模式
    STANDARD = "standard"  # 标准模式
    NORMAL = "normal"  # 正常模式


class DataType(Enum):
    """数据类型"""
    STOCK_DATA = "stock_data"  # 个股数据
    MARKET_SENTIMENT = "market_sentiment"  # 市场情绪
    SECTOR_DATA = "sector_data"  # 板块数据
    MARKET_VOLUME = "market_volume"  # 市场成交量
    HISTORICAL_DATA = "historical_data"  # 历史数据
    STOCK_LIST = "stock_list"  # 股票列表


@dataclass
class APIEndpoint:
    """API端点配置"""
    name: str
    provider: Callable
    priority: int = 0  # 优先级，数字越小优先级越高
    timeout: float = 10.0  # 超时时间（秒）
    retry_count: int = 3  # 重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）
    enabled: bool = True  # 是否启用
    market: MarketType = MarketType.A_STOCK  # 所属市场
    data_type: DataType = DataType.STOCK_DATA  # 数据类型
    run_mode: RunMode = RunMode.STANDARD  # 适用运行模式
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


@dataclass
class FallbackResult:
    """降级结果"""
    success: bool
    data: Any
    provider_name: str
    error: Optional[str] = None
    fallback_level: int = 0  # 降级了几次
    total_time: float = 0.0  # 总耗时
    tried_providers: List[str] = field(default_factory=list)


class APIFallbackManager:
    """
    API降级策略管理中心

    统一管理所有API的降级策略，支持：
    - 注册/注销API端点
    - 配置降级规则
    - 执行带降级的API调用
    - 记录降级日志
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._apis: Dict[str, Dict[str, List[APIEndpoint]]] = {}  # {market: {data_type: [endpoints]}}
        self._global_endpoints: List[APIEndpoint] = []  # 全局端点
        self._fallback_history: List[FallbackResult] = []  # 降级历史
        self._max_history_size = 1000
        self._statistics: Dict[str, Dict[str, int]] = {}  # 统计信息
        self._initialized = True

        logger.info("✅ API降级策略管理中心初始化完成")

    def register_api(
        self,
        name: str,
        provider: Callable,
        market: MarketType = MarketType.A_STOCK,
        data_type: DataType = DataType.STOCK_DATA,
        run_mode: RunMode = RunMode.STANDARD,
        priority: int = 0,
        timeout: float = 10.0,
        retry_count: int = 3,
        retry_delay: float = 1.0,
        enabled: bool = True,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> None:
        """
        注册API端点

        Args:
            name: API名称（唯一标识）
            provider: API调用函数
            market: 市场类型
            data_type: 数据类型
            run_mode: 运行模式
            priority: 优先级
            timeout: 超时时间
            retry_count: 重试次数
            retry_delay: 重试延迟
            enabled: 是否启用
            metadata: 额外元数据
        """
        endpoint = APIEndpoint(
            name=name,
            provider=provider,
            priority=priority,
            timeout=timeout,
            retry_count=retry_count,
            retry_delay=retry_delay,
            enabled=enabled,
            market=market,
            data_type=data_type,
            run_mode=run_mode,
            metadata=metadata or {}
        )

        key = f"{market.value}:{data_type.value}"
        if key not in self._apis:
            self._apis[key] = []

        # 检查是否已存在同名API
        existing = [i for i, e in enumerate(self._apis[key]) if e.name == name]
        if existing:
            self._apis[key][existing[0]] = endpoint
            logger.info(f"🔄 更新API端点: {name} ({key})")
        else:
            self._apis[key].append(endpoint)
            self._apis[key].sort(key=lambda x: x.priority)
            logger.info(f"✅ 注册API端点: {name} ({key}, 优先级: {priority})")

        # 更新统计信息
        self._init_statistics(name)

    def unregister_api(self, name: str, market: MarketType = None, data_type: DataType = None) -> bool:
        """
        注销API端点

        Args:
            name: API名称
            market: 市场类型（可选）
            data_type: 数据类型（可选）

        Returns:
            bool: 是否成功注销
        """
        if market and data_type:
            key = f"{market.value}:{data_type.value}"
            if key in self._apis:
                self._apis[key] = [e for e in self._apis[key] if e.name != name]
                logger.info(f"🗑️ 注销API端点: {name} ({key})")
                return True
        else:
            # 全局搜索并注销
            found = False
            for key, endpoints in self._apis.items():
                original_len = len(endpoints)
                self._apis[key] = [e for e in endpoints if e.name != name]
                if len(self._apis[key]) < original_len:
                    found = True
                    logger.info(f"🗑️ 注销API端点: {name} ({key})")
            return found
        return False

    def get_endpoints(self, market: MarketType, data_type: DataType, run_mode: RunMode = None) -> List[APIEndpoint]:
        """
        获取指定条件的API端点列表

        Args:
            market: 市场类型
            data_type: 数据类型
            run_mode: 运行模式（可选）

        Returns:
            List[APIEndpoint]: 端点列表，按优先级排序
        """
        key = f"{market.value}:{data_type.value}"
        if key not in self._apis:
            return []

        endpoints = [e for e in self._apis[key] if e.enabled]

        if run_mode:
            endpoints = [e for e in endpoints if e.run_mode == run_mode or e.run_mode == RunMode.STANDARD]

        return sorted(endpoints, key=lambda x: x.priority)

    def call_with_fallback(
        self,
        market: MarketType,
        data_type: DataType,
        run_mode: RunMode = RunMode.STANDARD,
        *args,
        **kwargs
    ) -> FallbackResult:
        """
        调用API并自动降级

        Args:
            market: 市场类型
            data_type: 数据类型
            run_mode: 运行模式
            *args: 传递给API的位置参数
            **kwargs: 传递给API的关键字参数

        Returns:
            FallbackResult: 降级结果
        """
        start_time = time.time()
        endpoints = self.get_endpoints(market, data_type, run_mode)

        if not endpoints:
            return FallbackResult(
                success=False,
                data=None,
                provider_name="",
                error=f"没有找到可用的API端点: {market.value}:{data_type.value}",
                fallback_level=0,
                total_time=time.time() - start_time
            )

        tried_providers = []
        fallback_level = 0
        last_error = None

        for endpoint in endpoints:
            tried_providers.append(endpoint.name)

            try:
                logger.info(f"📡 尝试调用API: {endpoint.name} ({market.value}:{data_type.value})")

                # 执行API调用
                for retry in range(endpoint.retry_count):
                    try:
                        result = endpoint.provider(*args, **kwargs)

                        if result is not None:
                            total_time = time.time() - start_time
                            logger.info(f"✅ API调用成功: {endpoint.name} (耗时: {total_time:.2f}s)")

                            # 记录成功
                            self._record_success(endpoint.name, total_time)

                            return FallbackResult(
                                success=True,
                                data=result,
                                provider_name=endpoint.name,
                                error=None,
                                fallback_level=fallback_level,
                                total_time=total_time,
                                tried_providers=tried_providers
                            )
                        else:
                            logger.warning(f"⚠️ API返回None: {endpoint.name}")
                            last_error = "API返回None"

                    except Exception as e:
                        last_error = str(e)
                        logger.warning(f"⚠️ API调用失败 ({endpoint.name}, 重试 {retry+1}/{endpoint.retry_count}): {e}")

                        if retry < endpoint.retry_count - 1:
                            time.sleep(endpoint.retry_delay)

                # 所有重试都失败，尝试下一个端点
                fallback_level += 1
                logger.warning(f"❌ API {endpoint.name} 完全失败，降级到下一个端点")
                self._record_failure(endpoint.name, last_error)

            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ API {endpoint.name} 调用异常: {e}")
                fallback_level += 1
                self._record_failure(endpoint.name, last_error)

        # 所有端点都失败
        total_time = time.time() - start_time
        logger.error(f"❌ 所有API端点都失败: {market.value}:{data_type.value}")

        return FallbackResult(
            success=False,
            data=None,
            provider_name="",
            error=f"所有API端点都失败，最后错误: {last_error}",
            fallback_level=fallback_level,
            total_time=total_time,
            tried_providers=tried_providers
        )

    def _record_success(self, api_name: str, duration: float) -> None:
        """记录成功调用"""
        if api_name not in self._statistics:
            self._init_statistics(api_name)

        self._statistics[api_name]["success_count"] += 1
        self._statistics[api_name]["total_duration"] += duration
        self._statistics[api_name]["last_success_time"] = time.time()

    def _record_failure(self, api_name: str, error: str) -> None:
        """记录失败调用"""
        if api_name not in self._statistics:
            self._init_statistics(api_name)

        self._statistics[api_name]["failure_count"] += 1
        self._statistics[api_name]["last_failure_time"] = time.time()
        self._statistics[api_name]["last_error"] = error[:100]

    def _init_statistics(self, api_name: str) -> None:
        """初始化统计信息"""
        if api_name not in self._statistics:
            self._statistics[api_name] = {
                "success_count": 0,
                "failure_count": 0,
                "total_duration": 0.0,
                "last_success_time": None,
                "last_failure_time": None,
                "last_error": None
            }

    def get_statistics(self, api_name: str = None) -> Dict:
        """
        获取API统计信息

        Args:
            api_name: API名称（可选，不提供则返回所有）

        Returns:
            Dict: 统计信息
        """
        if api_name:
            return self._statistics.get(api_name, {})
        return self._statistics

    def get_best_provider(self, market: MarketType, data_type: DataType) -> Optional[str]:
        """
        获取最佳Provider（基于历史成功率）

        Args:
            market: 市场类型
            data_type: 数据类型

        Returns:
            str: 最佳Provider名称
        """
        endpoints = self.get_endpoints(market, data_type)
        if not endpoints:
            return None

        best = None
        best_score = -1

        for endpoint in endpoints:
            stats = self._statistics.get(endpoint.name, {})
            success_count = stats.get("success_count", 0)
            failure_count = stats.get("failure_count", 0)
            total = success_count + failure_count

            if total == 0:
                score = 1.0  # 新端点给默认值
            else:
                score = success_count / total

            if score > best_score:
                best_score = score
                best = endpoint.name

        return best

    def enable_api(self, name: str, enabled: bool = True) -> bool:
        """
        启用/禁用API端点

        Args:
            name: API名称
            enabled: 是否启用

        Returns:
            bool: 是否成功
        """
        for key, endpoints in self._apis.items():
            for endpoint in endpoints:
                if endpoint.name == name:
                    endpoint.enabled = enabled
                    logger.info(f"{'✅ 启用' if enabled else '⏸️ 禁用'} API端点: {name}")
                    return True
        return False

    def get_fallback_history(self, limit: int = 100) -> List[FallbackResult]:
        """
        获取降级历史

        Args:
            limit: 返回数量限制

        Returns:
            List[FallbackResult]: 降级历史
        """
        return self._fallback_history[-limit:]


# 全局单例
_manager = None


def get_fallback_manager() -> APIFallbackManager:
    """获取API降级策略管理器单例"""
    global _manager
    if _manager is None:
        _manager = APIFallbackManager()
    return _manager


def api_fallback(
    market: MarketType,
    data_type: DataType,
    run_mode: RunMode = RunMode.STANDARD
):
    """
    API降级装饰器

    用法:
        @api_fallback(MarketType.A_STOCK, DataType.STOCK_DATA, RunMode.FAST)
        def get_stock_data(code):
            # 你的API调用逻辑
            return akshare_stock_data(code)

    Args:
        market: 市场类型
        data_type: 数据类型
        run_mode: 运行模式
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_fallback_manager()

            # 先尝试调用原函数
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"主API {func.__name__} 调用失败: {e}")

            # 尝试降级
            result = manager.call_with_fallback(market, data_type, run_mode, *args, **kwargs)

            if result.success:
                return result.data
            else:
                # 所有降级都失败，抛出异常
                raise Exception(f"API调用失败: {result.error}")

        return wrapper
    return decorator
