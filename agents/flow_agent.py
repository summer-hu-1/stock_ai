"""
资金 Agent - Flow Agent
负责市场资金活跃度分析
"""

from core.context import MarketContext


class FlowAgent:
    """
    资金分析Agent
    从MarketContext读取数据，不直接访问AkShare
    """

    @staticmethod
    def analyze(context: MarketContext):
        """
        分析市场资金状态

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
            market_volume = context.market_volume  # 单位：亿元
            total_volume_trillion = market_volume / 10000  # 转换为万亿

            # 从股票数据获取换手率信息
            turnover = context.stock_data.get("turnover", 2.0)

            # 判断流动性
            if total_volume_trillion > 3:
                liquidity = "充足"
            elif total_volume_trillion > 2:
                liquidity = "一般"
            else:
                liquidity = "紧张"

            # 判断活跃资金状态
            if turnover > 3:
                hot_money_status = "非常活跃"
            elif turnover > 2:
                hot_money_status = "活跃"
            elif turnover > 1:
                hot_money_status = "一般"
            else:
                hot_money_status = "低迷"

            # 判断投机热度（基于市场情绪）
            up_ratio = context.market_sentiment.get("up_ratio", 0.5)
            strong_count = int(context.market_sentiment.get("total_stocks", 0) * 0.05) if up_ratio > 0.5 else int(context.market_sentiment.get("total_stocks", 0) * 0.03)
            speculation_level = "高" if strong_count > 300 else ("中" if strong_count > 150 else "低")

            # 判断大盘股和小盘股状态
            market_cap = context.stock_data.get("market_cap", 0)
            large_cap_status = "强势" if market_cap > 500e8 and context.stock_data.get("change_pct", 0) > 1 else ("弱势" if market_cap > 500e8 and context.stock_data.get("change_pct", 0) < -1 else "平稳")
            small_cap_status = "活跃" if market_cap < 100e8 and turnover > 3 else ("低迷" if market_cap < 100e8 and turnover < 1 else "一般")

            # 资金判断
            if liquidity == "充足" and hot_money_status in ["活跃", "非常活跃"]:
                fund_summary = "市场资金活跃，短线机会多"
            elif liquidity == "紧张" or hot_money_status == "低迷":
                fund_summary = "市场资金紧张，谨慎操作"
            else:
                fund_summary = "市场资金一般，结构性机会"

            # 计算评分
            score = FlowAgent._calculate_score(total_volume_trillion, hot_money_status, speculation_level)

            # 判断信号
            signal = "看多" if score >= 60 else ("看空" if score < 40 else "观望")

            # 判断风险
            risk = "低" if liquidity == "充足" else ("高" if liquidity == "紧张" else "中")

            # 生成理由
            reasons = []
            if liquidity == "充足":
                reasons.append(f"全市场成交额 {total_volume_trillion:.2f}万亿，流动性充足")
            if hot_money_status in ["活跃", "非常活跃"]:
                reasons.append("活跃资金充裕，交投活跃")
            if speculation_level == "高":
                reasons.append("投机热度高，题材机会多")

            return {
                "score": score,
                "signal": signal,
                "risk": risk,
                "reason": reasons,
                "data": {
                    "liquidity": liquidity,
                    "hot_money_status": hot_money_status,
                    "speculation_level": speculation_level,
                    "total_volume": round(total_volume_trillion, 2),
                    "avg_turnover": round(turnover, 2),
                    "large_cap_status": large_cap_status,
                    "small_cap_status": small_cap_status,
                    "strong_count": strong_count,
                    "fund_summary": fund_summary
                }
            }

        except Exception as e:
            return {
                "score": 0,
                "signal": "未知",
                "risk": "高",
                "reason": [f"分析失败: {str(e)}"],
                "data": {}
            }

    @staticmethod
    def _calculate_score(total_volume: float, hot_money: str, speculation: str) -> int:
        """
        计算资金评分
        """
        score = 50

        # 成交额加分
        if total_volume > 3:
            score += 20
        elif total_volume > 2:
            score += 10

        # 活跃资金加分
        if hot_money == "非常活跃":
            score += 20
        elif hot_money == "活跃":
            score += 10

        # 投机热度加分
        if speculation == "高":
            score += 15
        elif speculation == "中":
            score += 5

        # 低迷扣分
        if hot_money == "低迷":
            score -= 20

        return max(0, min(100, score))

    @staticmethod
    def format_report(result):
        """格式化资金报告"""
        if not result.get("data"):
            return f"资金分析失败: {result.get('reason', ['未知错误'])[0]}"

        data = result["data"]

        lines = [
            f"💰 【资金分析】",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"市场流动性: {data['liquidity']}",
            f"活跃资金: {data['hot_money_status']}",
            f"投机热度: {data['speculation_level']}",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"全市场成交额: {data['total_volume']:.2f}万亿",
            f"平均换手率: {data['avg_turnover']:.2f}%",
            f"大盘股状态: {data['large_cap_status']}",
            f"小盘股状态: {data['small_cap_status']}",
            f"强势股数量: {data['strong_count']}家",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"整体判断: {data['fund_summary']}",
        ]

        lines.append(f"\n📈 综合评分: {result['score']}/100  |  信号: {result['signal']}  |  风险: {result['risk']}")

        if result['reason']:
            lines.append("\n💡 分析理由:")
            for i, reason in enumerate(result['reason'], 1):
                lines.append(f"  {i}. {reason}")

        return "\n".join(lines)
