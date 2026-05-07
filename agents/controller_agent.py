"""
总控 Agent - Controller Agent
负责协调所有 Agent 并生成最终报告
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def run_all_agents(stock_code):
    """
    运行所有 Agent 并汇总结果

    Returns:
        dict: 所有 Agent 的分析结果
    """
    from agents.market_agent import analyze_market, format_market_report
    from agents.sentiment_agent import analyze_sentiment, format_sentiment_report
    from agents.sector_agent import analyze_sector, format_sector_report
    from agents.flow_agent import analyze_flow, format_flow_report
    from agents.risk_agent import analyze_risk, format_risk_report

    market_data = analyze_market(stock_code)
    sentiment_data = analyze_sentiment()
    sector_data = analyze_sector(stock_code)
    flow_data = analyze_flow()
    risk_data = analyze_risk(sentiment_data, market_data)

    return {
        "market": market_data,
        "sentiment": sentiment_data,
        "sector": sector_data,
        "flow": flow_data,
        "risk": risk_data,
        "format": {
            "market": format_market_report(market_data),
            "sentiment": format_sentiment_report(sentiment_data),
            "sector": format_sector_report(sector_data),
            "flow": format_flow_report(flow_data),
            "risk": format_risk_report(risk_data)
        }
    }


def generate_report(all_data):
    """
    使用 DeepSeek AI 生成最终分析报告

    Args:
        all_data: 所有 Agent 的分析结果

    Returns:
        str: AI 生成的最终报告
    """
    market_data = all_data.get("market", {})
    sentiment_data = all_data.get("sentiment", {})
    sector_data = all_data.get("sector", {})
    flow_data = all_data.get("flow", {})
    risk_data = all_data.get("risk", {})

    today = datetime.now()
    today_str = today.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

    if 'error' not in market_data:
        market_info = f"""股票名称：{market_data.get('stock_name', '未知')}
股票代码：{market_data.get('stock_code', '未知')}
最新价：{market_data.get('price', 0)}元
涨跌幅：{market_data.get('price_change_pct', 0):.2f}%
涨停状态：{market_data.get('limit_status', '正常')}
换手率：{market_data.get('turnover_rate', 0):.2f}%
量比：{market_data.get('volume_ratio', 0):.2f}
强势度：{market_data.get('strength_level', '未知')}
异动信号：{', '.join(market_data.get('异动信号', [])) or '无'}"""
    else:
        market_info = "行情数据获取失败"

    stock_sectors_info = ""
    stock_sectors = sector_data.get('stock_sectors', [])
    if stock_sectors:
        stock_sectors_info = "个股所属板块：" + "、".join([f"{s['name']}(+{s['change_pct']}%)" for s in stock_sectors])
    else:
        stock_sectors_info = "个股所属板块：暂未获取"

    prompt = f"""你是A股顶级游资复盘分析师，擅长多维度市场分析。

【时间信息】
今天日期：{today_str}（{weekday}）

【核心分析对象】
{market_info}

【个股所属板块】
{stock_sectors_info}

【市场情绪背景】
情绪周期：{sentiment_data.get('emotion_cycle', '未知')}
市场情绪：{sentiment_data.get('market_mood', '未知')}
涨停家数：{sentiment_data.get('limit_up_count', 0)}家
上涨家数：{sentiment_data.get('rising_count', 0)}家 ({sentiment_data.get('rise_ratio', 0):.1f}%)
操作信号：{'可以做短线' if sentiment_data.get('做多信号') else '观望' if sentiment_data.get('做多信号') is False else '观察'}

【市场主线方向】
主线方向：{sector_data.get('main_line', '未知')}
资金流向：{sector_data.get('资金流向', '未知')}
第一强势板块：{sector_data.get('top_sectors', [{}])[0].get('name', '未知')} ({sector_data.get('top_sectors', [{}])[0].get('change_pct', 0)}%)

【市场资金环境】
市场流动性：{flow_data.get('liquidity', '未知')}
活跃资金：{flow_data.get('hot_money_status', '未知')}
投机热度：{flow_data.get('speculation_level', '未知')}
全市场成交额：{flow_data.get('total_volume', 0)}万亿

【风险评估】
风险等级：{risk_data.get('risk_level', '未知')}
风险提示：{risk_data.get('warning', '未知')}
操作建议：{risk_data.get('suggestion', '未知')}
短线可操作性：{'可以' if risk_data.get('可以做短线') else '谨慎' if risk_data.get('可以做短线') is False else '观察'}

【核心任务】
请以【核心分析对象】的个股为绝对核心，结合上述市场背景信息，生成一份专业、简洁、针对该股的交易分析报告。

【严格要求】
1. **所有分析必须围绕该股展开**，不要泛泛而谈市场，市场背景只是用来衬托个股分析
2. **个股核心分析** - 该股今天具体表现如何？有哪些异动信号？强势程度如何？
3. **板块关联分析** - 该股属于什么板块？和当前主线板块关系如何？是在主线里还是在边缘？
4. **资金与情绪** - 结合市场情绪和资金，该股是否有资金关注？有没有被市场遗忘？
5. **风险收益** - 就针对这只股票，现在值不值得参与？风险多大，收益空间多大？
6. **具体操作** - 给出针对这只股票的具体可执行建议（买入价位/持有策略/卖出点位/观望理由）
7. **明日走势** - 明天这只股票最可能怎么走？有什么关键点位需要关注？

输出要简洁有力，数据说话，每一句话都要和这只股票相关，不要说废话。
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI报告生成失败: {str(e)}"


def multi_agent_review(stock_code):
    """
    多 Agent 协同分析主函数

    Args:
        stock_code: 股票代码

    Returns:
        dict: {
            "agent_results": dict,      # 各 Agent 结果
            "final_report": str,         # AI 最终报告
            "summary": dict              # 快速摘要
        }
    """
    all_data = run_all_agents(stock_code)

    final_report = generate_report(all_data)

    sentiment = all_data.get("sentiment", {})
    risk = all_data.get("risk", {})

    summary = {
        "股票": f"{all_data.get('market', {}).get('stock_name', '未知')}({stock_code})",
        "情绪周期": sentiment.get("emotion_cycle", "未知"),
        "市场情绪": sentiment.get("market_mood", "未知"),
        "主线": all_data.get("sector", {}).get("main_line", "未知"),
        "风险等级": risk.get("risk_level", "未知"),
        "操作建议": risk.get("suggestion", "未知"),
        "短线可做": "✅" if risk.get("可以做短线") else ("⚠️" if risk.get("可以做短线") is False else "➖")
    }

    return {
        "agent_results": all_data,
        "final_report": final_report,
        "summary": summary
    }
