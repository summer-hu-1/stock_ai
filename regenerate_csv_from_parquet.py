#!/usr/bin/env python3
"""
从Parquet文件重新生成CSV数据
"""

import os
import pandas as pd
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据目录
PARQUET_DIR = BASE_DIR / "datalake" / "cn" / "daily"
CSV_DIR = BASE_DIR / "data" / "cn" / "daily"

SUB_DIRS = {
    '000': 'sz_main', '001': 'sz_main', '002': 'sz_sme', '003': 'sz_main',
    '300': 'sz_gem', '301': 'sz_gem',
    '600': 'sh_main', '601': 'sh_main', '603': 'sh_main', '605': 'sh_main',
    '688': 'sh_star', '689': 'sh_star',
}

def get_sub_dir(code: str) -> str:
    prefix = code[:3]
    return SUB_DIRS.get(prefix, 'unknown')

def regenerate_csv():
    """从Parquet文件重新生成CSV数据"""
    print("🔄 从Parquet重新生成CSV数据...")
    
    # 确保CSV目录存在
    for subdir in SUB_DIRS.values():
        (CSV_DIR / subdir).mkdir(parents=True, exist_ok=True)
    (CSV_DIR / 'unknown').mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    # 遍历SH和SZ目录
    for market_dir in ['SH', 'SZ']:
        market_path = PARQUET_DIR / market_dir
        if not market_path.exists():
            continue
        
        for parquet_file in market_path.glob("*.parquet"):
            try:
                # 读取Parquet文件
                df = pd.read_parquet(parquet_file)
                
                # 获取股票代码（去掉.parquet后缀）
                code = parquet_file.stem
                
                # 确定目标子目录
                sub_dir = get_sub_dir(code)
                
                # 确保日期列格式正确
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                
                # App所需的列名
                required_columns = [
                    'date', 'open', 'high', 'low', 'close', 
                    'volume', 'amount', 'turnover_rate', 
                    'price_change_pct', 'amplitude'
                ]
                
                # 选择存在的列，确保顺序正确
                available_cols = [col for col in required_columns if col in df.columns]
                df = df[available_cols]
                
                # 写入CSV
                csv_path = CSV_DIR / sub_dir / f"{code}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8')
                
                success_count += 1
                
            except Exception as e:
                print(f"  ⚠️ 处理 {parquet_file} 失败: {e}")
                fail_count += 1
    
    print(f"✅ 完成! 成功: {success_count}, 失败: {fail_count}")
    return success_count, fail_count

def verify_regenerated_data():
    """验证重新生成的数据"""
    print("\n🔍 验证重新生成的数据...")
    
    csv_count = sum(1 for _ in CSV_DIR.rglob("*.csv"))
    parquet_count = sum(1 for _ in PARQUET_DIR.rglob("*.parquet"))
    
    print(f"   CSV文件数量: {csv_count}")
    print(f"   Parquet文件数量: {parquet_count}")
    
    # 检查几个关键股票的数据
    test_codes = ['600519', '000001', '002624']
    for code in test_codes:
        found = False
        for csv_path in CSV_DIR.rglob(f"{code}.csv"):
            df = pd.read_csv(csv_path)
            print(f"   ✅ {code} 数据存在: {csv_path.parent.name}, 行数: {len(df)}")
            found = True
            break
        if not found:
            print(f"   ❌ {code} 数据缺失")
    
    print("✅ 验证完成")

def main():
    print("=" * 60)
    print("🔄 从Parquet重新生成CSV数据")
    print("=" * 60)
    
    # 1. 重新生成CSV
    success, fail = regenerate_csv()
    
    # 2. 验证数据
    verify_regenerated_data()
    
    print("\n" + "=" * 60)
    print("✅ CSV数据重新生成完成!")
    print(f"📌 新数据位置: data/cn/daily/")
    print(f"📌 生成文件: {success} 个")
    print("=" * 60)

if __name__ == "__main__":
    main()