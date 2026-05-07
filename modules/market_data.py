import akshare as ak
import pandas as pd
from datetime import datetime

def get_stock_data(stock_code):
    """
    获取A股基础行情数据
    """
    try:
        df = ak.stock_zh_a_spot_em()

        stock = df[df["代码"] == stock_code]

        if stock.empty:
            return None

        data = stock.iloc[0]

        result = {
            "code": data["代码"],
            "name": data["名称"],
            "price": float(data["最新价"]),
            "price_change_pct": float(data["涨跌幅"]),
            "volume": float(data["成交额"]),
            "turnover_rate": float(data["换手率"]),
            "amplitude": float(data["振幅"]),
            "volume_ratio": float(data["量比"]),
            "high": float(data["最高"]),
            "low": float(data["最低"]),
            "open": float(data["今开"]),
            "close": float(data["昨收"]),
            "market_cap": float(data["总市值"]) if "总市值" in data else 0,
            "float_share": float(data["流通市值"]) if "流通市值" in data else 0,
            "limit_status": "涨停" if float(data["涨跌幅"]) >= 9.9 else ("跌停" if float(data["涨跌幅"]) <= -9.9 else "正常")
        }

        return result
    except Exception as e:
        print(f"获取股票数据失败: {e}")
        return None

def format_stock_data(data):
    """
    格式化股票数据为易读字符串
    """
    if not data:
        return "未获取到数据"

    lines = [
        f"【{data['name']}】代码: {data['code']}",
        f"最新价: {data['price']}元",
        f"涨跌幅: {data['price_change_pct']:.2f}%",
        f"涨停状态: {data['limit_status']}",
        f"今开: {data['open']} | 最高: {data['high']} | 最低: {data['low']}",
        f"成交额: {data['volume']/1e8:.2f}亿",
        f"换手率: {data['turnover_rate']:.2f}%",
        f"量比: {data['volume_ratio']:.2f}",
        f"振幅: {data['amplitude']:.2f}%",
        f"总市值: {data['market_cap']/1e8:.2f}亿",
        f"流通市值: {data['float_share']/1e8:.2f}亿",
    ]

    return "\n".join(lines)
