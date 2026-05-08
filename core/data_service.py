"""
统一数据服务入口
整合市场选择、股票解析、数据获取、上下文构建

核心设计：
1. 统一的用户入口：市场 + 搜索关键词
2. 自动解析股票名称/代码
3. 自动选择数据源 Provider
4. 构建统一的 MarketContext
"""

import time
from typing import Optional

from core.market_registry import MARKETS, get_market_config
from core.symbol_resolver import SymbolResolver
from core.provider_factory import ProviderFactory
from core.context import MarketContext


class DataService:
    """
    统一数据服务
    
    提供单一入口：选择市场 + 搜索股票 → 获取 MarketContext
    
    使用示例：
        service = DataService("A股")
        context = service.build_context("贵州茅台")
        if context:
            print(f"股票: {context.stock_name}")
    """

    _cache = {}
    _cache_time = {}
    _cache_ttl = 60  # 缓存有效期（秒）

    def __init__(self, market_name: str):
        """
        初始化数据服务
        
        Args:
            market_name: 市场名称，如 "A股", "港股", "美股"
        """
        self.market_name = market_name
        self.market_config = get_market_config(market_name)
        
        if not self.market_config:
            raise ValueError(f"不支持的市场: {market_name}")
        
        # 初始化解析器和 Provider
        self.resolver = SymbolResolver(self.market_config)
        self.provider = ProviderFactory.get_provider(market_name)

    def build_context(self, query: str) -> Optional[MarketContext]:
        """
        构建市场上下文
        
        Args:
            query: 股票名称或代码（如 "贵州茅台", "600519", "AAPL"）
            
        Returns:
            MarketContext: 统一的市场上下文对象，未找到返回 None
        """
        cache_key = f"{self.market_name}_{query}"
        current_time = time.time()

        # 检查缓存
        if cache_key in DataService._cache:
            if current_time - DataService._cache_time.get(cache_key, 0) < DataService._cache_ttl:
                print(f"📦 使用缓存: {cache_key}")
                return DataService._cache[cache_key]

        try:
            print(f"🔄 正在构建 Context: {self.market_name} - {query}")

            # 1. 解析股票（名称 → 代码）
            stock_info = self._resolve_stock(query)
            
            if not stock_info:
                print(f"❌ 未找到股票: {query}")
                return None
            
            code = stock_info["code"]
            name = stock_info["name"]
            print(f"📍 解析结果: {name} ({code})")

            # 2. 添加市场后缀
            code_with_suffix = self._add_market_suffix(code)

            # 3. 从 Provider 获取数据
            stock_data = self.provider.get_stock_data(code_with_suffix)
            sentiment = self.provider.get_market_sentiment()
            sectors = self.provider.get_sectors()
            market_volume = self.provider.get_market_volume()

            # 4. 计算风险等级
            risk_level = self._calculate_risk(
                stock_data.get("change_pct", 0),
                stock_data.get("turnover", 0),
                sentiment.get("up_ratio", 0.5)
            )

            # 5. 构建统一上下文
            context = MarketContext(
                stock_code=code,
                stock_name=name,
                stock_data=stock_data,
                market_sentiment=sentiment,
                sectors=sectors,
                market_volume=market_volume,
                risk_level=risk_level,
                hot_stocks=[],
            )

            # 缓存
            DataService._cache[cache_key] = context
            DataService._cache_time[cache_key] = current_time

            print(f"✅ Context 构建成功: {name}")
            return context

        except Exception as e:
            print(f"❌ 构建 Context 失败: {e}")
            return None

    def _resolve_stock(self, query: str) -> Optional[dict]:
        """
        解析股票查询
        
        优先级：
        1. 首先尝试精确代码匹配
        2. 然后尝试名称模糊搜索
        3. 如果数据库为空，直接返回输入作为代码
        """
        # 尝试解析
        result = self.resolver.resolve(query)
        
        if result:
            return result
        
        # 如果数据库中没有，检查是否是纯数字代码（可能未收录）
        if query.isdigit():
            # 尝试直接使用输入作为代码
            return {
                "code": query,
                "name": query  # 临时使用代码作为名称
            }
        
        return None

    def _add_market_suffix(self, code: str) -> str:
        """
        根据市场添加代码后缀
        
        A股: 600519 → 600519.SH
        港股: 00700 → 00700.HK
        美股: AAPL → AAPL（保持原样）
        """
        suffix = self.market_config.get("suffix", "")
        
        if suffix and not code.upper().endswith(suffix.upper()):
            return code + suffix
        
        return code

    def _calculate_risk(self, change_pct: float, turnover: float, up_ratio: float) -> str:
        """
        根据行情数据评估风险等级
        """
        score = 0

        # 个股涨跌幅度
        if abs(change_pct) > 9:
            score += 30
        elif abs(change_pct) > 5:
            score += 15

        # 换手率
        if turnover > 20:
            score += 25
        elif turnover > 10:
            score += 15

        # 市场情绪
        if up_ratio < 0.3:
            score += 20
        elif up_ratio > 0.7:
            score += 10

        if score >= 60:
            return "高"
        elif score >= 30:
            return "中"
        else:
            return "低"

    def resolve_stock(self, query: str) -> Optional[dict]:
        """
        解析股票查询，返回股票信息
        
        Args:
            query: 股票名称或代码
            
        Returns:
            股票信息字典，未找到返回 None
        """
        return self.resolver.resolve(query)

    def search_stocks(self, keyword: str, limit: int = 10) -> list:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            股票列表
        """
        return self.resolver.search(keyword, limit)

    @staticmethod
    def clear_cache():
        """清除全局缓存"""
        DataService._cache.clear()
        DataService._cache_time.clear()
        print("🗑️ 数据服务缓存已清除")
