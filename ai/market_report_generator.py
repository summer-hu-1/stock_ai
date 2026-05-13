"""AI市场报告生成器 - 基于信号数据生成市场分析报告"""

from services.signal_service import get_signal_service
from datetime import datetime


def generate_report() -> str:
    """生成市场报告"""
    signal_service = get_signal_service()
    summary = signal_service.get_signal_summary()
    
    today = datetime.today().strftime("%Y-%m-%d")
    
    report = f"""
📊 {today} AI 市场扫描报告
================================

一、信号概览
----------
今日信号总数: {summary['total_signals']}
↑ 看多信号: {summary['up_signals']}
↓ 看空信号: {summary['down_signals']}
平均强度: {summary['avg_strength']}

二、强势股票
----------
"""
    
    if summary['top_stocks']:
        for i, code in enumerate(summary['top_stocks'], 1):
            report += f"  {i}. {code}\n"
    else:
        report += "  暂无数据\n"
    
    report += """
三、市场分析
----------
"""
    
    if summary['total_signals'] >= 10:
        bull_ratio = summary['up_signals'] / summary['total_signals']
        if bull_ratio > 0.6:
            report += "  📈 市场情绪偏多，多头信号占优\n"
        elif bull_ratio < 0.4:
            report += "  📉 市场情绪偏空，空头信号占优\n"
        else:
            report += "  ➡️ 市场情绪中性，多空平衡\n"
    else:
        report += "  📊 数据不足，建议等待更多信号\n"
    
    report += "\n================================\n"
    report += "生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return report


def generate_detailed_report() -> dict:
    """生成详细报告（结构化数据）"""
    signal_service = get_signal_service()
    
    today = datetime.today().strftime("%Y-%m-%d")
    df = signal_service.get_today_signals()
    
    if df.empty:
        return {
            "date": today,
            "success": False,
            "message": "暂无今日数据"
        }
    
    # 按信号类型统计
    signal_type_counts = df["signal_type"].value_counts().to_dict()
    
    # 按方向统计
    direction_counts = df["direction"].value_counts().to_dict()
    
    # 强度分布
    avg_strength = round(df["strength"].mean(), 2)
    max_strength = round(df["strength"].max(), 2)
    min_strength = round(df["strength"].min(), 2)
    
    # 强势股票（强度>0.8）
    strong_stocks = df[df["strength"] > 0.8][["code", "name", "signal_type", "strength"]].to_dict("records")
    
    return {
        "date": today,
        "success": True,
        "summary": {
            "total_signals": len(df),
            "up_signals": direction_counts.get("up", 0),
            "down_signals": direction_counts.get("down", 0),
            "neutral_signals": direction_counts.get("neutral", 0),
            "avg_strength": avg_strength,
            "max_strength": max_strength,
            "min_strength": min_strength
        },
        "signal_types": signal_type_counts,
        "strong_stocks": strong_stocks,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    print(generate_report())