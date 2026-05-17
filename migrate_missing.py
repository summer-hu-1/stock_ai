#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

CURRENT_DATA_DIR = Path('data/cn/daily')
DATALAKE_DIR = Path('datalake/cn/daily')

EXCHANGE_MAP = {
    '000': 'SZ', '001': 'SZ', '002': 'SZ', '003': 'SZ',
    '300': 'SZ', '301': 'SZ',
    '600': 'SH', '601': 'SH', '603': 'SH', '605': 'SH',
    '688': 'SH', '689': 'SH',
}

def get_exchange(code):
    return EXCHANGE_MAP.get(code[:3], 'UNKNOWN')

missing_codes = ['002624', '600131', '600161', '600298']

for code in missing_codes:
    csv_path = CURRENT_DATA_DIR / f'{code}.csv'
    exchange = get_exchange(code)
    parquet_path = DATALAKE_DIR / exchange / f'{code}.parquet'
    
    if csv_path.exists():
        print(f'迁移 {code} -> {exchange}/{code}.parquet')
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.rename(columns={'price_change_pct': 'change_pct'})
        df['code'] = code
        df.to_parquet(parquet_path, index=False)
    else:
        print(f'文件不存在: {csv_path}')

print('完成!')