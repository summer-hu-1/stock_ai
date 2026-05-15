"""
数据统一接口模块

所有数据访问统一走这里，不再直接访问分散的旧数据库
"""

from typing import Optional, List
from data.hub import get_datahub
from data_lake import get_data_lake
from database.market_db import get_db, DailyBar, MarketState


class UnifiedDataProvider:
    """统一数据提供者"""
    
    def __init__(self):
        self.datahub = get_datahub()
        self.data_lake = get_data_lake()
        self.db = next(get_db())
        
    def get_ohlcv(self, code: str, market: str = "cn", 
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None):
        """获取统一的 OHLCV 数据
        
        优先读取 DataLake (Parquet)，fallback 到 DataHub
        """
        try:
            df = self.data_lake.load_daily_data(code, market, start_date, end_date)
            if not df.empty:
                return df
        except Exception:
            pass
            
        return self.datahub.get_ohlcv_dataframe(code, market)
    
    def get_latest_market_state(self):
        """获取最新市场状态"""
        from database.market_db import MarketState
        
        state = self.db.query(MarketState).order_by(
            MarketState.date.desc()
        ).first()
        
        if state:
            return {
                "date": state.date,
                "market_cycle": state.market_cycle,
                "sentiment_score": state.sentiment_score,
                "risk_level": state.risk_level,
                "hot_sector": state.hot_sector,
            }
        return None
    
    def get_top_stocks(self, date: Optional[str] = None, limit: int = 20):
        """获取高分股票"""
        from quant.snapshot_engine import get_snapshot_engine
        
        engine = get_snapshot_engine()
        return engine.get_top_stocks_by_score(date, limit)


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
