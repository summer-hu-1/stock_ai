import akshare as ak
import pandas as pd
import os

from core.base_provider import BaseProvider

# 禁用代理环境变量
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class AShareProvider(BaseProvider):
    """
    A股数据源 Provider
    使用 AkShare 获取 A股行情数据
    """

    def get_stock_data(self, code: str) -> dict:
        """
        获取 A股个股数据
        
        Args:
            code: 股票代码，如 601360.SH 或 601360
        
        Returns:
            dict: 包含价格、涨跌幅等数据
        """
        # 去除后缀
        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()
        
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            raise Exception("获取A股行情数据失败")
        
        row = df[df["代码"] == pure_code]
        
        if row.empty:
            raise Exception(f"未找到股票: {code}")
        
        return {
            "code": code,
            "name": row["名称"].values[0],
            "price": float(row["最新价"].values[0]),
            "change_pct": float(row["涨跌幅"].values[0]),
            "turnover": float(row["换手率"].values[0]),
            "volume": float(row["成交额"].values[0]),
            "high": float(row["最高"].values[0]),
            "low": float(row["最低"].values[0]),
            "open": float(row["今开"].values[0]),
            "close": float(row["昨收"].values[0]),
            "amplitude": float(row["振幅"].values[0]),
            "volume_ratio": float(row["量比"].values[0]),
            "market": "A",
            "market_cap": float(row["总市值"].values[0]) if "总市值" in row.columns else 0.0,
            "float_cap": float(row["流通市值"].values[0]) if "流通市值" in row.columns else 0.0,
        }

    def get_market_sentiment(self) -> dict:
        """获取 A股市场情绪数据"""
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            return {
                "market": "A",
                "up_count": 0,
                "down_count": 0,
                "flat_count": 0,
                "total_stocks": 0,
                "up_ratio": 0.0,
            }
        
        up_count = len(df[df["涨跌幅"] > 0])
        down_count = len(df[df["涨跌幅"] < 0])
        flat_count = len(df[df["涨跌幅"] == 0])
        total_count = len(df)
        
        return {
            "market": "A",
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "total_stocks": total_count,
            "up_ratio": up_count / total_count if total_count > 0 else 0.0,
        }

    def get_sectors(self) -> list:
        """获取 A股热门板块数据"""
        df = ak.stock_board_industry_name_em()
        
        if df is None or df.empty:
            return []
        
        sectors = []
        for _, row in df.head(10).iterrows():
            sectors.append({
                "name": row.get("板块名称", ""),
                "change_pct": float(row.get("涨跌幅", 0)),
                "volume": float(row.get("成交额", 0)),
                "stocks": int(row.get("家数", 0)),
                "leader": row.get("领涨股", ""),
                "market": "A",
            })
        
        return sectors

    def get_market_volume(self) -> float:
        """获取 A股全市场成交额（亿元）"""
        df = ak.stock_zh_a_spot_em()
        
        if df is None or df.empty:
            return 0.0
        
        return float(df["成交额"].sum() / 100000000)
