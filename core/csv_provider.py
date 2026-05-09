#!/usr/bin/env python3
"""
CSV数据提供者 - 从本地CSV文件读取股票数据

提供统一的接口供Agent读取A股日线数据
"""

import os
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, timedelta


class CSVProvider:
    """CSV数据提供者类"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化CSVProvider
        
        Args:
            data_dir: 数据目录路径，默认为 data/cn/daily
        """
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(script_dir)
            data_dir = os.path.join(project_dir, "data", "cn", "daily")
        
        self.data_dir = data_dir
    
    def get_stock_daily(self, code: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据
        
        Args:
            code: 股票代码 (如: "000002", "600519")
            start_date: 开始日期 (格式: "YYYY-MM-DD" 或 "YYYYMMDD")
            end_date: 结束日期 (格式: "YYYY-MM-DD" 或 "YYYYMMDD")
        
        Returns:
            DataFrame: 包含日线数据的DataFrame，失败返回None
        
        CSV列:
            date, open, high, low, close, volume, amount, 
            amplitude, price_change_pct, turnover_rate
        """
        code = str(code).zfill(6)
        path = os.path.join(self.data_dir, f"{code}.csv")
        
        if not os.path.exists(path):
            return None
        
        try:
            df = pd.read_csv(path)
            
            # 转换日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                
                # 日期过滤
                if start_date:
                    start_date = self._parse_date(start_date)
                    df = df[df['date'] >= start_date]
                
                if end_date:
                    end_date = self._parse_date(end_date)
                    df = df[df['date'] <= end_date]
            
            return df
            
        except Exception as e:
            print(f"读取股票 {code} 数据失败: {e}")
            return None
    
    def get_stock_info(self, code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
        
        Returns:
            Dict: 包含股票基本信息的字典
        """
        df = self.get_stock_daily(code)
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        earliest = df.iloc[0]
        
        # 计算统计信息
        price_change = ((latest['close'] - earliest['close']) / earliest['close'] * 100) if earliest['close'] > 0 else 0
        
        return {
            'code': code,
            'latest_date': str(latest['date'].date()) if hasattr(latest['date'], 'date') else str(latest['date'])[:10],
            'latest_close': latest['close'],
            'earliest_date': str(earliest['date'].date()) if hasattr(earliest['date'], 'date') else str(earliest['date'])[:10],
            'earliest_close': earliest['close'],
            'price_change': round(price_change, 2),
            'total_days': len(df),
            'highest': df['high'].max(),
            'lowest': df['low'].min(),
            'avg_volume': df['volume'].mean(),
            'latest_close_date': str(latest['date'])[:10]
        }
    
    def get_stock_list(self) -> List[str]:
        """
        获取本地已有的股票代码列表
        
        Returns:
            List[str]: 股票代码列表
        """
        if not os.path.exists(self.data_dir):
            return []
        
        files = os.listdir(self.data_dir)
        codes = [f.replace('.csv', '') for f in files if f.endswith('.csv')]
        return sorted(codes)
    
    def get_latest_trading_date(self, code: str) -> Optional[str]:
        """
        获取指定股票的最新交易日期
        
        Args:
            code: 股票代码
        
        Returns:
            str: 最新交易日期 (格式: YYYY-MM-DD)
        """
        df = self.get_stock_daily(code)
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        return str(latest['date'])[:10]
    
    def get_recent_data(self, code: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        获取最近N个交易日的日线数据
        
        Args:
            code: 股票代码
            days: 天数
        
        Returns:
            DataFrame: 最近N天的日线数据
        """
        df = self.get_stock_daily(code)
        if df is None or df.empty:
            return None
        
        return df.tail(days)
    
    def search_stocks(self, keyword: str) -> List[Dict]:
        """
        搜索本地已下载的股票
        
        Args:
            keyword: 搜索关键词（股票代码或名称的一部分）
        
        Returns:
            List[Dict]: 匹配的股票列表
        """
        stock_list_path = os.path.join(os.path.dirname(self.data_dir), "stock_list.csv")
        
        if not os.path.exists(stock_list_path):
            return []
        
        try:
            df = pd.read_csv(stock_list_path)
            keyword = keyword.lower()
            
            # 搜索匹配
            mask = df['code'].astype(str).str.lower().str.contains(keyword) | \
                   df['name'].str.lower().str.contains(keyword)
            
            results = []
            for _, row in df[mask].iterrows():
                code = str(row['code']).zfill(6)
                info = self.get_stock_info(code)
                results.append({
                    'code': code,
                    'name': row['name'],
                    'has_data': info is not None
                })
            
            return results
            
        except Exception as e:
            print(f"搜索股票失败: {e}")
            return []
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """解析日期字符串"""
        if isinstance(date_str, datetime):
            return date_str
        
        date_str = str(date_str).replace('-', '')
        if len(date_str) == 8:
            return datetime.strptime(date_str, '%Y%m%d')
        return datetime.strptime(date_str[:10], '%Y-%m-%d')
    
    def get_data_status(self) -> Dict:
        """
        获取本地数据状态
        
        Returns:
            Dict: 包含数据统计信息的字典
        """
        stocks = self.get_stock_list()
        
        status = {
            'total_stocks': len(stocks),
            'data_dir': self.data_dir,
            'exists': os.path.exists(self.data_dir)
        }
        
        if not stocks:
            return status
        
        # 获取最新和最旧的日期
        latest_dates = []
        for code in stocks[:100]:
            latest = self.get_latest_trading_date(code)
            if latest:
                latest_dates.append(latest)
        
        if latest_dates:
            status['latest_update'] = max(latest_dates)
            status['earliest_update'] = min(latest_dates)
        
        return status


# 全局便捷函数
_csv_provider = None

def get_csv_provider() -> CSVProvider:
    """获取CSVProvider单例"""
    global _csv_provider
    if _csv_provider is None:
        _csv_provider = CSVProvider()
    return _csv_provider


def get_stock_daily(code: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """便捷函数：获取股票日线数据"""
    return get_csv_provider().get_stock_daily(code, start_date, end_date)


def get_stock_info(code: str) -> Optional[Dict]:
    """便捷函数：获取股票信息"""
    return get_csv_provider().get_stock_info(code)


def get_recent_data(code: str, days: int = 30) -> Optional[pd.DataFrame]:
    """便捷函数：获取最近N天数据"""
    return get_csv_provider().get_recent_data(code, days)