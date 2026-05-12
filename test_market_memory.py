#!/usr/bin/env python3
"""
市场记忆功能测试脚本

测试内容：
1. 生成市场快照
2. 保存市场快照
3. 读取历史快照
4. 分析市场周期
5. 分析情绪趋势
6. 分析板块轮动
7. 分析龙头切换
8. 分析风险变化
9. 生成市场趋势
10. 获取市场上下文
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from modules.market_sentiment import get_market_sentiment
from core.market_memory import MarketMemory


def test_market_memory():
    """测试市场记忆功能"""
    print("=" * 60)
    print("市场记忆功能测试")
    print("=" * 60)
    
    # 初始化市场记忆
    memory = MarketMemory()
    
    # 步骤1：获取市场情绪数据
    print("\n[步骤1] 获取市场情绪数据...")
    sentiment_data = get_market_sentiment(use_cache=False)
    print(f"✅ 市场情绪数据：涨停{sentiment_data['limit_up_count']}家，情绪{sentiment_data['market_mood']}")
    
    # 步骤2：生成市场快照
    print("\n[步骤2] 生成市场快照...")
    snapshot = memory.create_snapshot(sentiment_data)
    if snapshot:
        print(f"✅ 市场快照生成成功")
        print(f"   日期：{snapshot.date}")
        print(f"   市场情绪：{snapshot.market_sentiment}")
        print(f"   情绪得分：{snapshot.emotion_score}")
        print(f"   涨停家数：{snapshot.limit_up_count}")
        print(f"   风险等级：{snapshot.risk_level}")
        print(f"   市场周期：{snapshot.market_cycle}（{snapshot.cycle_stage}）")
        print(f"   热门板块：{', '.join(snapshot.top_sectors)}")
        print(f"   龙头股：{', '.join(snapshot.leaders)}")
    else:
        print("❌ 市场快照生成失败")
        return False
    
    # 步骤3：保存市场快照
    print("\n[步骤3] 保存市场快照...")
    success = memory.save_snapshot(sentiment_data)
    if success:
        print("✅ 市场快照保存成功")
    else:
        print("❌ 市场快照保存失败")
        return False
    
    # 步骤4：读取历史快照
    print("\n[步骤4] 读取历史快照...")
    snapshots = memory.get_recent_snapshots(7)
    print(f"✅ 获取到 {len(snapshots)} 条历史快照")
    
    # 步骤5：分析市场周期
    print("\n[步骤5] 分析市场周期...")
    market_cycle = memory.analyze_market_cycle(7)
    print(f"✅ 市场周期：{market_cycle['cycle']}（{market_cycle['stage']}）")
    print(f"   描述：{market_cycle['description']}")
    
    # 步骤6：分析情绪趋势
    print("\n[步骤6] 分析情绪趋势...")
    emotion_trend = memory.analyze_emotion_trend(5)
    print(f"✅ 情绪趋势：{emotion_trend['direction']}")
    print(f"   描述：{emotion_trend['description']}")
    if emotion_trend['trend']:
        print(f"   近5天情绪得分：{' → '.join([str(int(s)) for s in emotion_trend['trend']])}")
    
    # 步骤7：分析板块轮动
    print("\n[步骤7] 分析板块轮动...")
    sector_rotation = memory.analyze_sector_rotation(7)
    print(f"✅ 板块轮动：{sector_rotation['description']}")
    
    # 步骤8：分析龙头切换
    print("\n[步骤8] 分析龙头切换...")
    leader_rotation = memory.analyze_leader_rotation(5)
    print(f"✅ 龙头切换：{leader_rotation['description']}")
    
    # 步骤9：分析风险变化
    print("\n[步骤9] 分析风险变化...")
    risk_change = memory.analyze_risk_change(5)
    print(f"✅ 风险变化：{risk_change['description']}")
    
    # 步骤10：生成市场趋势
    print("\n[步骤10] 生成市场趋势...")
    market_trend = memory.generate_market_trend(7)
    print(f"✅ 市场趋势生成成功")
    print(f"   综合结论：{market_trend.conclusion}")
    
    # 步骤11：获取市场上下文
    print("\n[步骤11] 获取市场上下文...")
    context = memory.get_market_context(5)
    if context.get("has_context"):
        print(f"✅ 市场上下文获取成功")
        print(f"   最新日期：{context['latest_date']}")
        print(f"   市场周期：{context['market_cycle']['cycle']}")
        print(f"   情绪趋势：{context['emotion_trend']['direction']}")
    else:
        print(f"⚠️  {context.get('message', '暂无上下文')}")
    
    # 步骤12：格式化市场上下文
    print("\n[步骤12] 格式化市场上下文...")
    formatted_context = memory.format_market_context(5)
    print(f"✅ 格式化完成：\n{formatted_context}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_market_memory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
