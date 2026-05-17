#!/usr/bin/env python3
"""
使用 baostock 增量更新股票数据

功能：
1. 更新现有股票数据（从2023-01-13到现在）
2. 补充缺失的股票文件
3. 同时更新 CSV 和 Parquet 格式
"""

import os
import sys
import time
import baostock as bs
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set, Optional

# 配置
DATA_DIR = Path(__file__).parent / "data" / "cn" / "daily"
DATALAKE_DIR = Path(__file__).parent / "datalake" / "cn" / "daily"
START_DATE = "2023-01-13"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# 股票代码前缀到目录的映射
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


def get_code_info(code: str) -> tuple:
    """根据股票代码获取交易所和目录"""
    prefix = code[:3]
    return PREFIX_TO_DIR.get(prefix, ('unknown', 'UNKNOWN'))


def get_all_stock_codes() -> List[str]:
    """获取所有A股股票代码"""
    print("📡 连接 baostock...")
    bs.login()

    print("📋 获取A股股票列表...")
    stock_codes = []

    # 获取上海A股
    rs = bs.query_all_stock(code="sh.a")
    while rs.error_code == '0' and rs.next():
        stock = rs.get_data()
        code = stock['code']
        if code.startswith('sh.60') or code.startswith('sh.688'):
            stock_codes.append(code[3:])  # 去掉 "sh." 前缀

    # 获取深圳A股
    rs = bs.query_all_stock(code="sz.a")
    while rs.error_code == '0' and rs.next():
        stock = rs.get_data()
        code = stock['code']
        if code.startswith('sz.00') or code.startswith('sz.300') or code.startswith('sz.301'):
            stock_codes.append(code[3:])  # 去掉 "sz." 前缀

    bs.logout()
    print(f"✅ 获取到 {len(stock_codes)} 只股票")

    return sorted(stock_codes)


def get_stock_data(code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """获取单只股票的历史数据"""
    prefix = code[:3]
    if prefix in ['000', '001', '002', '003', '300', '301']:
        bs_code = f"sz.{code}"
    else:
        bs_code = f"sh.{code}"

    rs = bs.query_history_k_data_plus(
        bs_code,
        "date,open,high,low,close,volume,amount,turnoverrate,pe,pb",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2"  # 前复权
    )

    if rs.error_code != '0':
        return None

    data_list = []
    while rs.error_code == '0' and rs.next():
        data_list.append(rs.get_data())

    if not data_list:
        return None

    df = pd.DataFrame(data_list, columns=data_list[0].keys())
    df = df.rename(columns={
        'turnoverrate': 'turnover_rate',
        'pe': 'pe',
        'pb': 'pb'
    })

    # 计算额外字段
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['amount'] = df['amount'].astype(float)
    df['turnover_rate'] = df['turnover_rate'].astype(float)

    df['price_change_pct'] = df['close'].pct_change() * 100
    df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100

    df['ma_price5'] = df['close'].rolling(window=5).mean()
    df['ma_volume5'] = df['volume'].rolling(window=5).mean()

    return df


def get_existing_codes() -> Set[str]:
    """获取已存在的股票代码"""
    existing = set()
    for csv_file in DATA_DIR.glob("*.csv"):
        existing.add(csv_file.stem)
    for csv_file in (DATA_DIR / "sz_sme").glob("*.csv"):
        existing.add(csv_file.stem)
    for csv_file in (DATA_DIR / "sz_gem").glob("*.csv"):
        existing.add(csv_file.stem)
    for csv_file in (DATA_DIR / "sh_main").glob("*.csv"):
        existing.add(csv_file.stem)
    for csv_file in (DATA_DIR / "sh_star").glob("*.csv"):
        existing.add(csv_file.stem)
    return existing


def update_stock(code: str, dry_run: bool = False) -> bool:
    """更新单只股票数据"""
    csv_dir, exchange = get_code_info(code)

    # 确保目录存在
    target_dir = DATA_DIR / csv_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    csv_path = target_dir / f"{code}.csv"
    parquet_path = DATALAKE_DIR / exchange / f"{code}.parquet"

    # 获取数据
    df = get_stock_data(code, START_DATE, END_DATE)
    if df is None or df.empty:
        return False

    if dry_run:
        print(f"  📥 将更新: {code} ({len(df)} 行)")
        return True

    # 保存CSV
    df.to_csv(csv_path, index=False)

    # 确保Parquet目录存在
    parquet_dir = DATALAKE_DIR / exchange
    parquet_dir.mkdir(parents=True, exist_ok=True)

    # 保存Parquet
    df['code'] = code
    df = df.rename(columns={'price_change_pct': 'change_pct'})
    df.to_parquet(parquet_path, index=False)

    return True


def main():
    print("=" * 50)
    print("🚀 股票数据增量更新工具 (baostock)")
    print("=" * 50)
    print(f"📅 数据范围: {START_DATE} ~ {END_DATE}")
    print()

    # 获取所有股票代码
    all_codes = get_all_stock_codes()
    existing_codes = get_existing_codes()

    print(f"📊 股票总数: {len(all_codes)}")
    print(f"📁 已存在: {len(existing_codes)}")

    # 找出缺失的股票
    missing_codes = [c for c in all_codes if c not in existing_codes]
    existing_to_update = [c for c in all_codes if c in existing_codes]

    print(f"❌ 缺失: {len(missing_codes)}")
    print(f"🔄 需要更新: {len(existing_to_update)}")
    print()

    # 先补充缺失的
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
            time.sleep(0.1)  # 避免请求过快
        print(f"✅ 补充完成: {success_count} 只")
        print()

    # 更新现有股票
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
            time.sleep(0.1)
        print(f"✅ 更新完成: {success_count} 只")

    print()
    print("=" * 50)
    print("🎉 数据更新完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()