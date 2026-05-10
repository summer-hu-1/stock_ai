#!/usr/bin/env python3
"""
同步A股3年日线数据

运行: python data_sync/sync_cn_daily.py

功能：
- 读取 stock_list.csv 中的股票列表
- 拉取每只股票最近3年的日线数据
- 保存为 CSV 文件到 data/cn/daily/ 目录
"""

import akshare as ak
import pandas as pd
import os
import time
from tqdm import tqdm

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")

os.makedirs(data_dir, exist_ok=True)

# 列名映射
COLUMN_MAPPING = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "price_change_pct",
    "换手率": "turnover_rate"
}

KEEP_COLUMNS = [
    "date", "open", "high", "low", "close",
    "volume", "amount", "amplitude", "price_change_pct", "turnover_rate"
]


def sync_stock(code, start_date="20230101", max_retries=3):
    """
    同步单只股票的日线数据
    
    Args:
        code: 股票代码
        start_date: 开始日期 (格式: YYYYMMDD)
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功
    """
    save_path = f"{data_dir}/{code}.csv"
    
    # 如果文件已存在，跳过
    if os.path.exists(save_path):
        return True
    
    for attempt in range(max_retries):
        try:
            # 禁用代理
            os.environ['HTTP_PROXY'] = ''
            os.environ['HTTPS_PROXY'] = ''
            os.environ['http_proxy'] = ''
            os.environ['https_proxy'] = ''
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                adjust="qfq"
            )
            
            if df is None or df.empty:
                print(f"{code}: 无数据")
                return False
            
            # 重命名列
            df = df.rename(columns=COLUMN_MAPPING)
            
            # 只保留需要的列
            available_cols = [col for col in KEEP_COLUMNS if col in df.columns]
            df = df[available_cols]
            
            # 保存
            df.to_csv(save_path, index=False)
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"{code} 失败: {e}")
                return False
    
    return False


def main():
    stock_list_path = os.path.join(project_dir, "data", "cn", "stock_list.csv")
    
    if not os.path.exists(stock_list_path):
        print("❌ 股票列表文件不存在，请先运行 get_stock_list.py")
        return
    
    stock_df = pd.read_csv(stock_list_path)
    print("=" * 50)
    print(f"开始同步A股日线数据，共 {len(stock_df)} 只股票")
    print(f"数据保存目录: {data_dir}")
    print("=" * 50)
    
    success = 0
    failed = []
    
    for code in tqdm(stock_df["code"], desc="同步进度"):
        code = str(code).zfill(6)
        ok = sync_stock(code)
        if ok:
            success += 1
        else:
            failed.append(code)
        
        # 避免请求过快
        time.sleep(0.1)
    
    print("\n" + "=" * 50)
    print(f"✅ 同步完成: {success} 只股票")
    if failed:
        print(f"❌ 失败: {len(failed)} 只股票")
        print(f"失败股票: {failed[:10]}..." if len(failed) > 10 else f"失败股票: {failed}")
    print("=" * 50)


if __name__ == "__main__":
    main()
