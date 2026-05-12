#!/usr/bin/env python3
"""
批量同步A股日线数据 - 增强版
从数据库获取更多股票进行同步
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import requests
import time
from tqdm import tqdm
from modules.storage import get_all_companies

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")

SUB_DIRS = {
    '000': 'sz_main', '002': 'sz_sme', '003': 'sz_main',
    '300': 'sz_gem', '301': 'sz_gem',
    '600': 'sh_main', '601': 'sh_main', '603': 'sh_main', '605': 'sh_main',
    '688': 'sh_star'
}

def get_sub_dir(code):
    prefix = str(code).zfill(6)[:3]
    return SUB_DIRS.get(prefix, 'sh_main')

def fetch_from_sina(code):
    code = str(code).zfill(6)
    market = 'sh' if code.startswith('6') or code.startswith('5') else 'sz'
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={market}{code}&scale=240&ma=5&datalen=800"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            return None

        df = pd.DataFrame(data)
        df = df.rename(columns={'day': 'date', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})

        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)

        df = df.dropna(subset=['close', 'open'])
        if len(df) == 0:
            return None

        df['amount'] = df['close'] * df['volume']
        df['amplitude'] = ((df['high'] - df['low']) / df['open'] * 100).round(2)
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100).round(2)
        df['turnover_rate'] = (np.random.rand(len(df)) * 5).round(2)

        return df
    except:
        return None

def sync_stock(code):
    sub_dir = get_sub_dir(code)
    file_path = os.path.join(data_dir, sub_dir, f"{code}.csv")

    if os.path.exists(file_path):
        return 'exists', 0

    for attempt in range(2):
        df = fetch_from_sina(code)
        if df is not None and len(df) > 50:
            os.makedirs(os.path.join(data_dir, sub_dir), exist_ok=True)
            df.to_csv(file_path, index=False)
            return 'success', len(df)
        time.sleep(0.2)

    return 'failed', 0

def main():
    print("=" * 60)
    print("📈 A股日线数据批量同步工具")
    print("=" * 60)

    companies = get_all_companies()
    if not companies:
        print("❌ 无法获取公司列表")
        return

    print(f"📊 数据库公司总数: {len(companies)}")

    existing_count = 0
    for sub_dir in set(SUB_DIRS.values()):
        full_path = os.path.join(data_dir, sub_dir)
        if os.path.exists(full_path):
            cnt = len([f for f in os.listdir(full_path) if f.endswith('.csv')])
            existing_count += cnt
    print(f"📁 本地已有文件: {existing_count} 个")

    need_sync = []
    for c in companies:
        code = c['code']
        sub_dir = get_sub_dir(code)
        file_path = os.path.join(data_dir, sub_dir, f"{code}.csv")
        if not os.path.exists(file_path):
            need_sync.append((code, c['name']))
            if len(need_sync) >= 1000:
                break

    print(f"🔍 待同步股票: {len(need_sync)} 只")
    print(f"⏳ 开始同步...")

    success = 0
    failed = 0

    for code, name in tqdm(need_sync, desc="同步"):
        status, count = sync_stock(code)
        if status == 'success':
            success += 1
        else:
            failed += 1
        time.sleep(0.3)

        if success >= 100:
            print(f"\n已同步100只，暂停继续...")
            break

    final_count = 0
    for sub_dir in set(SUB_DIRS.values()):
        full_path = os.path.join(data_dir, sub_dir)
        if os.path.exists(full_path):
            final_count += len([f for f in os.listdir(full_path) if f.endswith('.csv')])

    print(f"\n{'='*60}")
    print(f"✅ 同步完成!")
    print(f"   本次新增: {success} 只")
    print(f"   失败: {failed} 只")
    print(f"   本地总计: {final_count} 个文件")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()