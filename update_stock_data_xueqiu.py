#!/usr/bin/env python3
"""
使用雪球API增量更新股票数据

功能：
1. 更新现有股票数据（从2023-01-13到现在）
2. 补充缺失的股票文件
3. 同时更新 CSV 和 Parquet 格式
"""

import os
import sys
import time
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set, Optional

sys.path.insert(0, str(Path(__file__).parent))

import akshare as ak

DATA_DIR = Path(__file__).parent / "data" / "cn" / "daily"
DATALAKE_DIR = Path(__file__).parent / "datalake" / "cn" / "daily"
START_DATE = "2023-01-13"
END_DATE = datetime.now().strftime("%Y-%m-%d")

PREFIX_TO_DIR = {
    '000': ('sz_main', 'SZ'),
    '001': ('sz_main', 'SZ'),
    '002': ('sz_sme', 'SZ'),
    '003': ('sz_main', 'SZ'),
    '300': ('sz_gem', 'SZ'),
    '301': ('sz_gem', 'SZ'),
    '600': ('sh_main', 'SH'),
    '601': ('sh_main', 'SH'),
    '603': ('sh_main', 'SH'),
    '605': ('sh_main', 'SH'),
    '688': ('sh_star', 'SH'),
    '689': ('sh_star', 'SH'),
}

requests_session = requests.Session()
requests_session.trust_env = False
requests_session.proxies = {}


def get_code_info(code: str) -> tuple:
    prefix = code[:3]
    return PREFIX_TO_DIR.get(prefix, ('unknown', 'UNKNOWN'))


def get_all_stock_codes() -> List[str]:
    print("📡 获取A股股票列表...")
    try:
        df = ak.stock_info_a_code_name()
        codes = df['code'].tolist()
        print(f"✅ 获取到 {len(codes)} 只股票")
        return sorted(codes)
    except Exception as e:
        print(f"❌ 获取股票列表失败: {e}")
        return []


def get_stock_data_from_xueqiu(code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """使用雪球API获取股票历史K线数据"""
    try:
        if code.startswith('6'):
            market = 'SH'
        else:
            market = 'SZ'

        session = requests.Session()
        session.trust_env = False
        session.proxies = {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://xueqiu.com/'
        }

        url = f'https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={market}{code}&begin={int(datetime.now().timestamp()*1000)}&period=day&type=before&count=-1000&indicator=kline'

        response = session.get(url, headers=headers, timeout=10)
        data = response.json()

        if data.get('error_code') == 0 and data.get('data'):
            klines = data['data']['klines']
            if klines:
                df = pd.DataFrame(klines, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turnover_rate', 'change_pct', 'change_amount', 'dummy'])
                df['date'] = pd.to_datetime(df['date'])
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)
                df['amount'] = df['amount'].astype(float)
                df['turnover_rate'] = df['turnover_rate'].astype(float)
                df['change_pct'] = df['change_pct'].astype(float)

                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

                if not df.empty:
                    return df

        return None
    except Exception as e:
        return None


def get_stock_data_from_akshare(code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """使用akshare获取股票历史数据"""
    try:
        start_str = start_date.replace('-', '')
        end_str = end_date.replace('-', '')

        df = ak.stock_zh_a_hist(symbol=code, start_date=start_str, end_date=end_str, adjust='qfq')

        if df is None or df.empty:
            return None

        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '换手率': 'turnover_rate',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change_amount',
            '振幅': 'amplitude',
        })

        df['date'] = pd.to_datetime(df['date'])

        return df
    except Exception as e:
        return None


def get_existing_codes() -> Set[str]:
    existing = set()
    for csv_file in DATA_DIR.glob("*.csv"):
        existing.add(csv_file.stem)
    for subdir in ['sz_sme', 'sz_gem', 'sh_main', 'sh_star', 'sz_main']:
        for csv_file in (DATA_DIR / subdir).glob("*.csv"):
            existing.add(csv_file.stem)
    return existing


def update_stock(code: str, dry_run: bool = False) -> bool:
    csv_dir, exchange = get_code_info(code)
    target_dir = DATA_DIR / csv_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    csv_path = target_dir / f"{code}.csv"
    parquet_path = DATALAKE_DIR / exchange / f"{code}.parquet"

    df = None

    try:
        df = get_stock_data_from_akshare(code, START_DATE, END_DATE)
    except:
        pass

    if df is None or df.empty:
        try:
            df = get_stock_data_from_xueqiu(code, START_DATE, END_DATE)
        except:
            pass

    if df is None or df.empty:
        return False

    if dry_run:
        print(f"  📥 将更新: {code} ({len(df)} 行)")
        return True

    df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100
    df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'turnover_rate', 'change_pct', 'amplitude']]
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    df.to_csv(csv_path, index=False)

    parquet_dir = DATALAKE_DIR / exchange
    parquet_dir.mkdir(parents=True, exist_ok=True)

    df_parquet = df.copy()
    df_parquet['code'] = code
    df_parquet = df_parquet.rename(columns={'change_pct': 'price_change_pct'})
    df_parquet.to_parquet(parquet_path, index=False)

    return True


def main():
    print("=" * 50)
    print("🚀 股票数据增量更新工具 (雪球API)")
    print("=" * 50)
    print(f"📅 数据范围: {START_DATE} ~ {END_DATE}")
    print()

    all_codes = get_all_stock_codes()
    existing_codes = get_existing_codes()

    print(f"📊 股票总数: {len(all_codes)}")
    print(f"📁 已存在: {len(existing_codes)}")

    missing_codes = [c for c in all_codes if c not in existing_codes]
    existing_to_update = [c for c in all_codes if c in existing_codes]

    print(f"❌ 缺失: {len(missing_codes)}")
    print(f"🔄 需要更新: {len(existing_to_update)}")
    print()

    if missing_codes:
        print(f"📥 补充缺失的 {len(missing_codes)} 只股票...")
        success_count = 0
        for i, code in enumerate(missing_codes):
            try:
                if update_stock(code):
                    success_count += 1
                    print(f"  ✅ {code} ({i+1}/{len(missing_codes)})")
                else:
                    print(f"  ❌ {code} 获取数据失败")
            except Exception as e:
                print(f"  ❌ {code} 错误: {e}")
            time.sleep(0.2)
        print(f"✅ 补充完成: {success_count} 只")
        print()

    if existing_to_update:
        print(f"🔄 更新现有的 {len(existing_to_update)} 只股票...")
        success_count = 0
        for i, code in enumerate(existing_to_update):
            try:
                if update_stock(code):
                    success_count += 1
                if (i + 1) % 100 == 0:
                    print(f"  进度: {i+1}/{len(existing_to_update)}")
            except Exception as e:
                print(f"  ❌ {code} 错误: {e}")
            time.sleep(0.2)
        print(f"✅ 更新完成: {success_count} 只")

    print()
    print("=" * 50)
    print("🎉 数据更新完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()