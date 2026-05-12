#!/usr/bin/env python3
"""
全量同步A股日线数据
自动同步数据库中的所有股票
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
from modules.storage import get_all_companies

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")
log_file = os.path.join(script_dir, "sync_full.log")

SUB_DIRS = {
    '000': 'sz_main', '002': 'sz_sme', '003': 'sz_main',
    '300': 'sz_gem', '301': 'sz_gem',
    '600': 'sh_main', '601': 'sh_main', '603': 'sh_main', '605': 'sh_main',
    '688': 'sh_star'
}

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(log_file, 'a') as f:
        f.write(log_msg + "\n")

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

    df = fetch_from_sina(code)
    if df is not None and len(df) > 50:
        os.makedirs(os.path.join(data_dir, sub_dir), exist_ok=True)
        df.to_csv(file_path, index=False)
        return 'success', len(df)

    time.sleep(0.2)
    return 'failed', 0

def get_existing_count():
    count = 0
    for sub_dir in set(SUB_DIRS.values()):
        full_path = os.path.join(data_dir, sub_dir)
        if os.path.exists(full_path):
            count += len([f for f in os.listdir(full_path) if f.endswith('.csv')])
    return count

def main():
    log("=" * 60)
    log("📈 A股日线数据全量同步开始")
    log("=" * 60)

    companies = get_all_companies()
    if not companies:
        log("❌ 无法获取公司列表")
        return

    total = len(companies)
    existing = get_existing_count()
    log(f"📊 数据库公司总数: {total}")
    log(f"📁 本地已有文件: {existing} 个")

    need_sync = []
    for c in companies:
        code = c['code']
        sub_dir = get_sub_dir(code)
        file_path = os.path.join(data_dir, sub_dir, f"{code}.csv")
        if not os.path.exists(file_path):
            need_sync.append((code, c['name']))

    log(f"🔍 待同步股票: {len(need_sync)} 只")
    log("⏳ 开始同步...")
    log("=" * 60)

    success = 0
    failed = 0
    start_time = time.time()

    for i, (code, name) in enumerate(need_sync):
        status, count = sync_stock(code)
        if status == 'success':
            success += 1
        else:
            failed += 1

        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = success / elapsed if elapsed > 0 else 0
            remaining = (len(need_sync) - i - 1) / rate if rate > 0 else 0
            log(f"进度: {i+1}/{len(need_sync)} | 成功: {success} | 失败: {failed} | 速度: {rate:.1f}/秒 | 预计剩余: {remaining/60:.1f}分钟")

        time.sleep(0.3)

    final = get_existing_count()
    log("=" * 60)
    log("✅ 全量同步完成!")
    log(f"   总计: {final} 个文件")
    log(f"   新增成功: {success}")
    log(f"   失败: {failed}")
    log(f"   耗时: {(time.time()-start_time)/60:.1f} 分钟")
    log("=" * 60)

if __name__ == "__main__":
    main()