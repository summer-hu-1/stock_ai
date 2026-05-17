"""
DataLake 统一数据访问接口

提供统一的 OHLCV 数据访问能力，支持 Parquet 格式存储
"""

from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import os
import pandas as pd
from pathlib import Path

from ..models import OHLCV


class DataLakeAdapter:
    """
    DataLake 统一数据适配器
    
    提供统一的股票数据访问接口，支持多市场数据读取
    """
    
    MARKET_MAP = {
        "cn": "cn/daily",
        "hk": "hk/daily",
        "us": "us/daily"
    }
    
    EXCHANGE_MAP = {
        '000': 'SZ', '001': 'SZ', '002': 'SZ', '003': 'SZ',
        '300': 'SZ', '301': 'SZ',
        '600': 'SH', '601': 'SH', '603': 'SH', '605': 'SH',
        '688': 'SH', '689': 'SH',
    }
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_dir = os.path.dirname(os.path.dirname(script_dir))
            self.base_dir = Path(project_dir) / "datalake"
        else:
            self.base_dir = Path(base_dir)
    
    def _get_exchange(self, code: str) -> str:
        """根据股票代码获取交易所"""
        prefix = code[:3]
        return self.EXCHANGE_MAP.get(prefix, 'UNKNOWN')
    
    def _get_data_path(self, code: str, market: str = "cn") -> Path:
        """获取数据文件路径"""
        market_path = self.MARKET_MAP.get(market, "cn/daily")
        exchange = self._get_exchange(code)
        return self.base_dir / market_path / exchange / f"{code}.parquet"
    
    def get_stock_daily(
        self,
        code: str,
        market: str = "cn",
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None
    ) -> List[OHLCV]:
        """
        获取股票日线数据
        
        Args:
            code: 股票代码
            market: 市场类型 (cn/hk/us)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            OHLCV 对象列表
        """
        code = str(code).zfill(6)
        path = self._get_data_path(code, market)
        
        if not path.exists():
            return []
        
        try:
            df = pd.read_parquet(path)
            
            # 日期过滤
            if start_date:
                start_date = self._parse_date(start_date)
                df = df[df['date'] >= start_date]
            
            if end_date:
                end_date = self._parse_date(end_date)
                df = df[df['date'] <= end_date]
            
            return self._df_to_ohlcv(df, code)
            
        except Exception as e:
            print(f"读取股票 {code} 数据失败：{e}")
            return []
    
    def get_stock_daily_df(
        self,
        code: str,
        market: str = "cn",
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据（DataFrame格式）
        
        Args:
            code: 股票代码
            market: 市场类型 (cn/hk/us)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame 或 None
        """
        code = str(code).zfill(6)
        path = self._get_data_path(code, market)
        
        if not path.exists():
            return None
        
        try:
            df = pd.read_parquet(path)
            
            if start_date:
                start_date = self._parse_date(start_date)
                df = df[df['date'] >= start_date]
            
            if end_date:
                end_date = self._parse_date(end_date)
                df = df[df['date'] <= end_date]
            
            return df
            
        except Exception as e:
            print(f"读取股票 {code} 数据失败：{e}")
            return None
    
    def _df_to_ohlcv(self, df: pd.DataFrame, code: str) -> List[OHLCV]:
        """将DataFrame转换为OHLCV对象列表"""
        result = []
        for _, row in df.iterrows():
            try:
                ohlcv = OHLCV(
                    code=code,
                    date=row.get('date', datetime.now()),
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=float(row.get('close', 0)),
                    volume=float(row.get('volume', 0)),
                    amount=float(row.get('amount', 0)),
                    turnover_rate=float(row.get('turnover_rate', 0)),
                    price_change_pct=float(row.get('change_pct', 0)),
                    amplitude=float(row.get('amplitude', 0))
                )
                result.append(ohlcv)
            except Exception:
                continue
        return result
    
    def _parse_date(self, date: Union[str, datetime]) -> datetime:
        """解析日期"""
        if isinstance(date, datetime):
            return date
        if isinstance(date, str):
            date = date.replace("/", "-")
            for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S"]:
                try:
                    return datetime.strptime(date, fmt)
                except ValueError:
                    continue
        return datetime.now()
    
    def list_available_stocks(self, market: str = "cn") -> List[str]:
        """
        获取可用股票列表
        
        Args:
            market: 市场类型
            
        Returns:
            股票代码列表
        """
        market_path = self.MARKET_MAP.get(market, "cn/daily")
        market_dir = self.base_dir / market_path
        
        if not market_dir.exists():
            return []
        
        codes = []
        for exchange_dir in market_dir.iterdir():
            if exchange_dir.is_dir():
                for file in exchange_dir.iterdir():
                    if file.suffix == '.parquet':
                        codes.append(file.stem)
        
        return sorted(codes)
    
    def get_metadata(self, market: str = "cn") -> Optional[Dict[str, Any]]:
        """
        获取市场元数据
        
        Args:
            market: 市场类型
            
        Returns:
            元数据字典或None
        """
        market_path = self.MARKET_MAP.get(market, "cn/daily")
        metadata_path = self.base_dir / market_path / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            import json
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取元数据失败：{e}")
            return None
    
    def get_stock_info(self, code: str, market: str = "cn") -> Optional[dict]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
            market: 市场类型
            
        Returns:
            股票信息字典或None
        """
        df = self.get_stock_daily_df(code, market)
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        return {
            "code": code,
            "name": code,
            "market": market,
            "exchange": self._get_exchange(code),
            "price": float(latest['close']),
            "change_pct": float(latest.get('change_pct', 0)),
            "volume": float(latest['volume']),
            "turnover_rate": float(latest.get('turnover_rate', 0)),
            "amount": float(latest['amount']),
        }


# 全局实例
_data_lake_adapter = None


def get_datalake_adapter() -> DataLakeAdapter:
    """获取全局DataLake适配器实例"""
    global _data_lake_adapter
    if _data_lake_adapter is None:
        _data_lake_adapter = DataLakeAdapter()
    return _data_lake_adapter