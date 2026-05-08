import akshare as ak
import os

from core.base_provider import BaseProvider

# 禁用代理环境变量
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class HKProvider(BaseProvider):
    """
    港股数据源 Provider
    使用 AkShare 获取港股行情数据
    """

    def get_stock_data(self, code: str) -> dict:
        """
        获取港股个股数据
        
        Args:
            code: 股票代码，如 00700.HK 或 00700
        
        Returns:
            dict: 包含价格、涨跌幅等数据
        """
        # 去除后缀
        pure_code = code.replace(".HK", "").strip()
        
        # 确保代码格式正确（港股代码通常为5位）
        pure_code = pure_code.zfill(5)
        
        try:
            df = ak.stock_hk_spot_em()
            
            if df is None or df.empty:
                raise Exception("获取港股行情数据失败")
            
            # 尝试多种匹配方式
            row = df[df["代码"] == pure_code]
            
            if row.empty:
                # 尝试带前缀的代码
                row = df[df["代码"] == f"0{pure_code}"]
            
            if row.empty:
                raise Exception(f"未找到股票: {code}")
            
            return {
                "code": code,
                "name": row["名称"].values[0],
                "price": float(row["最新价"].values[0]),
                "change_pct": float(row["涨跌幅"].values[0]),
                "volume": float(row["成交额"].values[0]),
                "high": float(row["最高"].values[0]),
                "low": float(row["最低"].values[0]),
                "open": float(row["今开"].values[0]),
                "market": "HK",
            }
        except Exception as e:
            # 如果获取失败，返回模拟数据
            return {
                "code": code,
                "name": f"港股股票{code}",
                "price": 0.0,
                "change_pct": 0.0,
                "volume": 0.0,
                "high": 0.0,
                "low": 0.0,
                "open": 0.0,
                "market": "HK",
            }

    def get_market_sentiment(self) -> dict:
        """获取港股市场情绪数据"""
        try:
            df = ak.stock_hk_spot_em()
            
            if df is None or df.empty:
                return {
                    "market": "HK",
                    "up_count": 0,
                    "down_count": 0,
                    "total_stocks": 0,
                }
            
            up_count = len(df[df["涨跌幅"] > 0])
            down_count = len(df[df["涨跌幅"] < 0])
            total_count = len(df)
            
            return {
                "market": "HK",
                "up_count": up_count,
                "down_count": down_count,
                "total_stocks": total_count,
                "up_ratio": up_count / total_count if total_count > 0 else 0.0,
            }
        except Exception:
            return {
                "market": "HK",
                "up_count": 0,
                "down_count": 0,
                "total_stocks": 0,
                "up_ratio": 0.5,
            }

    def get_sectors(self) -> list:
        """获取港股板块数据"""
        try:
            df = ak.stock_hk_board_spot_em()
            
            if df is None or df.empty:
                return []
            
            sectors = []
            for _, row in df.head(10).iterrows():
                sectors.append({
                    "name": row.get("名称", ""),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "market": "HK",
                })
            
            return sectors
        except Exception:
            return []

    def get_market_volume(self) -> float:
        """获取港股全市场成交额（亿元）"""
        try:
            df = ak.stock_hk_spot_em()
            
            if df is None or df.empty:
                return 0.0
            
            return float(df["成交额"].sum() / 100000000)
        except Exception:
            return 0.0
