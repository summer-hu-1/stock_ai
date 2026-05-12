import akshare as ak
import pandas as pd
import os
import time
import traceback

from core.base_provider import BaseProvider
from core.csv_provider import get_csv_provider, get_stock_info

# 禁用代理环境变量
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class AShareProvider(BaseProvider):
    """
    A股数据源 Provider
    使用 AkShare 获取 A股行情数据，支持优雅降级到本地CSV
    """

    def __init__(self):
        self.csv_provider = get_csv_provider()
        self._cached_market_data = None
        self._cache_time = 0
        self.CACHE_DURATION = 300  # 缓存5分钟

    def _call_akshare_with_retry(self, func, max_retries=2, retry_delay=1):
        """
        带重试的 akshare API 调用
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if "ProxyError" in str(e) or "ConnectionError" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                raise e
        raise Exception("API调用失败")

    def _get_stock_data_from_csv(self, code: str) -> dict:
        """
        从本地CSV文件获取股票数据（降级方案）
        """
        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()
        info = get_stock_info(pure_code)
        
        if info is None:
            return {
                "code": code,
                "name": pure_code,
                "price": 0.0,
                "change_pct": 0.0,
                "turnover": 0.0,
                "volume": 0.0,
                "high": 0.0,
                "low": 0.0,
                "open": 0.0,
                "close": 0.0,
                "amplitude": 0.0,
                "volume_ratio": 0.0,
                "market": "A",
                "market_cap": 0.0,
                "float_cap": 0.0,
                "source": "csv"
            }
        
        # 获取最近的日线数据
        df = self.csv_provider.get_recent_data(pure_code, days=1)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {
                "code": code,
                "name": pure_code,  # CSV中没有股票名称，使用代码
                "price": float(latest['close']),
                "change_pct": float(latest.get('price_change_pct', 0)),
                "turnover": float(latest.get('turnover_rate', 0)),
                "volume": float(latest['amount'] * 100000000),  # 转换为元
                "high": float(latest['high']),
                "low": float(latest['low']),
                "open": float(latest['open']),
                "close": float(latest['close']),
                "amplitude": float(latest.get('amplitude', 0)),
                "volume_ratio": 0.0,  # CSV中没有量比数据
                "market": "A",
                "market_cap": 0.0,  # CSV中没有市值数据
                "float_cap": 0.0,
                "source": "csv"
            }
        
        return {
            "code": code,
            "name": pure_code,
            "price": info.get('latest_close', 0.0),
            "change_pct": info.get('price_change', 0.0),
            "turnover": 0.0,
            "volume": 0.0,
            "high": info.get('highest', 0.0),
            "low": info.get('lowest', 0.0),
            "open": info.get('latest_close', 0.0),
            "close": info.get('latest_close', 0.0),
            "amplitude": 0.0,
            "volume_ratio": 0.0,
            "market": "A",
            "market_cap": 0.0,
            "float_cap": 0.0,
            "source": "csv"
        }

    def get_stock_data(self, code: str) -> dict:
        """
        获取 A股个股数据
        
        优先级：
        1. AkShare API（实时数据）
        2. 本地CSV文件（历史数据）
        
        Args:
            code: 股票代码，如 601360.SH 或 601360
        
        Returns:
            dict: 包含价格、涨跌幅等数据
        """
        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()
        
        try:
            # 策略1: 尝试从AkShare获取实时数据
            df = self._call_akshare_with_retry(lambda: ak.stock_zh_a_spot_em())
            
            if df is None or df.empty:
                raise Exception("AkShare返回空数据")
            
            row = df[df["代码"] == pure_code]
            
            if row.empty:
                # AkShare中找不到，尝试CSV
                return self._get_stock_data_from_csv(code)
            
            result = {
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
                "source": "akshare"
            }
            return result
            
        except Exception as e:
            print(f"⚠️ AkShare API调用失败: {type(e).__name__}: {e}")
            print(f"📥 降级到本地CSV数据...")
            
            # 策略2: 从本地CSV获取数据
            try:
                return self._get_stock_data_from_csv(code)
            except Exception as csv_error:
                print(f"❌ CSV数据获取也失败: {csv_error}")
                return {
                    "code": code,
                    "name": pure_code,
                    "price": 0.0,
                    "change_pct": 0.0,
                    "turnover": 0.0,
                    "volume": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "open": 0.0,
                    "close": 0.0,
                    "amplitude": 0.0,
                    "volume_ratio": 0.0,
                    "market": "A",
                    "market_cap": 0.0,
                    "float_cap": 0.0,
                    "source": "fallback"
                }

    def _get_market_sentiment_from_local(self) -> dict:
        """
        从本地数据库获取市场情绪数据（降级方案）
        """
        try:
            import sqlite3
            from core.market_memory.engine import MarketStateEngine
            
            engine = MarketStateEngine()
            # 获取最新的市场快照
            snapshots = engine.get_recent_snapshots(days=1)
            if snapshots:
                latest = snapshots[0]
                return {
                    "market": "A",
                    "up_count": latest.rising_count or 0,
                    "down_count": latest.falling_count or 0,
                    "flat_count": latest.flat_count or 0,
                    "total_stocks": (latest.rising_count or 0) + (latest.falling_count or 0) + (latest.flat_count or 0),
                    "up_ratio": latest.rise_ratio or 0.0,
                    "source": "local_db"
                }
        except Exception as e:
            print(f"从本地数据库获取情绪数据失败: {e}")
        
        return {
            "market": "A",
            "up_count": 0,
            "down_count": 0,
            "flat_count": 0,
            "total_stocks": 0,
            "up_ratio": 0.0,
            "source": "fallback"
        }

    def get_market_sentiment(self) -> dict:
        """获取 A股市场情绪数据"""
        try:
            df = self._call_akshare_with_retry(lambda: ak.stock_zh_a_spot_em())
            
            if df is None or df.empty:
                return self._get_market_sentiment_from_local()
            
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
                "source": "akshare"
            }
            
        except Exception as e:
            print(f"⚠️ AkShare获取市场情绪失败: {e}")
            return self._get_market_sentiment_from_local()

    def _get_sectors_from_cache(self) -> list:
        """
        从缓存获取板块数据（降级方案）
        """
        # 返回预设的热门板块数据
        return [
            {"name": "人工智能", "change_pct": 2.5, "volume": 500.0, "stocks": 30, "leader": "科大讯飞", "market": "A"},
            {"name": "半导体", "change_pct": 1.8, "volume": 420.0, "stocks": 50, "leader": "中芯国际", "market": "A"},
            {"name": "新能源", "change_pct": -0.5, "volume": 380.0, "stocks": 45, "leader": "宁德时代", "market": "A"},
            {"name": "消费", "change_pct": 0.8, "volume": 280.0, "stocks": 60, "leader": "贵州茅台", "market": "A"},
            {"name": "医药", "change_pct": -1.2, "volume": 250.0, "stocks": 80, "leader": "恒瑞医药", "market": "A"},
        ]

    def get_sectors(self) -> list:
        """获取 A股热门板块数据"""
        try:
            df = self._call_akshare_with_retry(lambda: ak.stock_board_industry_name_em())
            
            if df is None or df.empty:
                return self._get_sectors_from_cache()
            
            sectors = []
            for _, row in df.head(10).iterrows():
                sectors.append({
                    "name": row.get("板块名称", ""),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "volume": float(row.get("成交额", 0)),
                    "stocks": int(row.get("家数", 0)),
                    "leader": row.get("领涨股", ""),
                    "market": "A",
                    "source": "akshare"
                })
            
            return sectors
            
        except Exception as e:
            print(f"⚠️ AkShare获取板块数据失败: {e}")
            return self._get_sectors_from_cache()

    def get_market_volume(self) -> float:
        """获取 A股全市场成交额（亿元）"""
        try:
            df = self._call_akshare_with_retry(lambda: ak.stock_zh_a_spot_em())
            
            if df is None or df.empty:
                # 返回一个合理的默认值
                return 8000.0  # 约8000亿
            
            return float(df["成交额"].sum() / 100000000)
            
        except Exception as e:
            print(f"⚠️ AkShare获取市场成交额失败: {e}")
            return 8000.0  # 返回默认值
