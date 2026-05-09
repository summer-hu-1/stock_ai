#!/usr/bin/env python3
"""
获取A股股票列表

运行: python data_sync/get_stock_list.py
"""

import akshare as ak
import pandas as pd
import os

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn")

os.makedirs(data_dir, exist_ok=True)


def main():
    print("=" * 50)
    print("开始获取A股股票列表...")
    print("=" * 50)
    
    try:
        # 禁用代理
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        
        df = ak.stock_info_a_code_name()
        df.columns = ["code", "name"]
        
        save_path = os.path.join(data_dir, "stock_list.csv")
        df.to_csv(save_path, index=False)
        
        print(f"\n✅ 完成，共 {len(df)} 只股票")
        print(f"📁 保存位置: {save_path}")
        
        # 显示前10只股票
        print("\n前10只股票:")
        print(df.head(10).to_string(index=False))
        
    except Exception as e:
        print(f"\n❌ 获取失败: {e}")
        raise


if __name__ == "__main__":
    main()