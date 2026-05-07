"""
资金 Agent - Flow Agent
负责市场资金活跃度分析
"""
import akshare as ak
import pandas as pd


def analyze_flow():
    """
    分析市场资金状态

    Returns:
        dict: {
            "liquidity": str,           # 充足/一般/紧张
            "hot_money_status": str,    # 活跃/一般/低迷
            "speculation_level": str,    # 高/中/低
            "total_volume": float,       # 总成交额(万亿)
            "avg_turnover": float,       # 平均换手率
            "large_cap_status": str,     # 大盘股状态
            "small_cap_status": str,     # 小盘股状态
            "资金判断": str
        }
    """
    try:
        df = ak.stock_zh_a_spot_em()

        total_volume = df["成交额"].sum()
        total_volume万亿 = total_volume / 1e12

        avg_turnover = df["换手率"].mean()

        large_cap = df[df["总市值"] > 500e8] if "总市值" in df.columns else pd.DataFrame()
        small_cap = df[df["总市值"] < 100e8] if "总市值" in df.columns else pd.DataFrame()

        large_cap_status = "强势" if len(large_cap) > 0 and large_cap["涨跌幅"].mean() > 1 else ("弱势" if len(large_cap) > 0 and large_cap["涨跌幅"].mean() < -1 else "平稳")
        small_cap_status = "活跃" if len(small_cap) > 0 and small_cap["换手率"].mean() > 3 else ("低迷" if len(small_cap) > 0 and small_cap["换手率"].mean() < 1 else "一般")

        if total_volume万亿 > 3:
            liquidity = "充足"
        elif total_volume万亿 > 2:
            liquidity = "一般"
        else:
            liquidity = "紧张"

        if avg_turnover > 3:
            hot_money_status = "非常活跃"
        elif avg_turnover > 2:
            hot_money_status = "活跃"
        elif avg_turnover > 1:
            hot_money_status = "一般"
        else:
            hot_money_status = "低迷"

        strong_stocks = df[df["涨跌幅"] >= 5]
        speculation_level = "高" if len(strong_stocks) > 300 else ("中" if len(strong_stocks) > 150 else "低")

        if liquidity == "充足" and hot_money_status in ["活跃", "非常活跃"]:
            资金判断 = "市场资金活跃，短线机会多"
        elif liquidity == "紧张" or hot_money_status == "低迷":
            资金判断 = "市场资金紧张，谨慎操作"
        else:
            资金判断 = "市场资金一般，结构性机会"

        return {
            "liquidity": liquidity,
            "hot_money_status": hot_money_status,
            "speculation_level": speculation_level,
            "total_volume": round(total_volume万亿, 2),
            "avg_turnover": round(avg_turnover, 2),
            "large_cap_status": large_cap_status,
            "small_cap_status": small_cap_status,
            "strong_count": len(strong_stocks),
            "资金判断": 资金判断
        }

    except Exception as e:
        return {"error": str(e)}


def format_flow_report(flow_data):
    """格式化资金报告"""
    if "error" in flow_data:
        return f"资金数据获取失败: {flow_data['error']}"

    lines = [
        f"【资金分析】",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"市场流动性: {flow_data['liquidity']}",
        f"活跃资金: {flow_data['hot_money_status']}",
        f"投机热度: {flow_data['speculation_level']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"全市场成交额: {flow_data['total_volume']:.2f}万亿",
        f"平均换手率: {flow_data['avg_turnover']:.2f}%",
        f"大盘股状态: {flow_data['large_cap_status']}",
        f"小盘股状态: {flow_data['small_cap_status']}",
        f"强势股数量: {flow_data['strong_count']}家",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"整体判断: {flow_data['资金判断']}",
    ]

    return "\n".join(lines)
