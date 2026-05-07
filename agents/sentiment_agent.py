"""
情绪 Agent - Sentiment Agent
负责全市场情绪周期判断
"""
import akshare as ak
import pandas as pd


def analyze_sentiment():
    """
    分析全市场情绪状态

    Returns:
        dict: {
            "limit_up_count": int,      # 涨停家数
            "limit_down_count": int,    # 跌停家数
            "market_mood": str,         # 高潮/强势/震荡/退潮
            "emotion_cycle": str,       # 启动/发酵/加速/高潮/分歧/退潮
            "avg_change": float,        # 市场平均涨跌
            "rise_ratio": float,        # 上涨家数占比
            "rising_count": int,
            "falling_count": int,
            "strong_count": int,        # 强势股(≥5%)
            "weak_count": int,          # 弱势股(≤-5%)
            "bomb_rate": float,         # 炸板率
            "total_volume": float,       # 总成交额
            "情绪判断": str,
            "做多信号": bool
        }
    """
    try:
        df = ak.stock_zh_a_spot_em()

        limit_up = df[df["涨跌幅"] >= 9.8]
        limit_up_count = len(limit_up)

        limit_down = df[df["涨跌幅"] <= -9.8]
        limit_down_count = len(limit_down)

        avg_change = df["涨跌幅"].mean()

        rising_count = len(df[df["涨跌幅"] > 0])
        falling_count = len(df[df["涨跌幅"] < 0])
        flat_count = len(df[df["涨跌幅"] == 0])
        total_count = len(df)

        rise_ratio = rising_count / total_count * 100 if total_count > 0 else 0

        strong_stocks = df[df["涨跌幅"] >= 5]
        strong_count = len(strong_stocks)

        weak_stocks = df[df["涨跌幅"] <= -5]
        weak_count = len(weak_stocks)

        total_volume = df["成交额"].sum()

        if limit_up_count > 80:
            market_mood = "高潮"
            emotion_cycle = "高潮"
        elif limit_up_count > 50:
            market_mood = "强势"
            emotion_cycle = "加速"
        elif limit_up_count > 30:
            market_mood = "震荡"
            emotion_cycle = "分歧"
        elif limit_up_count > 15:
            market_mood = "偏弱"
            emotion_cycle = "退潮初期"
        else:
            market_mood = "退潮"
            emotion_cycle = "退潮"

        if limit_up_count > 50 and rise_ratio > 55:
            做多信号 = True
        elif limit_up_count < 20 or rise_ratio < 40:
            做多信号 = False
        else:
            做多信号 = None

        情绪判断 = f"涨停{limit_up_count}家 / 跌停{limit_down_count}家 / 上涨{rising_count}家({rise_ratio:.1f}%)"

        return {
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "market_mood": market_mood,
            "emotion_cycle": emotion_cycle,
            "avg_change": round(avg_change, 2),
            "rise_ratio": round(rise_ratio, 2),
            "rising_count": rising_count,
            "falling_count": falling_count,
            "flat_count": flat_count,
            "total_count": total_count,
            "strong_count": strong_count,
            "weak_count": weak_count,
            "bomb_rate": 0.0,
            "total_volume": round(total_volume / 1e12, 2),
            "情绪判断": 情绪判断,
            "做多信号": 做多信号
        }

    except Exception as e:
        return {"error": str(e)}


def format_sentiment_report(sentiment_data):
    """格式化情绪报告"""
    if "error" in sentiment_data:
        return f"情绪数据获取失败: {sentiment_data['error']}"

    做多信号_text = "✅ 适合短线" if sentiment_data.get("做多信号") == True else ("⚠️ 谨慎操作" if sentiment_data.get("做多信号") == False else "➖ 观望")

    lines = [
        f"【市场情绪分析】",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"涨停家数: {sentiment_data['limit_up_count']}家",
        f"跌停家数: {sentiment_data['limit_down_count']}家",
        f"市场情绪: {sentiment_data['market_mood']}",
        f"情绪周期: {sentiment_data['emotion_cycle']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"上涨家数: {sentiment_data['rising_count']}家 ({sentiment_data['rise_ratio']}%)",
        f"下跌家数: {sentiment_data['falling_count']}家",
        f"平盘家数: {sentiment_data['flat_count']}家",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"强势股(≥5%): {sentiment_data['strong_count']}家",
        f"弱势股(≤-5%): {sentiment_data['weak_count']}家",
        f"市场平均涨跌: {sentiment_data['avg_change']:.2f}%",
        f"全市场成交额: {sentiment_data['total_volume']:.2f}万亿",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"整体判断: {sentiment_data['情绪判断']}",
        f"操作建议: {做多信号_text}",
    ]

    return "\n".join(lines)
