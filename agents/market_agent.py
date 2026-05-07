"""
行情 Agent - Market Agent
负责个股基础行情状态判断
"""
import akshare as ak
import pandas as pd


def analyze_market(stock_code):
    """
    分析个股行情状态

    Returns:
        dict: {
            "stock_code": str,
            "stock_name": str,
            "price": float,
            "price_change_pct": float,
            "volume": float,
            "turnover_rate": float,
            "amplitude": float,
            "volume_ratio": float,
            "limit_status": str,  # 涨停/跌停/正常
            "strength_level": str,  # 强势/强势/一般/弱势
            "异动信号": list
        }
    """
    try:
        df = ak.stock_zh_a_spot_em()
        stock = df[df["代码"] == stock_code]

        if stock.empty:
            return {"error": f"未找到股票 {stock_code}"}

        data = stock.iloc[0]

        price = float(data["最新价"])
        change_pct = float(data["涨跌幅"])
        turnover = float(data["换手率"])
        amplitude = float(data["振幅"])
        volume_ratio = float(data["量比"])

        limit_status = "涨停" if change_pct >= 9.9 else ("跌停" if change_pct <= -9.9 else "正常")

        if change_pct >= 9.9 or turnover > 10:
            strength_level = "超级强势"
        elif change_pct >= 5 or turnover > 5:
            strength_level = "强势"
        elif change_pct >= 0:
            strength_level = "一般"
        else:
            strength_level = "弱势"

        异动信号 = []
        if change_pct >= 9.9:
            异动信号.append("涨停")
        if change_pct >= 5:
            异动信号.append("大涨")
        if turnover > 10:
            异动信号.append("高换手")
        if volume_ratio > 2:
            异动信号.append("放量")
        if amplitude > 10:
            异动信号.append("大幅波动")

        return {
            "stock_code": stock_code,
            "stock_name": data["名称"],
            "price": price,
            "price_change_pct": change_pct,
            "volume": float(data["成交额"]),
            "turnover_rate": turnover,
            "amplitude": amplitude,
            "volume_ratio": volume_ratio,
            "open": float(data["今开"]),
            "high": float(data["最高"]),
            "low": float(data["最低"]),
            "close": float(data["昨收"]),
            "market_cap": float(data["总市值"]) if "总市值" in data else 0,
            "float_cap": float(data["流通市值"]) if "流通市值" in data else 0,
            "limit_status": limit_status,
            "strength_level": strength_level,
            "异动信号": 异动信号
        }

    except Exception as e:
        return {"error": str(e)}


def format_market_report(market_data):
    """格式化行情报告"""
    if "error" in market_data:
        return f"行情数据获取失败: {market_data['error']}"

    lines = [
        f"【{market_data['stock_name']}】代码: {market_data['stock_code']}",
        f"最新价: {market_data['price']}元  涨跌: {market_data['price_change_pct']:.2f}%",
        f"涨停状态: {market_data['limit_status']}  强势度: {market_data['strength_level']}",
        f"今开: {market_data['open']}  最高: {market_data['high']}  最低: {market_data['low']}",
        f"成交额: {market_data['volume']/1e8:.2f}亿",
        f"换手率: {market_data['turnover_rate']:.2f}%",
        f"量比: {market_data['volume_ratio']:.2f}  振幅: {market_data['amplitude']:.2f}%",
        f"总市值: {market_data['market_cap']/1e8:.2f}亿",
    ]

    if market_data['异动信号']:
        lines.append(f"异动信号: {' / '.join(market_data['异动信号'])}")

    return "\n".join(lines)
