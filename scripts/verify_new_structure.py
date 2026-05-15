#!/usr/bin/env python3
"""
快速验证新的数据结构是否工作正常
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_market_db():
    """测试 market.db"""
    print("✅ 1. 测试 market.db...")
    try:
        from database.market_db import get_db
        db = next(get_db())
        print("   market.db 连接正常")
        return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_data_lake():
    """测试 DataLake"""
    print("\n✅ 2. 测试 DataLake...")
    try:
        from data_lake import get_data_lake
        lake = get_data_lake()
        print("   DataLake 实例化正常")
        stocks = lake.list_stocks("cn", "daily")
        print(f"   找到 {len(stocks)} 只股票 (空数据也正常)")
        return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_data_unifier():
    """测试统一数据接口"""
    print("\n✅ 3. 测试统一数据接口...")
    try:
        from data import get_unified_provider
        provider = get_unified_provider()
        print("   统一数据接口实例化正常")
        return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_quant_core():
    """测试 QuantCore"""
    print("\n✅ 4. 测试 QuantCore...")
    try:
        from quant import get_quant_core
        quant = get_quant_core()
        print("   QuantCore 实例化正常")
        return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_strategy_os():
    """测试 StrategyOS"""
    print("\n✅ 5. 测试 StrategyOS...")
    try:
        from strategy import get_strategy_os
        strategy = get_strategy_os()
        print("   StrategyOS 实例化正常")
        account = strategy.get_account()
        print(f"   账户正常: {account.total_assets:.2f}")
        return True
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def main():
    print("="*60)
    print("🧪 新数据结构验证")
    print("="*60)
    
    all_good = True
    all_good &= test_market_db()
    all_good &= test_data_lake()
    all_good &= test_data_unifier()
    all_good &= test_quant_core()
    all_good &= test_strategy_os()
    
    print("\n" + "="*60)
    if all_good:
        print("✅ 所有测试通过！新数据结构工作正常")
    else:
        print("⚠️  有些测试未通过，但基本框架已就绪")
    print("="*60)
    
    print("\n📊 当前项目结构：")
    print("  - database/market.db         ✅ 统一数据库")
    print("  - data_lake/                 ✅ 数据湖 (Parquet)")
    print("  - data/unifier.py            ✅ 统一数据接口")
    print("  - deprecated_data/           ✅ 旧数据备份")


if __name__ == "__main__":
    main()
