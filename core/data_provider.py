import time

from core.context import MarketContext
from core.provider_factory import ProviderFactory


class DataProvider:
    """
    统一数据提供者（多市场支持）
    负责根据股票代码自动选择数据源并构建统一的 MarketContext
    
    支持市场：
    - A股: 代码以 .SZ 或 .SH 结尾
    - 港股: 代码以 .HK 结尾  
    - 美股: 其他格式
    
    核心设计：
    1. 使用 ProviderFactory 自动选择数据源
    2. 所有数据通过统一接口获取
    3. 构建统一的 MarketContext 供所有 Agent 使用
    """

    _cache = {}
    _cache_time = {}
    _cache_ttl = 60  # 缓存有效期（秒）

    @staticmethod
    def build_context(stock_code: str) -> MarketContext:
        """
        构建完整的市场上下文（多市场支持）
        
        Args:
            stock_code: 股票代码，支持多种格式
                        A股: 601360.SH, 000002.SZ
                        港股: 00700.HK
                        美股: AAPL, MSFT
        
        Returns:
            MarketContext: 统一的市场上下文对象
        """
        cache_key = f"context_{stock_code}"
        current_time = time.time()

        # 检查缓存
        if cache_key in DataProvider._cache:
            if current_time - DataProvider._cache_time.get(cache_key, 0) < DataProvider._cache_ttl:
                print(f"📦 使用缓存的 MarketContext: {stock_code}")
                return DataProvider._cache[cache_key]

        try:
            print(f"🔄 正在构建 MarketContext: {stock_code}")

            # 1. 根据股票代码获取对应的 Provider
            provider = ProviderFactory.get_provider(stock_code)
            market_type = ProviderFactory.detect_market(stock_code)
            
            print(f"📍 检测到市场类型: {market_type}")

            # 2. 获取个股数据
            stock_data = provider.get_stock_data(stock_code)
            stock_name = stock_data.get("name", stock_code)

            # 3. 获取市场情绪
            market_sentiment = provider.get_market_sentiment()

            # 4. 获取板块数据
            sectors = provider.get_sectors()

            # 5. 获取全市场成交额
            market_volume = provider.get_market_volume()

            # 6. 评估风险等级
            risk_level = DataProvider._calculate_risk(
                stock_data.get("change_pct", 0),
                stock_data.get("turnover", 0),
                market_sentiment.get("up_ratio", 0.5)
            )

            # 7. 获取热门股票（仅A股支持）
            hot_stocks = []
            if market_type == "A":
                hot_stocks = DataProvider._get_hot_stocks()

            # 构建上下文
            context = MarketContext(
                stock_code=stock_code,
                stock_name=stock_name,
                stock_data=stock_data,
                market_sentiment=market_sentiment,
                sectors=sectors,
                market_volume=market_volume,
                risk_level=risk_level,
                hot_stocks=hot_stocks,
            )

            # 缓存
            DataProvider._cache[cache_key] = context
            DataProvider._cache_time[cache_key] = current_time

            print(f"✅ MarketContext 构建成功: {stock_code}")
            return context

        except Exception as e:
            print(f"❌ 构建 MarketContext 失败: {e}")
            raise

    @staticmethod
    def _calculate_risk(change_pct: float, turnover: float, up_ratio: float) -> str:
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

    @staticmethod
    def _get_hot_stocks() -> list:
        """
        获取热门股票列表（按成交额排序）- 仅A股
        """
        import akshare as ak
        import pandas as pd
        
        try:
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is None or spot_df.empty:
                return []
            
            hot_df = spot_df.sort_values("成交额", ascending=False).head(10)
            hot_stocks = []
            for _, row in hot_df.iterrows():
                hot_stocks.append({
                    "code": row["代码"],
                    "name": row["名称"],
                    "price": float(row["最新价"]),
                    "change_pct": float(row["涨跌幅"]),
                    "volume": float(row["成交额"]),
                })
            return hot_stocks
        except Exception:
            return []

    @staticmethod
    def clear_cache():
        """清除缓存"""
        DataProvider._cache.clear()
        DataProvider._cache_time.clear()
        print("🗑️ 缓存已清除")
