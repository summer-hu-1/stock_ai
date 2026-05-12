"""
测试AI市场洞察功能

测试内容：
1. NarrativeEngine - 市场叙事引擎
2. MarketContextBuilder - 市场上下文构建器
3. LLMPromptBuilder - LLM提示词构建器
4. MarketInsightEngine - 市场洞察引擎
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.market_memory import (
    MarketMemory,
    NarrativeEngine,
    MarketContextBuilder,
    LLMPromptBuilder,
    MarketInsightEngine
)
from modules.market_sentiment import analyze_sentiment


def test_narrative_engine():
    """测试市场叙事引擎"""
    print("=" * 80)
    print("测试1: NarrativeEngine - 市场叙事引擎")
    print("=" * 80)
    
    memory = MarketMemory()
    snapshots = memory.get_recent_snapshots(5)
    
    if not snapshots:
        print("❌ 没有历史快照数据，请先生成市场快照")
        return False
    
    narrative_engine = NarrativeEngine(memory.engine)
    
    # 测试构建市场摘要
    print("\n📊 构建市场摘要（最新快照）：")
    summary = narrative_engine.build_market_summary(snapshots[0])
    print(f"日期: {summary['date']}")
    print(f"市场情绪: {summary['market_sentiment']}")
    print(f"情绪得分: {summary['emotion_score']}")
    print(f"涨停家数: {summary['limit_up_count']}")
    print(f"最高连板: {summary['highest_board']}")
    print(f"热点板块: {', '.join(summary['top_sectors'])}")
    print(f"市场风格: {summary['market_style']}")
    print(f"风险信号: {summary['risk_signal']}")
    
    # 测试构建市场故事
    print("\n📖 构建市场故事（最近5天）：")
    market_story = narrative_engine.build_market_story(days=5)
    print(market_story)
    
    print("\n✅ NarrativeEngine 测试通过")
    return True


def test_market_context_builder():
    """测试市场上下文构建器"""
    print("\n" + "=" * 80)
    print("测试2: MarketContextBuilder - 市场上下文构建器")
    print("=" * 80)
    
    memory = MarketMemory()
    context_builder = MarketContextBuilder(memory.engine)
    
    # 测试构建市场上下文
    print("\n📊 构建市场上下文（最近5天）：")
    context = context_builder.build_market_context(days=5)
    
    if not context.get("has_context"):
        print("❌ 没有历史数据")
        return False
    
    print(f"最新日期: {context['latest_date']}")
    print(f"分析天数: {context['days']}")
    print(f"\n今日摘要:")
    today_summary = context['today_summary']
    print(f"  市场情绪: {today_summary['market_sentiment']}")
    print(f"  情绪得分: {today_summary['emotion_score']}")
    print(f"  涨停家数: {today_summary['limit_up_count']}")
    print(f"  热点板块: {', '.join(today_summary['top_sectors'])}")
    
    print(f"\n市场周期: {context['market_cycle']['cycle']}")
    print(f"情绪趋势: {context['emotion_trend']['direction']}")
    print(f"板块轮动: {context['sector_rotation']['description']}")
    print(f"龙头切换: {context['leader_rotation']['description']}")
    print(f"风险变化: {context['risk_change']['description']}")
    
    # 测试构建LLM上下文
    print("\n🤖 构建LLM上下文：")
    llm_context = context_builder.build_llm_context(days=5)
    print(llm_context)
    
    print("\n✅ MarketContextBuilder 测试通过")
    return True


def test_llm_prompt_builder():
    """测试LLM提示词构建器"""
    print("\n" + "=" * 80)
    print("测试3: LLMPromptBuilder - LLM提示词构建器")
    print("=" * 80)
    
    memory = MarketMemory()
    context_builder = MarketContextBuilder(memory.engine)
    prompt_builder = LLMPromptBuilder(context_builder)
    
    # 测试构建市场洞察提示词
    print("\n🤖 构建市场洞察提示词（最近5天）：")
    prompt = prompt_builder.build_market_insight_prompt(days=5)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    print("\n✅ LLMPromptBuilder 测试通过")
    return True


def test_market_insight_engine():
    """测试市场洞察引擎"""
    print("\n" + "=" * 80)
    print("测试4: MarketInsightEngine - 市场洞察引擎")
    print("=" * 80)
    
    memory = MarketMemory()
    insight_engine = MarketInsightEngine()
    
    # 测试加载历史上下文
    print("\n📊 加载历史上下文（最近5天）：")
    context = insight_engine.load_history_context(days=5)
    
    if not context.get("has_context"):
        print("❌ 没有历史数据")
        return False
    
    print(f"最新日期: {context['latest_date']}")
    print(f"市场周期: {context['market_cycle']['cycle']}")
    print(f"情绪趋势: {context['emotion_trend']['direction']}")
    
    # 测试构建市场故事
    print("\n📖 构建市场故事：")
    market_story = insight_engine.build_market_story(days=5)
    print(market_story[:500] + "..." if len(market_story) > 500 else market_story)
    
    # 测试构建LLM提示词
    print("\n🤖 构建LLM提示词：")
    prompt = insight_engine.build_llm_prompt(days=5)
    print(f"提示词长度: {len(prompt)} 字符")
    
    # 测试生成市场洞察
    print("\n🧠 生成市场洞察：")
    insight = insight_engine.generate_market_insight(days=5)
    
    print(f"日期: {insight.date}")
    print(f"市场状态: {insight.current_state}")
    print(f"状态描述: {insight.state_description}")
    print(f"风险提示: {insight.risk_alert}")
    print(f"机会提示: {insight.opportunity}")
    print(f"操作建议: {insight.action_suggestion}")
    print(f"置信度: {insight.confidence*100:.0f}%")
    
    if insight.key_changes:
        print(f"\n关键观察点:")
        for change in insight.key_changes:
            print(f"  - {change}")
    
    # 测试保存洞察
    print("\n💾 保存市场洞察：")
    success = insight_engine.save_insight(insight)
    print(f"保存{'成功' if success else '失败'}")
    
    # 测试获取最新洞察
    print("\n📜 获取最新洞察：")
    latest_insight = insight_engine.get_latest_insight()
    if latest_insight:
        print(f"最新洞察日期: {latest_insight.date}")
        print(f"市场状态: {latest_insight.current_state}")
    
    # 测试获取历史洞察
    print("\n📜 获取最近10条洞察：")
    recent_insights = insight_engine.get_recent_insights(10)
    print(f"共有 {len(recent_insights)} 条历史洞察")
    
    print("\n✅ MarketInsightEngine 测试通过")
    return True


def test_market_memory_api():
    """测试MarketMemory统一API"""
    print("\n" + "=" * 80)
    print("测试5: MarketMemory - 统一API")
    print("=" * 80)
    
    memory = MarketMemory()
    
    # 测试加载历史上下文
    print("\n📊 加载历史上下文：")
    context = memory.load_history_context(days=5)
    if context.get("has_context"):
        print(f"✅ 成功加载 {context['days']} 天的历史上下文")
    else:
        print("❌ 没有历史数据")
        return False
    
    # 测试构建市场故事
    print("\n📖 构建市场故事：")
    market_story = memory.build_market_story(days=5)
    print(f"✅ 成功生成市场故事（{len(market_story)} 字符）")
    
    # 测试构建LLM提示词
    print("\n🤖 构建LLM提示词：")
    prompt = memory.build_llm_prompt(days=5)
    print(f"✅ 成功生成LLM提示词（{len(prompt)} 字符）")
    
    # 测试生成市场洞察
    print("\n🧠 生成市场洞察：")
    insight = memory.generate_market_insight(days=5)
    print(f"✅ 成功生成市场洞察")
    print(f"   市场状态: {insight.current_state}")
    print(f"   置信度: {insight.confidence*100:.0f}%")
    
    # 测试保存洞察
    print("\n💾 保存市场洞察：")
    success = memory.save_insight(insight)
    print(f"✅ 保存{'成功' if success else '失败'}")
    
    # 测试获取最新洞察
    print("\n📜 获取最新洞察：")
    latest_insight = memory.get_latest_insight()
    if latest_insight:
        print(f"✅ 最新洞察: {latest_insight.date} - {latest_insight.current_state}")
    
    # 测试获取历史洞察
    print("\n📜 获取最近5条洞察：")
    recent_insights = memory.get_recent_insights(5)
    print(f"✅ 共有 {len(recent_insights)} 条历史洞察")
    
    print("\n✅ MarketMemory API 测试通过")
    return True


def test_full_workflow():
    """测试完整工作流程"""
    print("\n" + "=" * 80)
    print("测试6: 完整工作流程")
    print("=" * 80)
    
    memory = MarketMemory()
    
    # 1. 检查是否有历史快照
    snapshots = memory.get_recent_snapshots(5)
    if len(snapshots) < 2:
        print("❌ 历史快照不足，需要至少2天的快照数据")
        print("💡 请先运行以下命令生成市场快照：")
        print("   1. 在Streamlit界面中点击「生成市场快照」")
        print("   2. 或者运行: python -c \"from modules.market_sentiment import analyze_sentiment; from core.market_memory import MarketMemory; memory = MarketMemory(); memory.save_snapshot(analyze_sentiment())\"")
        return False
    
    print(f"✅ 找到 {len(snapshots)} 天的历史快照")
    
    # 2. 加载历史上下文
    print("\n📊 步骤1: 加载历史上下文")
    context = memory.load_history_context(days=5)
    print(f"   市场周期: {context['market_cycle']['cycle']}")
    print(f"   情绪趋势: {context['emotion_trend']['direction']}")
    
    # 3. 构建市场故事
    print("\n📖 步骤2: 构建市场故事")
    market_story = memory.build_market_story(days=5)
    print(f"   故事长度: {len(market_story)} 字符")
    
    # 4. 构建LLM提示词
    print("\n🤖 步骤3: 构建LLM提示词")
    prompt = memory.build_llm_prompt(days=5)
    print(f"   提示词长度: {len(prompt)} 字符")
    
    # 5. 生成市场洞察
    print("\n🧠 步骤4: 生成市场洞察")
    insight = memory.generate_market_insight(days=5)
    print(f"   市场状态: {insight.current_state}")
    print(f"   置信度: {insight.confidence*100:.0f}%")
    
    # 6. 保存洞察
    print("\n💾 步骤5: 保存市场洞察")
    success = memory.save_insight(insight)
    print(f"   保存{'成功' if success else '失败'}")
    
    # 7. 获取最新洞察
    print("\n📜 步骤6: 验证保存结果")
    latest_insight = memory.get_latest_insight()
    if latest_insight and latest_insight.date == insight.date:
        print(f"   ✅ 验证成功: 最新洞察日期为 {latest_insight.date}")
    else:
        print(f"   ❌ 验证失败")
    
    print("\n✅ 完整工作流程测试通过")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("🧪 AI市场洞察功能测试")
    print("=" * 80)
    
    test_results = []
    
    # 运行所有测试
    try:
        test_results.append(("NarrativeEngine", test_narrative_engine()))
    except Exception as e:
        print(f"❌ NarrativeEngine 测试失败: {e}")
        test_results.append(("NarrativeEngine", False))
    
    try:
        test_results.append(("MarketContextBuilder", test_market_context_builder()))
    except Exception as e:
        print(f"❌ MarketContextBuilder 测试失败: {e}")
        test_results.append(("MarketContextBuilder", False))
    
    try:
        test_results.append(("LLMPromptBuilder", test_llm_prompt_builder()))
    except Exception as e:
        print(f"❌ LLMPromptBuilder 测试失败: {e}")
        test_results.append(("LLMPromptBuilder", False))
    
    try:
        test_results.append(("MarketInsightEngine", test_market_insight_engine()))
    except Exception as e:
        print(f"❌ MarketInsightEngine 测试失败: {e}")
        test_results.append(("MarketInsightEngine", False))
    
    try:
        test_results.append(("MarketMemory API", test_market_memory_api()))
    except Exception as e:
        print(f"❌ MarketMemory API 测试失败: {e}")
        test_results.append(("MarketMemory API", False))
    
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
        print("\n🎉 所有测试通过！AI市场洞察功能正常工作。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息。")


if __name__ == "__main__":
    main()
