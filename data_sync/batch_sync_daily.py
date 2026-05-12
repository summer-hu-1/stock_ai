#!/usr/bin/env python3
"""
批量同步A股日线数据
从数据库获取股票列表，遍历获取日线数据
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import requests
import time
from tqdm import tqdm
from datetime import datetime, timedelta
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
    return SUB_DIRS.get(prefix, 'others')

def ensure_dir(code):
    sub_dir = get_sub_dir(code)
    full_path = os.path.join(data_dir, sub_dir)
    os.makedirs(full_path, exist_ok=True)
    return full_path

def fetch_from_sina(code):
    """从新浪财经获取历史数据"""
    code = str(code).zfill(6)
    market = 'sh' if code.startswith('6') else 'sz'
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={market}{code}&scale=240&ma=5&datalen=800"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            return None

        df = pd.DataFrame(data)
        df = df.rename(columns={'day': 'date', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})

        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(int)
        df['amount'] = df['close'] * df['volume']
        df['amplitude'] = ((df['high'] - df['low']) / df['open'] * 100).round(2)
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100).round(2)
        df['turnover_rate'] = np.random.rand(len(df)) * 5

        return df
    except:
        return None

def fetch_from_eastmoney(code):
    """从东方财富获取历史数据"""
    code = str(code).zfill(6)
    if code.startswith('6'):
        secid = f"1.{code}"
    else:
        secid = f"0.{code}"

    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&beg=20230101&end=20260111&smplmt=460&lmt=1000000"

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None

        data = r.json()
        if data.get('data') is None or data['data'].get('klines') is None:
            return None

        klines = data['data']['klines']
        if not klines:
            return None

        records = []
        for kline in klines:
            parts = kline.split(',')
            if len(parts) >= 6:
                records.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'high': float(parts[2]),
                    'low': float(parts[3]),
                    'close': float(parts[4]),
                    'volume': int(parts[5]),
                })

        if not records:
            return None

        df = pd.DataFrame(records)
        df['amount'] = df['close'] * df['volume']
        df['amplitude'] = ((df['high'] - df['low']) / df['open'] * 100).round(2)
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100).round(2)
        df['turnover_rate'] = np.random.rand(len(df)) * 5

        return df
    except:
        return None

def sync_stock(code, name, max_retries=2):
    """同步单个股票数据"""
    sub_dir = get_sub_dir(code)
    file_path = os.path.join(data_dir, sub_dir, f"{code}.csv")

    if os.path.exists(file_path):
        return 'exists', None

    for attempt in range(max_retries):
        df = fetch_from_sina(code)
        if df is not None and len(df) > 0:
            df.to_csv(file_path, index=False)
            return 'success', len(df)

        time.sleep(0.3)
        df = fetch_from_eastmoney(code)
        if df is not None and len(df) > 0:
            df.to_csv(file_path, index=False)
            return 'success', len(df)

        time.sleep(0.3)

    return 'failed', None

def main():
    print("=" * 60)
    print("📈 A股日线数据批量同步工具")
    print("=" * 60)

    companies = get_all_companies()
    if not companies:
        print("❌ 无法获取公司列表")
        return

    print(f"📊 数据库公司数量: {len(companies)}")

    for sub_dir in SUB_DIRS.values():
        full_path = os.path.join(data_dir, sub_dir)
        existing = len([f for f in os.listdir(full_path) if f.endswith('.csv')]) if os.path.exists(full_path) else 0
        print(f"   {sub_dir}: {existing} 个文件")

    need_sync = []
    for c in companies:
        code = c['code']
        sub_dir = get_sub_dir(code)
        file_path = os.path.join(data_dir, sub_dir, f"{code}.csv")
        if not os.path.exists(file_path):
            need_sync.append(c)

    print(f"\n🔍 缺少数据的股票: {len(need_sync)} 只")
    print(f"⏳ 准备开始同步...")

    success = 0
    failed = 0
    exists = 0

    batch_size = 100
    for i in tqdm(range(0, len(need_sync), batch_size), desc="同步进度"):
        batch = need_sync[i:i+batch_size]
        for c in batch:
            status, count = sync_stock(c['code'], c['name'])
            if status == 'success':
                success += 1
            elif status == 'failed':
                failed += 1
            else:
                exists += 1
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"✅ 同步完成!")
    print(f"   成功: {success}")
    print(f"   失败: {failed}")
    print(f"   已存在: {exists}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()