"""
风险 Agent - Risk Agent
负责市场风险评估
"""
import akshare as ak
import pandas as pd


def analyze_risk(sentiment_data=None, market_data=None):
    """
    分析市场风险

    Args:
        sentiment_data: 情绪 Agent 输出
        market_data: 行情 Agent 输出

    Returns:
        dict: {
            "risk_level": str,         # 高/中/低
            "main_risks": list,        # 主要风险
            "warning": str,            # 风险提示
            "suggestion": str,         # 建议
            "可以做短线": bool
        }
    """
    try:
        if sentiment_data is None:
            df = ak.stock_zh_a_spot_em()
            limit_down = len(df[df["涨跌幅"] <= -9.8])
            limit_up = len(df[df["涨跌幅"] >= 9.8])
            avg_change = df["涨跌幅"].mean()
        else:
            limit_down = sentiment_data.get("limit_down_count", 0)
            limit_up = sentiment_data.get("limit_up_count", 0)
            avg_change = sentiment_data.get("avg_change", 0)

        main_risks = []

        if limit_down > 30:
            main_risks.append("跌停家数过多")
            risk_level = "高"
        elif limit_down > 15:
            main_risks.append("跌停扩散")
            risk_level = "中高"

        if avg_change < -1:
            main_risks.append("市场整体下跌")
            risk_level = risk_level if 'risk_level' in dir() else "高"

        if limit_up < 20:
            main_risks.append("涨停家数过少")
            if 'risk_level' not in dir():
                risk_level = "高"

        if market_data:
            if market_data.get("price_change_pct", 0) > 9.9:
                main_risks.append("高位追涨风险")

            if market_data.get("turnover_rate", 0) > 20:
                main_risks.append("换手率过高")

        if 'risk_level' not in dir():
            if limit_up > 50 and avg_change > 1:
                risk_level = "低"
            elif limit_up > 30:
                risk_level = "中低"
            else:
                risk_level = "中"

        if risk_level == "高":
            warning = "市场风险较高，谨慎操作"
            suggestion = "建议空仓或轻仓观望"
            可以做短线 = False
        elif risk_level == "中高":
            warning = "市场存在风险，注意控制仓位"
            suggestion = "谨慎追高，关注确定性机会"
            可以做短线 = None
        elif risk_level == "中低":
            warning = "市场机会与风险并存"
            suggestion = "可轻仓参与主线龙头"
            可以做短线 = True
        else:
            warning = "市场情绪良好，短线机会较多"
            suggestion = "积极参与主线龙头，注意轮动"
            可以做短线 = True

        return {
            "risk_level": risk_level,
            "main_risks": main_risks if main_risks else ["无明显风险"],
            "warning": warning,
            "suggestion": suggestion,
            "可以做短线": 可以做短线
        }

    except Exception as e:
        return {"error": str(e)}


def format_risk_report(risk_data):
    """格式化风险报告"""
    if "error" in risk_data:
        return f"风险数据获取失败: {risk_data['error']}"

    risk_emoji = {
        "高": "🔴",
        "中高": "🟠",
        "中": "🟡",
        "中低": "🟢",
        "低": "✅"
    }.get(risk_data["risk_level"], "❓")

    lines = [
        f"【风险分析】{risk_emoji} 风险等级: {risk_data['risk_level']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"主要风险点:",
    ]

    for risk in risk_data["main_risks"]:
        lines.append(f"  • {risk}")

    lines.extend([
        f"━━━━━━━━━━━━━━━━━━━━",
        f"风险提示: {risk_data['warning']}",
        f"操作建议: {risk_data['suggestion']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"短线可操作性: {'✅ 可以' if risk_data.get('可以做短线') == True else ('⚠️ 谨慎' if risk_data.get('可以做短线') == False else '➖ 观察')}",
    ])

    return "\n".join(lines)
