import akshare as ak
import pandas as pd
from datetime import datetime

def get_market_sentiment():
    """
    获取A股全市场情绪数据
    """
    try:
        df = ak.stock_zh_a_spot_em()

        limit_up = df[df["涨跌幅"] >= 9.8]
        limit_up_count = len(limit_up)

        limit_down = df[df["涨跌幅"] <= -9.8]
        limit_down_count = len(limit_down)

        zt_pool = df[df["涨跌幅"] >= 9.8]
        high_vol = df[df["成交额"] > df["成交额"].quantile(0.9)]
        bomb_candidates = high_vol[(high_vol["涨跌幅"] >= 5) & (high_vol["涨跌幅"] < 9.8)]
        bomb_rate = len(bomb_candidates) / max(len(zt_pool), 1) if len(zt_pool) > 0 else 0

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

        if limit_up_count > 80:
            mood = "高潮"
        elif limit_up_count > 50:
            mood = "强势"
        elif limit_up_count > 30:
            mood = "震荡"
        else:
            mood = "退潮"

        total_volume = df["成交额"].sum()
        market_cap_total = df["总市值"].sum() if "总市值" in df.columns else 0

        return {
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "bomb_rate": round(bomb_rate, 2),
            "avg_change": round(avg_change, 2),
            "market_mood": mood,
            "rising_count": rising_count,
            "falling_count": falling_count,
            "flat_count": flat_count,
            "total_count": total_count,
            "rise_ratio": round(rise_ratio, 2),
            "strong_count": strong_count,
            "weak_count": weak_count,
            "total_volume": round(total_volume / 1e12, 2),
            "market_cap": round(market_cap_total / 1e12, 2) if market_cap_total else 0
        }
    except Exception as e:
        print(f"获取市场情绪数据失败: {e}")
        return None

def get_sector_data():
    """
    获取板块涨跌排名数据（简化版）
    """
    try:
        df = ak.stock_board_industry_name_em()

        top_gainers = df.nlargest(10, "涨跌幅")[["板块名称", "涨跌幅", "总市值", "上涨家数", "下跌家数"]]
        top_losers = df.nsmallest(10, "涨跌幅")[["板块名称", "涨跌幅", "总市值", "上涨家数", "下跌家数"]]

        sector_data = {
            "top_gainers": [],
            "top_losers": []
        }

        for _, row in top_gainers.iterrows():
            sector_data["top_gainers"].append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "rise_count": int(row["上涨家数"]),
                "fall_count": int(row["下跌家数"])
            })

        for _, row in top_losers.iterrows():
            sector_data["top_losers"].append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "rise_count": int(row["上涨家数"]),
                "fall_count": int(row["下跌家数"])
            })

        return sector_data
    except Exception as e:
        print(f"获取板块数据失败: {e}")
        return None

def get_hot_sectors():
    """
    获取热门板块（概念板块涨幅排行）
    """
    try:
        df = ak.stock_board_concept_name_em()

        hot_sectors = df.nlargest(15, "涨跌幅")[["板块名称", "涨跌幅", "换手率", "上涨家数", "下跌家数", "总市值"]]

        result = []
        for _, row in hot_sectors.iterrows():
            result.append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "turnover_rate": round(row["换手率"], 2) if pd.notna(row["换手率"]) else 0,
                "rise_count": int(row["上涨家数"]),
                "fall_count": int(row["下跌家数"])
            })

        return result
    except Exception as e:
        print(f"获取热门板块失败: {e}")
        return None

def format_market_sentiment(data, sector_data=None, hot_sectors=None):
    """
    格式化市场情绪数据为易读字符串
    """
    if not data:
        return "未获取到市场情绪数据"

    lines = [
        f"【市场情绪概览】",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"涨停家数: {data['limit_up_count']}家",
        f"跌停家数: {data['limit_down_count']}家",
        f"炸板率: {data['bomb_rate']*100:.1f}%",
        f"市场情绪: {data['market_mood']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"上涨家数: {data['rising_count']}家 ({data['rise_ratio']}%)",
        f"下跌家数: {data['falling_count']}家",
        f"平盘家数: {data['flat_count']}家",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"强势股(≥5%): {data['strong_count']}家",
        f"弱势股(≤-5%): {data['weak_count']}家",
        f"市场平均涨跌: {data['avg_change']:.2f}%",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"全市场成交额: {data['total_volume']:.2f}万亿",
        f"总市值: {data['market_cap']:.2f}万亿",
    ]

    if sector_data and sector_data.get("top_gainers"):
        lines.append(f"")
        lines.append(f"【涨幅前五板块】")
        for i, sector in enumerate(sector_data["top_gainers"][:5], 1):
            lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}%")

    if hot_sectors:
        lines.append(f"")
        lines.append(f"【热门概念板块】")
        for i, sector in enumerate(hot_sectors[:5], 1):
            lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}% (换手{sector['turnover_rate']}%)")

    return "\n".join(lines)
