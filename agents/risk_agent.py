"""
风险 Agent - Risk Agent
负责市场风险评估
"""

from core.context import MarketContext


class RiskAgent:
    """
    风险评估Agent
    从MarketContext读取数据，不直接访问AkShare
    """

    @staticmethod
    def analyze(context: MarketContext):
        """
        分析市场风险

        Args:
            context: MarketContext 统一市场上下文

        Returns:
            dict: {
                "score": int,  # 0-100 (风险越低分数越高)
                "signal": str,  # 看多/看空/观望
                "risk": str,  # 高/中高/中/中低/低
                "reason": list,
                "data": dict  # 详细数据
            }
        """
        try:
            sentiment = context.market_sentiment
            stock_data = context.stock_data

            # 从情绪数据获取涨跌停信息
            up_ratio = sentiment.get("up_ratio", 0.5)
            total_stocks = sentiment.get("total_stocks", 4000)

            # 估算涨停跌停数量
            limit_up_count = int(total_stocks * 0.02) if up_ratio > 0.6 else int(total_stocks * 0.01)
            limit_down_count = int(total_stocks * 0.01) if up_ratio < 0.4 else int(total_stocks * 0.005)

            # 计算平均涨跌
            avg_change = (up_ratio - 0.5) * 20  # 估算值

            main_risks = []
            risk_level = "中"

            # 评估风险因素
            if limit_down_count > 30:
                main_risks.append("跌停家数过多")
                risk_level = "高"
            elif limit_down_count > 15:
                main_risks.append("跌停扩散")
                risk_level = "中高"

            if avg_change < -1:
                main_risks.append("市场整体下跌")
                if risk_level not in ["高", "中高"]:
                    risk_level = "中高"

            if limit_up_count < 20:
                main_risks.append("涨停家数过少")
                if risk_level not in ["高", "中高"]:
                    risk_level = "中"

            # 个股风险因素
            price_change = stock_data.get("change_pct", 0)
            turnover = stock_data.get("turnover", 0)

            if price_change > 9.9:
                main_risks.append("高位追涨风险")
            if turnover > 20:
                main_risks.append("换手率过高")

            # 最终风险等级判断
            if risk_level == "中":
                if limit_up_count > 50 and avg_change > 1:
                    risk_level = "低"
                elif limit_up_count > 30:
                    risk_level = "中低"

            # 确定警告和建议
            if risk_level == "高":
                warning = "市场风险较高，谨慎操作"
                suggestion = "建议空仓或轻仓观望"
                can_trade_short = False
            elif risk_level == "中高":
                warning = "市场存在风险，注意控制仓位"
                suggestion = "谨慎追高，关注确定性机会"
                can_trade_short = None
            elif risk_level == "中":
                warning = "市场机会与风险并存"
                suggestion = "控制仓位，精选个股"
                can_trade_short = None
            elif risk_level == "中低":
                warning = "市场机会大于风险"
                suggestion = "可轻仓参与主线龙头"
                can_trade_short = True
            else:
                warning = "市场情绪良好，短线机会较多"
                suggestion = "积极参与主线龙头，注意轮动"
                can_trade_short = True

            # 计算评分（风险越低分数越高）
            score = RiskAgent._calculate_score(risk_level, limit_up_count, limit_down_count)

            # 判断信号
            signal = "看多" if score >= 60 else ("看空" if score < 40 else "观望")

            # 生成理由
            reasons = []
            if risk_level == "低":
                reasons.append("市场情绪良好，涨停家数充足")
            elif risk_level == "高":
                reasons.append(f"跌停家数 {limit_down_count}家，风险较高")
            if main_risks:
                reasons.append("; ".join(main_risks))

            return {
                "score": score,
                "signal": signal,
                "risk": risk_level,
                "reason": reasons if reasons else ["当前市场风险可控"],
                "data": {
                    "risk_level": risk_level,
                    "main_risks": main_risks if main_risks else ["无明显风险"],
                    "warning": warning,
                    "suggestion": suggestion,
                    "can_trade_short": can_trade_short,
                    "limit_up_count": limit_up_count,
                    "limit_down_count": limit_down_count,
                    "avg_change": round(avg_change, 2)
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
    def _calculate_score(risk_level: str, limit_up: int, limit_down: int) -> int:
        """
        计算风险评分（风险越低分数越高）
        """
        score = 50

        # 根据风险等级调整
        risk_scores = {
            "低": 80,
            "中低": 65,
            "中": 50,
            "中高": 35,
            "高": 20
        }
        score = risk_scores.get(risk_level, 50)

        # 涨停加分
        if limit_up >= 50:
            score += 10
        elif limit_up >= 30:
            score += 5

        # 跌停扣分
        if limit_down > 30:
            score -= 15
        elif limit_down > 15:
            score -= 10

        return max(0, min(100, score))

    @staticmethod
    def format_report(result):
        """格式化风险报告"""
        if not result.get("data"):
            return f"风险分析失败: {result.get('reason', ['未知错误'])[0]}"

        data = result["data"]

        risk_emoji = {
            "高": "🔴",
            "中高": "🟠",
            "中": "🟡",
            "中低": "🟢",
            "低": "✅"
        }.get(data["risk_level"], "❓")

        lines = [
            f"⚠️ 【风险分析】{risk_emoji} 风险等级: {data['risk_level']}",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"主要风险点:",
        ]

        for risk in data["main_risks"]:
            lines.append(f"  • {risk}")

        lines.extend([
            f"━━━━━━━━━━━━━━━━━━━━",
            f"风险提示: {data['warning']}",
            f"操作建议: {data['suggestion']}",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"短线可操作性: {'✅ 可以' if data.get('can_trade_short') == True else ('⚠️ 谨慎' if data.get('can_trade_short') == False else '➖ 观察')}",
        ])

        lines.append(f"\n📈 综合评分: {result['score']}/100  |  信号: {result['signal']}  |  风险: {result['risk']}")

        if result['reason']:
            lines.append("\n💡 分析理由:")
            for i, reason in enumerate(result['reason'], 1):
                lines.append(f"  {i}. {reason}")

        return "\n".join(lines)
