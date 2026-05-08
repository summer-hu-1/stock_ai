"""
行情 Agent - Market Agent
负责个股基础行情状态判断
"""

from core.context import MarketContext


class MarketAgent:
    """
    行情分析Agent
    从MarketContext读取数据，不直接访问AkShare
    """

    @staticmethod
    def analyze(context: MarketContext):
        """
        分析个股行情状态

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
            stock_data = context.stock_data

            price = stock_data["price"]
            change_pct = stock_data["change_pct"]
            turnover = stock_data["turnover"]
            amplitude = stock_data["amplitude"]
            volume_ratio = stock_data["volume_ratio"]

            # 判断涨停状态
            limit_status = "涨停" if change_pct >= 9.9 else ("跌停" if change_pct <= -9.9 else "正常")

            # 判断强势度
            if change_pct >= 9.9 or turnover > 10:
                strength_level = "超级强势"
            elif change_pct >= 5 or turnover > 5:
                strength_level = "强势"
            elif change_pct >= 0:
                strength_level = "一般"
            else:
                strength_level = "弱势"

            # 生成异动信号
            signals = []
            if change_pct >= 9.9:
                signals.append("涨停")
            if change_pct >= 5:
                signals.append("大涨")
            if turnover > 10:
                signals.append("高换手")
            if volume_ratio > 2:
                signals.append("放量")
            if amplitude > 10:
                signals.append("大幅波动")

            # 计算评分
            score = MarketAgent._calculate_score(change_pct, turnover, volume_ratio)

            # 判断信号
            signal = "看多" if score >= 60 else ("看空" if score < 40 else "观望")

            # 判断风险
            risk = "高" if abs(change_pct) > 9 or turnover > 20 else ("中" if abs(change_pct) > 5 or turnover > 10 else "低")

            # 生成理由
            reasons = []
            if change_pct > 5:
                reasons.append(f"涨幅达 {change_pct:.2f}%，表现强势")
            if change_pct < -5:
                reasons.append(f"跌幅达 {change_pct:.2f}%，表现弱势")
            if turnover > 10:
                reasons.append(f"换手率 {turnover:.2f}%，交投活跃")
            if volume_ratio > 2:
                reasons.append(f"量比 {volume_ratio:.2f}，明显放量")

            return {
                "score": score,
                "signal": signal,
                "risk": risk,
                "reason": reasons,
                "data": {
                    "stock_code": context.stock_code,
                    "stock_name": context.stock_name,
                    "price": price,
                    "price_change_pct": change_pct,
                    "volume": stock_data["volume"],
                    "turnover_rate": turnover,
                    "amplitude": amplitude,
                    "volume_ratio": volume_ratio,
                    "open": stock_data["open"],
                    "high": stock_data["high"],
                    "low": stock_data["low"],
                    "close": stock_data["close"],
                    "market_cap": stock_data["market_cap"],
                    "float_cap": stock_data["float_cap"],
                    "limit_status": limit_status,
                    "strength_level": strength_level,
                    "signals": signals
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
    def _calculate_score(change_pct: float, turnover: float, volume_ratio: float) -> int:
        """
        计算行情评分
        """
        score = 50

        # 涨幅加分
        if change_pct >= 9.9:
            score += 30
        elif change_pct >= 5:
            score += 20
        elif change_pct >= 3:
            score += 10
        elif change_pct >= 0:
            score += 5

        # 跌幅扣分
        if change_pct <= -9.9:
            score -= 30
        elif change_pct <= -5:
            score -= 20
        elif change_pct <= -3:
            score -= 10
        elif change_pct < 0:
            score -= 5

        # 换手率加分（活跃）
        if turnover > 10:
            score += 10
        elif turnover > 5:
            score += 5

        # 量比加分
        if volume_ratio > 2:
            score += 10
        elif volume_ratio > 1.5:
            score += 5

        return max(0, min(100, score))

    @staticmethod
    def format_report(result):
        """格式化行情报告"""
        if not result.get("data"):
            return f"行情分析失败: {result.get('reason', ['未知错误'])[0]}"

        data = result["data"]
        lines = [
            f"📊 【{data['stock_name']}】行情分析",
            f"代码: {data['stock_code']}",
            f"最新价: {data['price']:.2f}元  涨跌: {data['price_change_pct']:.2f}%",
            f"状态: {data['limit_status']}  |  强势度: {data['strength_level']}",
            f"今开: {data['open']:.2f}  最高: {data['high']:.2f}  最低: {data['low']:.2f}",
            f"成交额: {data['volume']/1e8:.2f}亿元",
            f"换手率: {data['turnover_rate']:.2f}%  |  量比: {data['volume_ratio']:.2f}",
            f"振幅: {data['amplitude']:.2f}%",
            f"总市值: {data['market_cap']/1e8:.2f}亿元  |  流通市值: {data['float_cap']/1e8:.2f}亿元",
        ]

        if data['signals']:
            lines.append(f"⚠️ 异动信号: {' / '.join(data['signals'])}")

        lines.append(f"\n📈 综合评分: {result['score']}/100  |  信号: {result['signal']}  |  风险: {result['risk']}")

        if result['reason']:
            lines.append("\n💡 分析理由:")
            for i, reason in enumerate(result['reason'], 1):
                lines.append(f"  {i}. {reason}")

        return "\n".join(lines)
