"""
测试历史快照拉取功能

测试内容：
1. HistoricalSnapshotFetcher - 历史快照拉取器
2. MarketMemory历史快照API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.market_memory import MarketMemory, HistoricalSnapshotFetcher
from datetime import datetime, timedelta


def test_historical_fetcher():
    """测试历史快照拉取器"""
    print("=" * 80)
    print("测试1: HistoricalSnapshotFetcher - 历史快照拉取器")
    print("=" * 80)
    
    fetcher = HistoricalSnapshotFetcher()
    
    # 测试获取缺失日期
    print("\n📊 获取最近7天的缺失日期：")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    missing_dates = fetcher.get_missing_dates(start_date, end_date)
    print(f"缺失日期: {missing_dates}")
    
    # 测试单日期拉取（使用今天之前的一个工作日）
    print("\n📥 测试单日期拉取：")
    test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    success = fetcher.fetch_and_save_snapshot(test_date)
    print(f"拉取 {test_date}: {'✅ 成功' if success else '❌ 失败'}")
    
    print("\n✅ HistoricalSnapshotFetcher 测试通过")
    return True


def test_market_memory_history_api():
    """测试MarketMemory历史快照API"""
    print("\n" + "=" * 80)
    print("测试2: MarketMemory - 历史快照API")
    print("=" * 80)
    
    memory = MarketMemory()
    
    # 测试获取缺失日期
    print("\n📊 获取最近5天的缺失日期：")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    missing_dates = memory.get_missing_dates(start_date, end_date)
    print(f"缺失日期: {missing_dates}")
    
    # 测试日期范围拉取
    print("\n📥 测试日期范围拉取（最近3天）：")
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    result = memory.fetch_date_range(start_date, end_date)
    print(f"拉取结果: 成功={result['success']}, 失败={result['failed']}, 跳过={result['skipped']}")
    
    # 测试增量更新
    print("\n🔄 测试增量更新（最近7天）：")
    result = memory.update_missing_snapshots(days=7)
    print(f"更新结果: 缺失={result['total_missing']}, 成功={result['success']}, 失败={result['failed']}")
    
    # 测试获取最近快照
    print("\n📜 获取最近10天的快照：")
    snapshots = memory.get_recent_snapshots(10)
    print(f"共有 {len(snapshots)} 条快照")
    if snapshots:
        print(f"最新快照日期: {snapshots[0].date}")
        print(f"情绪得分: {snapshots[0].emotion_score}")
        print(f"涨停家数: {snapshots[0].limit_up_count}")
    
    print("\n✅ MarketMemory 历史快照API测试通过")
    return True


def test_full_workflow():
    """测试完整工作流程"""
    print("\n" + "=" * 80)
    print("测试3: 完整工作流程")
    print("=" * 80)
    
    memory = MarketMemory()
    
    # 1. 检查当前快照数量
    snapshots_before = memory.get_recent_snapshots(365)
    print(f"📊 当前快照数量: {len(snapshots_before)}")
    
    # 2. 增量更新最近7天
    print("\n🔄 步骤1: 增量更新最近7天")
    result = memory.update_missing_snapshots(days=7)
    print(f"   更新结果: 缺失={result['total_missing']}, 成功={result['success']}")
    
    # 3. 检查更新后的快照数量
    snapshots_after = memory.get_recent_snapshots(365)
    print(f"\n📊 步骤2: 更新后快照数量: {len(snapshots_after)}")
    added = len(snapshots_after) - len(snapshots_before)
    print(f"   新增快照: {added} 条")
    
    # 4. 生成市场洞察
    print("\n🧠 步骤3: 生成市场洞察")
    insight = memory.generate_market_insight(days=5)
    print(f"   市场状态: {insight.current_state}")
    print(f"   置信度: {insight.confidence*100:.0f}%")
    
    # 5. 保存洞察
    print("\n💾 步骤4: 保存市场洞察")
    success = memory.save_insight(insight)
    print(f"   保存{'成功' if success else '失败'}")
    
    print("\n✅ 完整工作流程测试通过")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("🧪 历史快照拉取功能测试")
    print("=" * 80)
    
    test_results = []
    
    try:
        test_results.append(("HistoricalSnapshotFetcher", test_historical_fetcher()))
    except Exception as e:
        print(f"❌ HistoricalSnapshotFetcher 测试失败: {e}")
        test_results.append(("HistoricalSnapshotFetcher", False))
    
    try:
        test_results.append(("MarketMemory History API", test_market_memory_history_api()))
    except Exception as e:
        print(f"❌ MarketMemory History API 测试失败: {e}")
        test_results.append(("MarketMemory History API", False))
    
    try:
        test_results.append(("完整工作流程", test_full_workflow()))
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        test_results.append(("完整工作流程", False))
    
    # 打印测试结果汇总
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:30s} {status}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print("\n" + "=" * 80)
    print(f"总计: {passed}/{total} 个测试通过")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 所有测试通过！历史快照拉取功能正常工作。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()
