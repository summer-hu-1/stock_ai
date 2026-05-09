#!/usr/bin/env python3
"""
增量更新A股日线数据

运行: python data_sync/update_cn_daily.py

功能：
- 只更新最新交易日的数据
- 增量追加到现有CSV文件
- 自动跳过无变化的股票
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


def update_stock(code, max_retries=3):
    """
    增量更新单只股票的日线数据
    
    Args:
        code: 股票代码
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否有更新
    """
    path = f"{data_dir}/{code}.csv"
    
    if not os.path.exists(path):
        print(f"{code}: 文件不存在，请先运行 sync_cn_daily.py")
        return False
    
    for attempt in range(max_retries):
        try:
            # 禁用代理
            os.environ['HTTP_PROXY'] = ''
            os.environ['HTTPS_PROXY'] = ''
            os.environ['http_proxy'] = ''
            os.environ['https_proxy'] = ''
            
            # 读取本地数据，获取最后日期
            local_df = pd.read_csv(path)
            last_date = local_df["date"].iloc[-1]
            last_date = str(last_date).replace("-", "")
            
            # 获取最新数据（从最后一个日期开始）
            new_df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=last_date,
                adjust="qfq"
            )
            
            if new_df is None or new_df.empty:
                return False
            
            # 重命名列
            new_df = new_df.rename(columns=COLUMN_MAPPING)
            
            # 只保留需要的列
            available_cols = [col for col in KEEP_COLUMNS if col in new_df.columns]
            new_df = new_df[available_cols]
            
            # 过滤掉最后一个日期（已存在）
            new_df = new_df[new_df["date"] > last_date]
            
            if new_df.empty:
                return False
            
            # 合并数据
            df = pd.concat([local_df, new_df])
            
            # 去重
            df.drop_duplicates(subset=["date"], inplace=True)
            
            # 按日期排序
            df = df.sort_values("date")
            
            # 保存
            df.to_csv(path, index=False)
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"{code} 更新失败: {e}")
                return False
    
    return False


def main():
    stock_list_path = os.path.join(project_dir, "data", "cn", "stock_list.csv")
    
    if not os.path.exists(stock_list_path):
        print("❌ 股票列表文件不存在，请先运行 get_stock_list.py")
        return
    
    stock_df = pd.read_csv(stock_list_path)
    print("=" * 50)
    print(f"开始增量更新A股日线数据，共 {len(stock_df)} 只股票")
    print(f"数据目录: {data_dir}")
    print("=" * 50)
    
    updated = 0
    skipped = 0
    
    for code in tqdm(stock_df["code"], desc="更新进度"):
        code = str(code).zfill(6)
        
        path = f"{data_dir}/{code}.csv"
        if not os.path.exists(path):
            skipped += 1
            continue
        
        ok = update_stock(code)
        if ok:
            updated += 1
        
        # 避免请求过快
        time.sleep(0.1)
    
    print("\n" + "=" * 50)
    print(f"✅ 更新完成: {updated} 只股票已更新")
    print(f"⏭️ 跳过(无文件): {skipped} 只股票")
    print("=" * 50)


if __name__ == "__main__":
    main()