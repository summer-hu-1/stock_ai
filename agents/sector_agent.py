"""
板块 Agent - Sector Agent
负责板块热度分析和主线识别
"""
import akshare as ak
import pandas as pd


def get_stock_sectors(stock_code):
    """
    获取个股所属板块

    Args:
        stock_code: 股票代码

    Returns:
        list: 个股所属板块列表
    """
    try:
        industry_df = ak.stock_board_industry_name_em()
        stock_sectors = []

        for _, row in industry_df.iterrows():
            board_name = row["板块名称"]
            try:
                board_stocks = ak.stock_board_industry_cons_em(symbol=board_name)
                if stock_code in board_stocks["代码"].values:
                    stock_sectors.append({
                        "name": board_name,
                        "change_pct": round(row["涨跌幅"], 2),
                        "turnover_rate": round(row["换手率"], 2) if pd.notna(row["换手率"]) else 0
                    })
                    if len(stock_sectors) >= 3:
                        break
            except:
                continue

        return stock_sectors
    except Exception as e:
        return []


def analyze_sector(stock_code=None):
    """
    分析板块热度

    Args:
        stock_code: 股票代码（可选，用于获取个股所属板块）

    Returns:
        dict: {
            "top_sectors": list,        # 涨幅前5板块
            "hot_concepts": list,       # 热门概念
            "main_line": str,           # 主线方向
            "sector_count": int,        # 涨停板块数量
            "资金流向": str,
            "stock_sectors": list       # 个股所属板块
        }
    """
    try:
        industry_df = ak.stock_board_industry_name_em()
        concept_df = ak.stock_board_concept_name_em()

        top_industry = industry_df.nlargest(5, "涨跌幅")[["板块名称", "涨跌幅", "换手率", "上涨家数"]]
        hot_concepts = concept_df.nlargest(10, "涨跌幅")[["板块名称", "涨跌幅", "换手率", "上涨家数"]]

        top_sectors = []
        for _, row in top_industry.iterrows():
            top_sectors.append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "turnover_rate": round(row["换手率"], 2) if pd.notna(row["换手率"]) else 0,
                "rise_count": int(row["上涨家数"])
            })

        hot_concept_list = []
        for _, row in hot_concepts.iterrows():
            hot_concept_list.append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "turnover_rate": round(row["换手率"], 2) if pd.notna(row["换手率"]) else 0,
                "rise_count": int(row["上涨家数"])
            })

        main_line = top_sectors[0]["name"] if top_sectors else "未知"

        if len(top_sectors) >= 3:
            if any(s["change_pct"] > 5 for s in top_sectors[:3]):
                资金流向 = "集中进攻主线"
            elif all(s["change_pct"] > 2 for s in top_sectors[:3]):
                资金流向 = "多点开花"
            else:
                资金流向 = "轮动切换"
        else:
            资金流向 = "观望"

        stock_sectors = []
        if stock_code:
            stock_sectors = get_stock_sectors(stock_code)

        return {
            "top_sectors": top_sectors,
            "hot_concepts": hot_concept_list,
            "main_line": main_line,
            "sector_count": len(top_sectors),
            "资金流向": 资金流向,
            "stock_sectors": stock_sectors
        }

    except Exception as e:
        return {"error": str(e), "top_sectors": [], "hot_concepts": [], "main_line": "未知", "sector_count": 0, "资金流向": "未知", "stock_sectors": []}


def format_sector_report(sector_data):
    """格式化板块报告"""
    if "error" in sector_data:
        return f"板块数据获取失败: {sector_data['error']}"

    lines = [
        f"【板块分析】",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"主线方向: {sector_data['main_line']}",
        f"资金流向: {sector_data['资金流向']}",
        f"━━━━━━━━━━━━━━━━━━━━",
    ]

    if sector_data.get("stock_sectors"):
        lines.append(f"【个股所属板块】")
        for i, sector in enumerate(sector_data["stock_sectors"], 1):
            lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}%")
        lines.append(f"")

    lines.append(f"【行业板块涨幅前5】")

    for i, sector in enumerate(sector_data["top_sectors"], 1):
        lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}% (换手{sector['turnover_rate']}%)")

    lines.append(f"")
    lines.append(f"【热门概念板块TOP5】")

    for i, concept in enumerate(sector_data["hot_concepts"][:5], 1):
        lines.append(f"{i}. {concept['name']}: +{concept['change_pct']}% (换手{concept['turnover_rate']}%)")

    return "\n".join(lines)
