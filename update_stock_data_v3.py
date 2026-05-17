#!/usr/bin/env python3
"""
使用雪球API增量更新股票数据 - 禁用代理版本
"""

import os
import sys
import time
import warnings
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

import urllib3
urllib3.disable_warnings()

requests_session = requests.Session()
requests_session.trust_env = False
requests_session.proxies = {}

original_session_request = requests.Session.request
def no_proxy_session_request(self, method, url, **kwargs):
    kwargs.pop('proxies', None)
    return original_session_request(self, method, url, proxies={}, **kwargs)
requests.Session.request = no_proxy_session_request

sys.path.insert(0, str(Path(__file__).parent))

import akshare as ak

DATA_DIR = Path(__file__).parent / "data" / "cn" / "daily"
DATALAKE_DIR = Path(__file__).parent / "datalake" / "cn" / "daily"
START_DATE = "2023-01-13"
END_DATE = datetime.now().strftime("%Y-%m-%d")

PREFIX_TO_DIR = {
    '000': ('sz_main', 'SZ'), '001': ('sz_main', 'SZ'), '002': ('sz_sme', 'SZ'),
    '003': ('sz_main', 'SZ'), '300': ('sz_gem', 'SZ'), '301': ('sz_gem', 'SZ'),
    '600': ('sh_main', 'SH'), '601': ('sh_main', 'SH'), '603': ('sh_main', 'SH'),
    '605': ('sh_main', 'SH'), '688': ('sh_star', 'SH'), '689': ('sh_star', 'SH'),
}


def get_code_info(code):
    prefix = code[:3]
    return PREFIX_TO_DIR.get(prefix, ('unknown', 'UNKNOWN'))


def get_stock_codes():
    print("📡 获取股票列表...")
    df = ak.stock_info_a_code_name()
    codes = df['code'].tolist()
    print(f"✅ 获取到 {len(codes)} 只股票")
    return codes


def get_existing_codes():
    existing = set()
    for csv_file in DATA_DIR.glob("*.csv"):
        existing.add(csv_file.stem)
    for subdir in ['sz_sme', 'sz_gem', 'sh_main', 'sh_star', 'sz_main']:
        for csv_file in (DATA_DIR / subdir).glob("*.csv"):
            existing.add(csv_file.stem)
    return existing


def get_stock_data(code, start_date, end_date):
    start_str = start_date.replace('-', '')
    end_str = end_date.replace('-', '')

    try:
        df = ak.stock_zh_a_hist(symbol=code, start_date=start_str, end_date=end_str, adjust='qfq')
        if df is not None and not df.empty:
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '最高': 'high', '最低': 'low',
                '收盘': 'close', '成交量': 'volume', '成交额': 'amount',
                '换手率': 'turnover_rate', '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount', '振幅': 'amplitude',
            })
            df['date'] = pd.to_datetime(df['date'])
            return df
    except Exception as e:
        pass
    return None


def update_stock(code):
    csv_dir, exchange = get_code_info(code)
    target_dir = DATA_DIR / csv_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    csv_path = target_dir / f"{code}.csv"
    parquet_path = DATALAKE_DIR / exchange / f"{code}.parquet"

    df = get_stock_data(code, START_DATE, END_DATE)
    if df is None or df.empty:
        return False

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
    print("🚀 股票数据增量更新工具")
    print("=" * 50)
    print(f"📅 数据范围: {START_DATE} ~ {END_DATE}")

    all_codes = get_stock_codes()
    existing_codes = get_existing_codes()

    print(f"\n📊 股票总数: {len(all_codes)}")
    print(f"📁 已存在: {len(existing_codes)}")

    missing = [c for c in all_codes if c not in existing_codes]
    to_update = [c for c in all_codes if c in existing_codes]

    print(f"❌ 缺失: {len(missing)}")
    print(f"🔄 需要更新: {len(to_update)}")

    total = len(missing) + len(to_update)
    success = 0

    for i, code in enumerate(missing + to_update):
        try:
            if update_stock(code):
                success += 1
        except:
            pass

        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{total} ({success} 成功)")

        if (i + 1) % 10 == 0:
            time.sleep(0.3)

    print(f"\n✅ 完成! 成功: {success}/{total}")
    print("=" * 50)


if __name__ == "__main__":
    main()