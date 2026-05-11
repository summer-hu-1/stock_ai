#!/usr/bin/env python3
"""
从真实数据源获取A股历史数据并更新现有文件

功能：
1. 尝试从akshare和雪球API获取真实数据
2. 如果真实数据获取成功，更新现有的CSV文件
3. 保留数据完整性检查
"""

import pandas as pd
import numpy as np
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


def update_with_real_data(code, name, start_date="20230101", max_retries=2):
    """
    尝试从真实数据源获取数据并更新文件
    
    Args:
        code: 股票代码
        name: 股票名称
        start_date: 开始日期
        max_retries: 最大重试次数
    
    Returns:
        tuple: (success, source_type, record_count)
               source_type: 'real' | 'csv' | 'mock'
    """
    code = str(code).zfill(6)
    save_path = f"{data_dir}/{code}.csv"
    
    print(f"\n📥 [{code}] {name}")
    
    for attempt in range(max_retries):
        try:
            # 使用统一API降级框架获取历史数据
            df = get_stock_hist_with_fallback(code, start_date=start_date)
            
            if df is None or df.empty:
                print(f"   ⚠️ 所有数据源都返回空数据")
                return (False, 'none', 0)
            
            # 识别数据来源（通过日志判断）
            # 如果数据日期超过当前日期，说明是模拟数据
            if 'date' in df.columns and len(df) > 0:
                last_date = df['date'].iloc[-1]
                if pd.to_datetime(last_date) > datetime.now():
                    print(f"   ⚠️ 数据日期异常，可能是模拟数据")
                    return (False, 'mock', len(df))
            
            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            # 只保留需要的列
            available_cols = [col for col in KEEP_COLUMNS if col in df.columns]
            df = df[available_cols]
            
            # 按日期排序
            df = df.sort_values('date')
            
            # 保存
            df.to_csv(save_path, index=False)
            
            # 检查数据质量
            if len(df) > 365 * 2:  # 至少2年数据
                print(f"   ✅ 成功获取真实数据 ({len(df)} 条记录)")
                return (True, 'real', len(df))
            else:
                print(f"   ⚠️ 数据量不足 ({len(df)} 条)，可能是部分数据")
                return (True, 'partial', len(df))
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   ⚠️ 第 {attempt + 1} 次尝试失败，重试...")
                time.sleep(3)
            else:
                print(f"   ❌ 获取失败: {str(e)[:50]}")
                return (False, 'error', 0)
    
    return (False, 'error', 0)


def main():
    # 初始化API降级框架
    register_default_apis()
    
    # 读取股票列表
    if not os.path.exists(stock_list_path):
        print("❌ 股票列表文件不存在")
        return
    
    stock_df = pd.read_csv(stock_list_path)
    stock_df['code'] = stock_df['code'].apply(lambda x: str(x).zfill(6))
    
    # 按名称排序
    stock_df = stock_df.sort_values('name')
    
    # 计算3年前的日期
    three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
    print(f"📅 同步起始日期: {three_years_ago}")
    
    # 统计现有文件
    existing_files = {}
    for f in os.listdir(data_dir):
        if f.endswith('.csv'):
            code = f.replace('.csv', '')
            existing_files[code] = os.path.join(data_dir, f)
    
    print(f"\n📂 已存在 {len(existing_files)} 个数据文件")
    
    print("\n" + "=" * 70)
    print("开始更新真实数据（优先使用在线API）")
    print(f"总计股票: {len(stock_df)}")
    print("=" * 70)
    
    results = {
        'real': 0,
        'partial': 0,
        'mock': 0,
        'error': 0,
        'none': 0
    }
    
    for idx, row in tqdm(stock_df.iterrows(), desc="更新进度", total=len(stock_df)):
        code = str(row['code']).zfill(6)
        name = row['name']
        
        success, source, count = update_with_real_data(code, name, start_date=three_years_ago)
        results[source] += 1
        
        # 避免请求过快
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("更新结果统计:")
    print(f"✅ 真实数据: {results['real']} 只")
    print(f"⚠️ 部分数据: {results['partial']} 只")
    print(f"🔄 模拟数据: {results['mock']} 只")
    print(f"❌ 获取失败: {results['error']} 只")
    print(f"🔍 无数据: {results['none']} 只")
    print("=" * 70)


if __name__ == "__main__":
    main()