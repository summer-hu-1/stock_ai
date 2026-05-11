#!/usr/bin/env python3
"""
按股票名称排序同步A股3年日线数据

功能：
1. 获取完整的A股股票列表
2. 按股票名称拼音排序
3. 依次为每只股票拉取近三年日线数据
4. 保存为CSV文件到 data/cn/daily/ 目录
5. 支持断点续传（跳过已存在的文件）
"""

import pandas as pd
import os
import time
from tqdm import tqdm
from datetime import datetime, timedelta

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
import sys
sys.path.insert(0, project_dir)

# 导入统一API降级框架
from core.api_fallback.registry import (
    register_default_apis,
    get_stock_hist_with_fallback,
    get_stock_list_with_fallback
)

# 获取项目根目录
data_dir = os.path.join(project_dir, "data", "cn", "daily")
stock_list_path = os.path.join(project_dir, "data", "cn", "stock_list.csv")

os.makedirs(data_dir, exist_ok=True)

# 列名映射
KEEP_COLUMNS = [
    "date", "open", "high", "low", "close",
    "volume", "amount", "amplitude", "price_change_pct", "turnover_rate"
]


def sync_stock(code, name, start_date="20230101", max_retries=2):
    """
    同步单只股票的日线数据
    
    Args:
        code: 股票代码
        name: 股票名称
        start_date: 开始日期 (格式: YYYYMMDD)
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功
    """
    code = str(code).zfill(6)
    save_path = f"{data_dir}/{code}.csv"
    
    # 如果文件已存在，跳过
    if os.path.exists(save_path):
        print(f"⏭️ [{code}] {name} - 已存在，跳过")
        return True
    
    print(f"\n📥 [{code}] {name} - 开始同步")
    
    for attempt in range(max_retries):
        try:
            # 使用统一API降级框架获取历史数据
            df = get_stock_hist_with_fallback(code, start_date=start_date)
            
            if df is None or df.empty:
                print(f"⚠️ [{code}] {name} - 无数据")
                return False
            
            # 确保日期格式正确
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            # 只保留需要的列
            available_cols = [col for col in KEEP_COLUMNS if col in df.columns]
            df = df[available_cols]
            
            # 按日期排序
            if 'date' in df.columns:
                df = df.sort_values('date')
            
            # 保存
            df.to_csv(save_path, index=False)
            print(f"✅ [{code}] {name} - 成功 ({len(df)} 条记录)")
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ [{code}] {name} - 第 {attempt + 1} 次尝试失败，重试...")
                time.sleep(2)
            else:
                print(f"❌ [{code}] {name} - 失败: {e}")
                return False
    
    return False


def download_stock_list():
    """下载股票列表"""
    print("📥 正在获取股票列表...")
    
    # 使用统一API降级框架获取股票列表
    stocks = get_stock_list_with_fallback()
    
    if not stocks:
        print("❌ 无法获取股票列表")
        return None
    
    # 创建DataFrame
    df = pd.DataFrame(stocks)
    df['code'] = df['code'].apply(lambda x: str(x).zfill(6))
    
    # 按名称排序
    df = df.sort_values('name')
    
    # 保存
    os.makedirs(os.path.dirname(stock_list_path), exist_ok=True)
    df.to_csv(stock_list_path, index=False)
    print(f"✅ 股票列表保存成功，共 {len(df)} 只股票（已按名称排序）")
    
    return df


def main():
    # 初始化API降级框架
    register_default_apis()
    
    # 检查股票列表是否存在
    if not os.path.exists(stock_list_path):
        print("⚠️ 股票列表文件不存在，正在获取...")
        stock_df = download_stock_list()
        if stock_df is None:
            return
    else:
        stock_df = pd.read_csv(stock_list_path)
        # 确保按名称排序
        stock_df = stock_df.sort_values('name')
        print(f"📋 读取已有的股票列表，共 {len(stock_df)} 只股票")
    
    # 计算3年前的日期
    three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
    print(f"📅 同步起始日期: {three_years_ago}")
    
    # 统计已存在的文件
    existing_files = set()
    for f in os.listdir(data_dir):
        if f.endswith('.csv'):
            existing_files.add(f.replace('.csv', ''))
    
    print(f"📂 已存在 {len(existing_files)} 个数据文件")
    
    # 筛选需要同步的股票（排除已存在的）
    stock_df['needs_sync'] = ~stock_df['code'].isin(existing_files)
    stocks_to_sync = stock_df[stock_df['needs_sync']]
    
    print("\n" + "=" * 70)
    print(f"开始按名称排序同步A股日线数据")
    print(f"总计股票: {len(stock_df)} | 待同步: {len(stocks_to_sync)} | 已存在: {len(existing_files)}")
    print("=" * 70)
    
    success = 0
    failed = []
    skipped = 0
    
    for idx, row in tqdm(stocks_to_sync.iterrows(), desc="同步进度", total=len(stocks_to_sync)):
        code = str(row['code']).zfill(6)
        name = row['name']
        
        ok = sync_stock(code, name, start_date=three_years_ago)
        if ok:
            success += 1
        else:
            failed.append(f"{code} ({name})")
        
        # 避免请求过快
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print(f"⏭️ 跳过: {len(existing_files)} 只（已存在）")
    print(f"✅ 成功: {success} 只股票")
    if failed:
        print(f"❌ 失败: {len(failed)} 只股票")
        print(f"失败股票: {failed[:5]}..." if len(failed) > 5 else f"失败股票: {failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()