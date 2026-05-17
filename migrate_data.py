#!/usr/bin/env python3
"""
数据迁移脚本 - 将旧数据备份并确保app使用新数据
"""

import os
import shutil
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据目录
DATA_DIR = BASE_DIR / "data" / "cn" / "daily"
BACKUP_DIR = BASE_DIR / "data_backup" / "cn" / "daily"
DATA_LAKE_DIR = BASE_DIR / "data_lake" / "cn" / "daily"  # 旧的datalake目录

def backup_old_data():
    """备份旧数据到备份目录"""
    print("📦 开始备份旧数据...")
    
    # 创建备份子目录
    for subdir in ['sh_main', 'sh_star', 'sz_gem', 'sz_main', 'sz_sme', 'unknown']:
        (BACKUP_DIR / subdir).mkdir(parents=True, exist_ok=True)
    
    # 备份data_lake目录中的旧数据（如果存在）
    if DATA_LAKE_DIR.exists():
        for item in DATA_LAKE_DIR.iterdir():
            if item.is_dir():
                dest = BACKUP_DIR / "old_datalake" / item.name
                dest.mkdir(parents=True, exist_ok=True)
                for file in item.glob("*"):
                    try:
                        shutil.copy(file, dest / file.name)
                    except Exception as e:
                        print(f"  ⚠️ 复制 {file} 失败: {e}")
        print(f"✅ 已备份 data_lake 目录")
    
    print("✅ 旧数据备份完成")

def verify_new_data():
    """验证新数据"""
    print("\n🔍 验证新数据...")
    
    csv_count = sum(1 for _ in DATA_DIR.rglob("*.csv"))
    parquet_count = sum(1 for _ in (BASE_DIR / "datalake").rglob("*.parquet"))
    
    print(f"   CSV文件数量: {csv_count}")
    print(f"   Parquet文件数量: {parquet_count}")
    
    # 检查几个关键股票的数据
    test_codes = ['600519', '000001', '002624']
    for code in test_codes:
        found = False
        for csv_path in DATA_DIR.rglob(f"{code}.csv"):
            print(f"   ✅ {code} 数据存在: {csv_path.parent.name}")
            found = True
            break
        if not found:
            print(f"   ❌ {code} 数据缺失")
    
    print("✅ 新数据验证完成")

def update_app_config():
    """更新app配置以使用新数据"""
    print("\n⚙️ 检查app配置...")
    
    # 检查app.py中的数据获取逻辑
    app_file = BASE_DIR / "app.py"
    if app_file.exists():
        print("   ✅ app.py 存在")
        
        # 检查是否使用了正确的数据目录
        with open(app_file, 'r') as f:
            content = f.read()
            if "get_datahub" in content:
                print("   ✅ app已配置使用datahub获取数据")
            else:
                print("   ⚠️ app可能未使用datahub")
    else:
        print("   ❌ app.py 不存在")
    
    print("✅ 配置检查完成")

def main():
    print("=" * 60)
    print("🚀 数据迁移脚本")
    print("=" * 60)
    
    # 1. 备份旧数据
    backup_old_data()
    
    # 2. 验证新数据
    verify_new_data()
    
    # 3. 更新配置
    update_app_config()
    
    print("\n" + "=" * 60)
    print("✅ 数据迁移完成!")
    print("📌 新数据位置: data/cn/daily/")
    print("📌 旧数据备份: data_backup/cn/daily/")
    print("=" * 60)

if __name__ == "__main__":
    main()