"""
Data Lake 工具模块 - K线数据存储引擎

使用 Parquet 格式存储海量K线数据：
- 超轻量
- 超快查询
- pandas/pyarrow 原生支持
- 支持分区查询

目录结构：
data_lake/
├── cn/
│   ├── daily/
│   │   ├── 000001.parquet
│   │   ├── 000002.parquet
│   │   └── ...
│   └── minute/
├── hk/
└── us/
"""

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

class DataLake:
    """数据湖核心类"""
    
    def __init__(self, base_path: str = None):
        if base_path:
            self.base_path = base_path
        else:
            self.base_path = os.path.join(
                os.path.dirname(__file__), '..', 'data_lake'
            )
        os.makedirs(self.base_path, exist_ok=True)
    
    def _get_market_path(self, market: str, freq: str) -> str:
        """获取市场数据路径"""
        path = os.path.join(self.base_path, market, freq)
        os.makedirs(path, exist_ok=True)
        return path
    
    def _get_code_file(self, market: str, freq: str, code: str) -> str:
        """获取股票文件路径"""
        path = self._get_market_path(market, freq)
        return os.path.join(path, f"{code}.parquet")
    
    def save_daily_data(self, code: str, market: str, df: pd.DataFrame):
        """
        保存每日K线数据到数据湖
        
        Args:
            code: 股票代码
            market: 市场 (cn/hk/us)
            df: 包含 date, open, high, low, close, volume, amount 的DataFrame
        """
        file_path = self._get_code_file(market, "daily", code)
        
        # 确保数据格式正确
        df = df.copy()
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # 转换为 PyArrow Table
        table = pa.Table.from_pandas(df)
        
        # 写入 Parquet 文件
        pq.write_table(table, file_path)
    
    def load_daily_data(self, code: str, market: str, 
                        start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        从数据湖加载每日K线数据
        
        Args:
            code: 股票代码
            market: 市场 (cn/hk/us)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            DataFrame 或空DataFrame
        """
        file_path = self._get_code_file(market, "daily", code)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        # 读取 Parquet 文件
        table = pq.read_table(file_path)
        df = table.to_pandas()
        
        # 日期过滤
        if 'date' in df.columns:
            if start_date:
                df = df[df['date'] >= start_date]
            if end_date:
                df = df[df['date'] <= end_date]
        
        return df.sort_values('date').reset_index(drop=True)
    
    def save_minute_data(self, code: str, market: str, df: pd.DataFrame):
        """保存分钟K线数据"""
        file_path = self._get_code_file(market, "minute", code)
        
        df = df.copy()
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        table = pa.Table.from_pandas(df)
        pq.write_table(table, file_path)
    
    def load_minute_data(self, code: str, market: str, 
                         start_time: str = None, end_time: str = None) -> pd.DataFrame:
        """加载分钟K线数据"""
        file_path = self._get_code_file(market, "minute", code)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        table = pq.read_table(file_path)
        df = table.to_pandas()
        
        if 'datetime' in df.columns and start_time:
            df = df[df['datetime'] >= start_time]
        if 'datetime' in df.columns and end_time:
            df = df[df['datetime'] <= end_time]
        
        return df.sort_values('datetime').reset_index(drop=True)
    
    def list_stocks(self, market: str, freq: str = "daily") -> list:
        """列出指定市场的所有股票"""
        path = self._get_market_path(market, freq)
        stocks = []
        
        for filename in os.listdir(path):
            if filename.endswith('.parquet'):
                code = filename.replace('.parquet', '')
                stocks.append(code)
        
        return sorted(stocks)
    
    def get_stock_count(self, market: str, freq: str = "daily") -> int:
        """获取指定市场的股票数量"""
        return len(self.list_stocks(market, freq))
    
    def update_daily_data(self, code: str, market: str, new_df: pd.DataFrame):
        """
        更新每日数据（追加或更新）
        
        如果文件已存在，合并新数据并去重
        """
        file_path = self._get_code_file(market, "daily", code)
        
        if os.path.exists(file_path):
            # 读取现有数据
            existing_df = self.load_daily_data(code, market)
            
            # 合并并去重
            combined_df = pd.concat([existing_df, new_df])
            combined_df = combined_df.drop_duplicates(subset='date', keep='last')
        else:
            combined_df = new_df
        
        # 保存合并后的数据
        self.save_daily_data(code, market, combined_df)
    
    def delete_stock_data(self, code: str, market: str, freq: str = "daily"):
        """删除指定股票的数据"""
        file_path = self._get_code_file(market, freq, code)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def get_data_range(self, code: str, market: str, freq: str = "daily") -> tuple:
        """获取数据的日期范围"""
        df = self.load_daily_data(code, market)
        
        if df.empty or 'date' not in df.columns:
            return None, None
        
        return df['date'].min(), df['date'].max()
    
    def get_latest_date(self, market: str, freq: str = "daily") -> str:
        """获取市场最新数据日期"""
        latest_date = None
        stocks = self.list_stocks(market, freq)
        
        for code in stocks:
            start, end = self.get_data_range(code, market, freq)
            if end and (not latest_date or end > latest_date):
                latest_date = end
        
        return latest_date

# 全局实例
_data_lake = None

def get_data_lake() -> DataLake:
    """获取全局数据湖实例"""
    global _data_lake
    if _data_lake is None:
        _data_lake = DataLake()
    return _data_lake

# 示例用法
if __name__ == "__main__":
    lake = get_data_lake()
    
    # 示例：创建测试数据
    test_data = pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'open': [10.0, 10.2, 10.1],
        'high': [10.5, 10.4, 10.3],
        'low': [9.8, 10.0, 9.9],
        'close': [10.2, 10.1, 10.0],
        'volume': [10000, 12000, 8000],
        'amount': [102000, 121200, 80000]
    })
    
    # 保存测试数据
    lake.save_daily_data('000001', 'cn', test_data)
    print("✅ 测试数据保存成功")
    
    # 加载测试数据
    loaded_df = lake.load_daily_data('000001', 'cn')
    print("📊 加载的数据:")
    print(loaded_df)
    
    # 列出股票
    stocks = lake.list_stocks('cn')
    print(f"\n📈 市场股票数量: {len(stocks)}")