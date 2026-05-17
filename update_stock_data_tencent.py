#!/usr/bin/env python3
"""
使用腾讯财经API增量更新股票数据
"""

import os
import sys
import time
import json
import warnings
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent / "data" / "cn" / "daily"
DATALAKE_DIR = Path(__file__).parent / "datalake" / "cn" / "daily"
STOCK_LIST_FILE = Path(__file__).parent / "stock_list.csv"
START_DATE = "2023-01-13"
END_DATE = datetime.now().strftime("%Y-%m-%d")

PREFIX_TO_DIR = {
    '000': ('sz_main', 'SZ'), '001': ('sz_main', 'SZ'), '002': ('sz_sme', 'SZ'),
    '003': ('sz_main', 'SZ'), '300': ('sz_gem', 'SZ'), '301': ('sz_gem', 'SZ'),
    '600': ('sh_main', 'SH'), '601': ('sh_main', 'SH'), '603': ('sh_main', 'SH'),
    '605': ('sh_main', 'SH'), '688': ('sh_star', 'SH'), '689': ('sh_star', 'SH'),
}


def get_code_info(code):
    code = str(code).zfill(6)
    prefix = code[:3]
    return PREFIX_TO_DIR.get(prefix, ('unknown', 'UNKNOWN'))


def get_stock_codes():
    print("📡 读取股票列表...")
    if STOCK_LIST_FILE.exists():
        df = pd.read_csv(STOCK_LIST_FILE)
        codes = [str(c).zfill(6) for c in df['code'].tolist()]
        print(f"✅ 从本地文件获取到 {len(codes)} 只股票")
        return codes
    else:
        print("❌ 本地股票列表文件不存在")
        return []


def get_existing_codes():
    existing = set()
    for csv_file in DATA_DIR.glob("*.csv"):
        existing.add(csv_file.stem)
    for subdir in ['sz_sme', 'sz_gem', 'sh_main', 'sh_star', 'sz_main']:
        for csv_file in (DATA_DIR / subdir).glob("*.csv"):
            existing.add(csv_file.stem)
    return existing


def get_stock_data_from_tencent(code, start_date, end_date):
    code = str(code).zfill(6)

    session = requests.Session()
    session.trust_env = False
    session.proxies = {}

    if code.startswith('6'):
        market = 'sh'
    else:
        market = 'sz'

    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={market}{code},day,{start_date},{end_date},1000,qfq'

    try:
        r = session.get(url, timeout=10)
        text = r.text
        if text.startswith('kline_dayqfq='):
            text = text[len('kline_dayqfq='):]

        data = json.loads(text)
        if data.get('code') == 0 and data.get('data'):
            stock_data = data['data'].get(f'{market}{code}', {})
            qfqday = stock_data.get('qfqday', [])

            if not qfqday:
                return None

            cleaned_data = []
            for row in qfqday:
                if len(row) >= 6:
                    cleaned_data.append([row[0], row[1], row[2], row[3], row[4], row[5]])

            df = pd.DataFrame(cleaned_data, columns=['date', 'open', 'close', 'high', 'low', 'volume'])

            df['date'] = pd.to_datetime(df['date'])
            df['open'] = df['open'].astype(float)
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)

            df['amount'] = df['volume'] * df['close']
            df['turnover_rate'] = 0.0
            df['change_pct'] = df['close'].pct_change() * 100
            df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100

            df = df.sort_values('date')
            return df
    except Exception as e:
        pass

    return None


def update_stock(code):
    code = str(code).zfill(6)
    csv_dir, exchange = get_code_info(code)
    target_dir = DATA_DIR / csv_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    csv_path = target_dir / f"{code}.csv"
    parquet_path = DATALAKE_DIR / exchange / f"{code}.parquet"

    df = get_stock_data_from_tencent(code, START_DATE, END_DATE)
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
    print("🚀 股票数据增量更新工具 (腾讯财经API)")
    print("=" * 50)
    print(f"📅 数据范围: {START_DATE} ~ {END_DATE}")

    all_codes = get_stock_codes()
    if not all_codes:
        return

    existing_codes = get_existing_codes()

    print(f"\n📊 股票总数: {len(all_codes)}")
    print(f"📁 已存在: {len(existing_codes)}")

    missing = [c for c in all_codes if c not in existing_codes]
    to_update = [c for c in all_codes if c in existing_codes]

    print(f"❌ 缺失: {len(missing)} (API可能不支持)")
    print(f"🔄 需要更新: {len(to_update)}")

    print("\n" + "=" * 50)
    print("📝 提示: 缺失的股票可能是北交所(92xxxx)、新股或数据源不支持")
    print("=" * 50 + "\n")

    total = len(to_update)
    success = 0
    fail = 0

    for i, code in enumerate(to_update):
        try:
            if update_stock(code):
                success += 1
                status = "✅"
            else:
                fail += 1
                status = "❌"
        except Exception as e:
            fail += 1
            status = f"❌ Error: {e}"

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{total}] 成功: {success}, 失败: {fail}")

        if (i + 1) % 100 == 0:
            print(f"\n  进度: {i+1}/{total} ({success} 成功, {fail} 失败)\n")

        time.sleep(0.05)

    print(f"\n" + "=" * 50)
    print(f"✅ 完成! 成功: {success}, 失败: {fail}")
    print("=" * 50)


if __name__ == "__main__":
    main()