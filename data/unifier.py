"""
数据统一接口模块

所有数据访问统一走这里，不再直接访问分散的旧数据库
"""

from typing import Optional, List
import pandas as pd
from .hub import get_datahub
from .adapters.datalake_adapter import get_datalake_adapter


class UnifiedDataProvider:
    """统一数据提供者"""
    
    def __init__(self):
        self.datahub = get_datahub()
        self.datalake = get_datalake_adapter()
        
    def get_ohlcv(self, code: str, market: str = "cn", 
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """获取统一的 OHLCV 数据
        
        优先读取 DataLake (Parquet)，fallback 到 DataHub (CSV)
        """
        try:
            df = self.datalake.get_stock_daily_df(code, market, start_date, end_date)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"从 DataLake 读取失败: {e}")
            
        return self.datahub.get_ohlcv_dataframe(code, market)
    
    def get_latest_market_state(self):
        """获取最新市场状态"""
        return {
            "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "market_cycle": "震荡",
            "sentiment_score": 50.0,
            "risk_level": "中等",
            "hot_sector": "未知",
        }
    
    def get_top_stocks(self, date: Optional[str] = None, limit: int = 20):
        """获取高分股票"""
        try:
            from quant.snapshot_engine import get_snapshot_engine
            engine = get_snapshot_engine()
            return engine.get_top_stocks_by_score(date, limit)
        except Exception:
            return []
    
    def list_available_stocks(self, market: str = "cn") -> List[str]:
        """获取可用股票列表"""
        return self.datalake.list_available_stocks(market)
    
    def get_stock_info(self, code: str, market: str = "cn") -> Optional[dict]:
        """获取股票基本信息"""
        return self.datalake.get_stock_info(code, market)


# 全局实例
_unified_provider = None


def get_unified_provider() -> UnifiedDataProvider:
    """获取全局统一数据提供者"""
    global _unified_provider
    if _unified_provider is None:
        _unified_provider = UnifiedDataProvider()
    return _unified_provider


if __name__ == "__main__":
    print("✅ 数据统一接口模块已加载")
    
    # 测试
    provider = get_unified_provider()
    stocks = provider.list_available_stocks()
    print(f"📊 可用股票数量: {len(stocks)}")
    
    if stocks:
        sample = stocks[0]
        df = provider.get_ohlcv(sample)
        if df is not None:
            print(f"📈 股票 {sample} 数据行数: {len(df)}")