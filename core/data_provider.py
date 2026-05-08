import akshare as ak
import pandas as pd
import time
import os
from typing import List

from core.context import MarketContext

# 禁用代理环境变量
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class DataProvider:
    """
    统一数据提供者
    负责从 AkShare 获取所有数据并构建统一的 MarketContext
    """

    _cache = {}
    _cache_time = {}
    _cache_ttl = 60  # 缓存有效期（秒）

    @staticmethod
    def build_context(stock_code: str) -> MarketContext:
        """
        构建完整的市场上下文
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

            # 1. 获取A股实时行情数据
            spot_df = ak.stock_zh_a_spot_em()

            if spot_df is None or spot_df.empty:
                raise Exception("获取行情数据失败")

            # 2. 获取目标股票数据
            stock_row = spot_df[spot_df["代码"] == stock_code]

            if stock_row.empty:
                raise Exception(f"未找到股票: {stock_code}")

            stock_data = {
                "price": float(stock_row["最新价"].values[0]),
                "change_pct": float(stock_row["涨跌幅"].values[0]),
                "turnover": float(stock_row["换手率"].values[0]),
                "volume": float(stock_row["成交额"].values[0]),
                "high": float(stock_row["最高"].values[0]),
                "low": float(stock_row["最低"].values[0]),
                "open": float(stock_row["今开"].values[0]),
                "close": float(stock_row["昨收"].values[0]),
                "amplitude": float(stock_row["振幅"].values[0]),
                "volume_ratio": float(stock_row["量比"].values[0]),
                "market_cap": float(stock_row["总市值"].values[0]) if "总市值" in stock_row.columns else 0.0,
                "float_cap": float(stock_row["流通市值"].values[0]) if "流通市值" in stock_row.columns else 0.0,
            }

            # 3. 计算市场情绪
            up_count = len(spot_df[spot_df["涨跌幅"] > 0])
            down_count = len(spot_df[spot_df["涨跌幅"] < 0])
            flat_count = len(spot_df[spot_df["涨跌幅"] == 0])

            market_sentiment = {
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "up_ratio": up_count / len(spot_df) if len(spot_df) > 0 else 0.0,
                "total_stocks": len(spot_df),
            }

            # 4. 获取热门板块
            sector_df = ak.stock_board_industry_name_em()
            sectors = []
            if sector_df is not None and not sector_df.empty:
                for _, row in sector_df.head(10).iterrows():
                    sectors.append({
                        "name": row.get("板块名称", ""),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交额", 0)),
                        "stocks": int(row.get("家数", 0)),
                        "leader": row.get("领涨股", ""),
                    })

            # 5. 计算全市场成交额（亿元）
            market_volume = float(spot_df["成交额"].sum() / 100000000)

            # 6. 评估风险等级
            risk_level = DataProvider._calculate_risk(
                stock_data["change_pct"],
                stock_data["turnover"],
                market_sentiment["up_ratio"]
            )

            # 7. 获取热门股票
            hot_stocks = DataProvider._get_hot_stocks(spot_df)

            # 构建上下文
            context = MarketContext(
                stock_code=stock_code,
                stock_name=stock_row["名称"].values[0],
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
    def _get_hot_stocks(spot_df: pd.DataFrame) -> List[dict]:
        """
        获取热门股票列表（按成交额排序）
        """
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

    @staticmethod
    def clear_cache():
        """清除缓存"""
        DataProvider._cache.clear()
        DataProvider._cache_time.clear()
        print("🗑️ 缓存已清除")
