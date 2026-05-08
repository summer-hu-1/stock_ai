"""
板块 Agent - Sector Agent
负责板块热度分析和主线识别
"""

from core.context import MarketContext


class SectorAgent:
    """
    板块分析Agent
    从MarketContext读取数据，不直接访问AkShare
    """

    @staticmethod
    def analyze(context: MarketContext):
        """
        分析板块热度

        Args:
            context: MarketContext 统一市场上下文

        Returns:
            dict: {
                "score": int,  # 0-100
                "signal": str,  # 看多/看空/观望
                "risk": str,  # 高/中/低
                "reason": list,
                "data": dict  # 详细数据
            }
        """
        try:
            sectors = context.sectors

            # 按涨幅排序
            sorted_sectors = sorted(sectors, key=lambda x: x.get("change_pct", 0), reverse=True)
            top_sectors = sorted_sectors[:5]
            hot_concepts = sorted_sectors[:10]

            # 判断主线方向
            main_line = top_sectors[0]["name"] if top_sectors else "未知"

            # 判断资金流向
            if len(top_sectors) >= 3:
                if any(s["change_pct"] > 5 for s in top_sectors[:3]):
                    fund_flow = "集中进攻主线"
                elif all(s["change_pct"] > 2 for s in top_sectors[:3]):
                    fund_flow = "多点开花"
                else:
                    fund_flow = "轮动切换"
            else:
                fund_flow = "观望"

            # 计算评分
            score = SectorAgent._calculate_score(top_sectors)

            # 判断信号
            signal = "看多" if score >= 60 else ("看空" if score < 40 else "观望")

            # 判断风险
            risk = "低" if len(top_sectors) >= 3 and top_sectors[0]["change_pct"] > 3 else "中"

            # 生成理由
            reasons = []
            if top_sectors:
                reasons.append(f"主线板块 {main_line} 涨幅 {top_sectors[0]['change_pct']:.2f}%")
            if fund_flow == "集中进攻主线":
                reasons.append("资金集中，主线明确")
            elif fund_flow == "多点开花":
                reasons.append("多个板块活跃，机会较多")

            return {
                "score": score,
                "signal": signal,
                "risk": risk,
                "reason": reasons,
                "data": {
                    "top_sectors": top_sectors,
                    "hot_concepts": hot_concepts,
                    "main_line": main_line,
                    "sector_count": len(top_sectors),
                    "fund_flow": fund_flow,
                    "stock_sectors": []  # 个股所属板块信息
                }
            }

        except Exception as e:
            return {
                "score": 0,
                "signal": "未知",
                "risk": "高",
                "reason": [f"分析失败: {str(e)}"],
                "data": {
                    "top_sectors": [],
                    "hot_concepts": [],
                    "main_line": "未知",
                    "sector_count": 0,
                    "fund_flow": "未知",
                    "stock_sectors": []
                }
            }

    @staticmethod
    def _calculate_score(top_sectors: list) -> int:
        """
        计算板块评分
        """
        score = 50

        if not top_sectors:
            return 30

        # 主线强度加分
        first_change = top_sectors[0]["change_pct"]
        if first_change > 5:
            score += 20
        elif first_change > 3:
            score += 15
        elif first_change > 2:
            score += 10

        # 板块扩散度加分
        if len(top_sectors) >= 5:
            avg_change = sum(s["change_pct"] for s in top_sectors[:5]) / 5
            if avg_change > 3:
                score += 15
            elif avg_change > 2:
                score += 10

        # 资金流向判断
        active_count = sum(1 for s in top_sectors if s["change_pct"] > 2)
        if active_count >= 3:
            score += 10
        elif active_count >= 2:
            score += 5

        return max(0, min(100, score))

    @staticmethod
    def format_report(result):
        """格式化板块报告"""
        if not result.get("data"):
            return f"板块分析失败: {result.get('reason', ['未知错误'])[0]}"

        data = result["data"]

        lines = [
            f"🧭 【板块分析】",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"主线方向: {data['main_line']}",
            f"资金流向: {data['fund_flow']}",
            f"━━━━━━━━━━━━━━━━━━━━",
        ]

        if data.get("stock_sectors"):
            lines.append(f"【个股所属板块】")
            for i, sector in enumerate(data["stock_sectors"], 1):
                lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}%")
            lines.append(f"")

        lines.append(f"【行业板块涨幅前5】")

        for i, sector in enumerate(data["top_sectors"], 1):
            lines.append(f"{i}. {sector['name']}: +{sector['change_pct']:.2f}% (换手{sector.get('turnover_rate', 0):.2f}%)")

        lines.append(f"")
        lines.append(f"【热门概念板块TOP5】")

        for i, concept in enumerate(data["hot_concepts"][:5], 1):
            lines.append(f"{i}. {concept['name']}: +{concept['change_pct']:.2f}%")

        lines.append(f"\n📈 综合评分: {result['score']}/100  |  信号: {result['signal']}  |  风险: {result['risk']}")

        if result['reason']:
            lines.append("\n💡 分析理由:")
            for i, reason in enumerate(result['reason'], 1):
                lines.append(f"  {i}. {reason}")

        return "\n".join(lines)
