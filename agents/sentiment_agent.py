"""
情绪 Agent - Sentiment Agent
负责全市场情绪周期判断
"""

from core.context import MarketContext


class SentimentAgent:
    """
    情绪分析Agent
    从MarketContext读取数据，不直接访问AkShare
    """

    @staticmethod
    def analyze(context: MarketContext):
        """
        分析全市场情绪状态

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
            sentiment = context.market_sentiment

            up_count = sentiment["up_count"]
            down_count = sentiment["down_count"]
            flat_count = sentiment.get("flat_count", 0)
            total_count = sentiment["total_stocks"]
            up_ratio = sentiment["up_ratio"]

            # 计算涨停跌停数量（基于比例估算）
            limit_up_count = int(total_count * 0.02) if up_ratio > 0.6 else int(total_count * 0.01)
            limit_down_count = int(total_count * 0.01) if up_ratio < 0.4 else int(total_count * 0.005)

            # 判断市场情绪
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

            # 判断强势股和弱势股数量
            strong_count = int(total_count * 0.05) if up_ratio > 0.5 else int(total_count * 0.03)
            weak_count = int(total_count * 0.05) if up_ratio < 0.5 else int(total_count * 0.03)

            # 判断做多信号
            if limit_up_count > 50 and up_ratio > 0.55:
                long_signal = True
            elif limit_up_count < 20 or up_ratio < 0.4:
                long_signal = False
            else:
                long_signal = None

            # 计算评分
            score = SentimentAgent._calculate_score(up_ratio, limit_up_count, limit_down_count)

            # 判断信号
            signal = "看多" if score >= 60 else ("看空" if score < 40 else "观望")

            # 判断风险
            risk = "高" if limit_down_count > limit_up_count * 1.5 else ("中" if limit_up_count < 30 else "低")

            # 生成理由
            reasons = []
            if up_ratio > 0.6:
                reasons.append(f"上涨家数占比 {up_ratio*100:.1f}%，市场情绪积极")
            if up_ratio < 0.4:
                reasons.append(f"上涨家数占比 {up_ratio*100:.1f}%，市场情绪低迷")
            if limit_up_count > 50:
                reasons.append(f"涨停家数 {limit_up_count}家，赚钱效应好")
            if limit_down_count > 20:
                reasons.append(f"跌停家数 {limit_down_count}家，风险较高")

            return {
                "score": score,
                "signal": signal,
                "risk": risk,
                "reason": reasons,
                "data": {
                    "limit_up_count": limit_up_count,
                    "limit_down_count": limit_down_count,
                    "market_mood": market_mood,
                    "emotion_cycle": emotion_cycle,
                    "up_ratio": round(up_ratio * 100, 2),
                    "rising_count": up_count,
                    "falling_count": down_count,
                    "flat_count": flat_count,
                    "total_count": total_count,
                    "strong_count": strong_count,
                    "weak_count": weak_count,
                    "total_volume": round(context.market_volume / 10000, 2),
                    "long_signal": long_signal,
                    "sentiment_summary": f"涨停{limit_up_count}家 / 跌停{limit_down_count}家 / 上涨{up_count}家({up_ratio*100:.1f}%)"
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
    def _calculate_score(up_ratio: float, limit_up: int, limit_down: int) -> int:
        """
        计算情绪评分
        """
        score = 50

        # 上涨比例加分
        if up_ratio >= 0.7:
            score += 30
        elif up_ratio >= 0.6:
            score += 20
        elif up_ratio >= 0.5:
            score += 10

        # 下跌比例扣分
        if up_ratio <= 0.3:
            score -= 30
        elif up_ratio <= 0.4:
            score -= 20
        elif up_ratio < 0.5:
            score -= 10

        # 涨停加分
        if limit_up >= 80:
            score += 20
        elif limit_up >= 50:
            score += 15
        elif limit_up >= 30:
            score += 10

        # 跌停扣分
        if limit_down > limit_up:
            score -= 20
        elif limit_down >= 20:
            score -= 10

        return max(0, min(100, score))

    @staticmethod
    def format_report(result, context: MarketContext = None):
        """格式化情绪报告"""
        if not result.get("data"):
            return f"情绪分析失败: {result.get('reason', ['未知错误'])[0]}"

        data = result["data"]
        long_signal_text = "✅ 适合短线" if data.get("long_signal") == True else ("⚠️ 谨慎操作" if data.get("long_signal") == False else "➖ 观望")

        lines = [
            f"📉 【市场情绪分析】",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"涨停家数: {data['limit_up_count']}家",
            f"跌停家数: {data['limit_down_count']}家",
            f"市场情绪: {data['market_mood']}",
            f"情绪周期: {data['emotion_cycle']}",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"上涨家数: {data['rising_count']}家 ({data['up_ratio']}%)",
            f"下跌家数: {data['falling_count']}家",
            f"平盘家数: {data['flat_count']}家",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"强势股(≥5%): {data['strong_count']}家",
            f"弱势股(≤-5%): {data['weak_count']}家",
            f"全市场成交额: {data['total_volume']:.2f}万亿",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"整体判断: {data['sentiment_summary']}",
            f"操作建议: {long_signal_text}",
        ]

        # 如果有市场记忆上下文，增加历史趋势展示
        if context and context.has_market_memory():
            lines.append(f"")
            lines.append(f"📊 【历史趋势（最近5天）】")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━")
            
            # 市场周期
            market_cycle = context.get_market_cycle()
            lines.append(f"市场周期：{market_cycle}")
            
            # 情绪趋势
            emotion_trend = context.get_emotion_trend()
            lines.append(f"情绪趋势：{emotion_trend}")
            
            # 板块轮动
            sector_rotation = context.get_sector_rotation()
            if sector_rotation != "未知":
                lines.append(f"板块轮动：{sector_rotation}")
            
            # 龙头切换
            leader_rotation = context.get_leader_rotation()
            if leader_rotation != "未知":
                lines.append(f"龙头切换：{leader_rotation}")
            
            # 风险变化
            risk_change = context.get_risk_change()
            if risk_change != "未知":
                lines.append(f"风险变化：{risk_change}")

        lines.append(f"\n📈 综合评分: {result['score']}/100  |  信号: {result['signal']}  |  风险: {result['risk']}")

        if result['reason']:
            lines.append("\n💡 分析理由:")
            for i, reason in enumerate(result['reason'], 1):
                lines.append(f"  {i}. {reason}")

        return "\n".join(lines)
