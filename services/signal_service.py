"""信号服务 - 提供信号查询接口"""

import sqlite3
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List

# 获取项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_DIR, "storage", "sqlite", "signals.db")


class SignalService:
    """信号服务 - 提供信号查询和分析功能"""

    def __init__(self):
        # 确保数据库存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def get_signals(self, code: str = None, date: str = None, limit: int = 100) -> pd.DataFrame:
        """
        获取信号数据
        
        Args:
            code: 股票代码，不传则获取所有
            date: 日期，不传则获取所有
            limit: 返回数量限制
        
        Returns:
            DataFrame: 信号数据
        """
        conn = sqlite3.connect(DB_PATH)
        
        query = "SELECT * FROM signals WHERE 1=1 "
        params = []
        
        if code:
            query += "AND code = ? "
            params.append(code)
        
        if date:
            query += "AND date = ? "
            params.append(date)
        
        query += "ORDER BY date DESC, strength DESC LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql(query, conn, params=params)
        
        conn.close()
        
        return df

    def get_today_signals(self) -> pd.DataFrame:
        """获取今日信号"""
        today = datetime.today().strftime("%Y-%m-%d")
        return self.get_signals(date=today)

    def get_stock_signals(self, code: str) -> pd.DataFrame:
        """获取指定股票的所有信号"""
        return self.get_signals(code=code)

    def get_top_signals(self, limit: int = 20, min_strength: float = 0.7) -> pd.DataFrame:
        """获取高强度信号"""
        conn = sqlite3.connect(DB_PATH)
        
        query = """
            SELECT * FROM signals 
            WHERE strength >= ? 
            ORDER BY strength DESC 
            LIMIT ?
        """
        
        df = pd.read_sql(query, conn, params=[min_strength, limit])
        
        conn.close()
        
        return df

    def get_leaders(self) -> pd.DataFrame:
        """获取龙头股列表"""
        conn = sqlite3.connect(DB_PATH)
        
        query = """
            SELECT * FROM leaders 
            ORDER BY leader_score DESC
        """
        
        df = pd.read_sql(query, conn)
        
        conn.close()
        
        return df

    def get_watchlist(self) -> pd.DataFrame:
        """获取关注列表"""
        conn = sqlite3.connect(DB_PATH)
        
        query = """
            SELECT * FROM watchlist 
            ORDER BY priority, added_at DESC
        """
        
        df = pd.read_sql(query, conn)
        
        conn.close()
        
        return df

    def get_signal_summary(self) -> Dict:
        """获取信号统计摘要"""
        today = datetime.today().strftime("%Y-%m-%d")
        df = self.get_signals(date=today)
        
        if df.empty:
            return {
                "total_signals": 0,
                "up_signals": 0,
                "down_signals": 0,
                "avg_strength": 0,
                "top_stocks": []
            }
        
        return {
            "total_signals": len(df),
            "up_signals": len(df[df["direction"] == "up"]),
            "down_signals": len(df[df["direction"] == "down"]),
            "avg_strength": round(df["strength"].mean(), 2),
            "top_stocks": df.sort_values("strength", ascending=False)["code"].head(5).tolist()
        }


# 全局单例
_signal_service_instance = None

def get_signal_service() -> SignalService:
    """获取信号服务单例"""
    global _signal_service_instance
    if _signal_service_instance is None:
        _signal_service_instance = SignalService()
    return _signal_service_instance