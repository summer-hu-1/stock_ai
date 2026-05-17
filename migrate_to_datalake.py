#!/usr/bin/env python3
"""
数据迁移脚本：将CSV数据迁移到DataLake (Parquet格式)

运行方式：python migrate_to_datalake.py
"""

import os
import pandas as pd
from pathlib import Path

# 配置
CURRENT_DATA_DIR = Path(__file__).parent / "data" / "cn" / "daily"
DATALAKE_DIR = Path(__file__).parent / "datalake" / "cn" / "daily"

# 股票代码前缀映射到交易所
EXCHANGE_MAP = {
    '000': 'SZ',  # 深圳主板
    '001': 'SZ',  # 深圳主板
    '002': 'SZ',  # 深圳中小板
    '003': 'SZ',  # 深圳主板
    '300': 'SZ',  # 深圳创业板
    '301': 'SZ',  # 深圳创业板
    '600': 'SH',  # 上海主板
    '601': 'SH',  # 上海主板
    '603': 'SH',  # 上海主板
    '605': 'SH',  # 上海主板
    '688': 'SH',  # 上海科创板
    '689': 'SH',  # 上海科创板
}


def get_exchange(code: str) -> str:
    """根据股票代码获取交易所"""
    prefix = code[:3]
    return EXCHANGE_MAP.get(prefix, 'UNKNOWN')


def migrate_csv_to_parquet():
    """迁移CSV文件到Parquet格式"""
    # 创建DataLake目录
    DATALAKE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 收集所有CSV文件
    csv_files = []
    
    # 扫描主目录
    for item in CURRENT_DATA_DIR.iterdir():
        if item.is_file() and item.suffix == '.csv':
            csv_files.append(item)
    
    # 扫描所有子目录
    for subdir in ['sz_sme', 'sz_gem', 'sh_main', 'sh_star', 'sz_main']:
        subdir_path = CURRENT_DATA_DIR / subdir
        if subdir_path.exists():
            for item in subdir_path.iterdir():
                if item.is_file() and item.suffix == '.csv':
                    csv_files.append(item)
    
    print(f"发现 {len(csv_files)} 个CSV文件")
    
    # 迁移每个文件
    migrated_count = 0
    skipped_count = 0
    
    for csv_path in csv_files:
        code = csv_path.stem
        exchange = get_exchange(code)
        
        # 创建交易所子目录
        exchange_dir = DATALAKE_DIR / exchange
        exchange_dir.mkdir(exist_ok=True)
        
        # 目标Parquet路径
        parquet_path = exchange_dir / f"{code}.parquet"
        
        # 如果已存在则跳过
        if parquet_path.exists():
            print(f"跳过 {code} (已存在)")
            skipped_count += 1
            continue
        
        try:
            # 读取CSV
            df = pd.read_csv(csv_path)
            
            # 统一列名和格式
            df = standardize_dataframe(df, code)
            
            # 保存为Parquet
            df.to_parquet(parquet_path, index=False)
            
            print(f"迁移 {code} -> {exchange}/{code}.parquet")
            migrated_count += 1
            
        except Exception as e:
            print(f"迁移 {code} 失败: {e}")
            skipped_count += 1
    
    print(f"\n迁移完成：{migrated_count} 成功, {skipped_count} 跳过")


def standardize_dataframe(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """标准化DataFrame格式"""
    # 确保日期列格式正确
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # 统一列名映射
    column_mapping = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'amount': 'amount',
        'turnover_rate': 'turnover_rate',
        'price_change_pct': 'change_pct',
        'amplitude': 'amplitude',
        'ma_price5': 'ma5',
        'ma_volume5': 'ma_volume5',
    }
    
    # 重命名列
    df = df.rename(columns=column_mapping)
    
    # 确保必需列存在
    required_columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0.0
    
    # 添加股票代码列
    df['code'] = code
    
    # 设置正确的数据类型
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['amount'] = df['amount'].astype(float)
    
    # 按日期排序
    df = df.sort_values('date')
    
    return df


def create_metadata():
    """创建元数据文件"""
    metadata = {
        'version': '1.0',
        'created_at': pd.Timestamp.now().isoformat(),
        'description': 'A股日线数据 - DataLake格式',
        'exchange_map': EXCHANGE_MAP,
        'columns': {
            'code': '股票代码',
            'date': '交易日期',
            'open': '开盘价',
            'high': '最高价',
            'low': '最低价',
            'close': '收盘价',
            'volume': '成交量',
            'amount': '成交额',
            'turnover_rate': '换手率',
            'change_pct': '涨跌幅(%)',
            'amplitude': '振幅(%)',
        }
    }
    
    import json
    metadata_path = DATALAKE_DIR / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"创建元数据文件: {metadata_path}")


if __name__ == "__main__":
    print("=== 数据迁移脚本 ===")
    print(f"源目录: {CURRENT_DATA_DIR}")
    print(f"目标目录: {DATALAKE_DIR}")
    print()
    
    migrate_csv_to_parquet()
    create_metadata()
    
    print("\n=== 迁移完成 ===")