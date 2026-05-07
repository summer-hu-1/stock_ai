import akshare as ak
import pandas as pd
from datetime import datetime
import time

_stock_data_cache = {}
_stock_data_cache_time = {}
_stock_data_cache_ttl = 60

def get_stock_data(stock_code, use_cache=True):
    """
    获取A股基础行情数据
    use_cache: 是否使用缓存
    """
    global _stock_data_cache, _stock_data_cache_time

    current_time = time.time()
    if use_cache and stock_code in _stock_data_cache:
        if current_time - _stock_data_cache_time.get(stock_code, 0) < _stock_data_cache_ttl:
            print(f"📦 使用缓存的股票数据: {stock_code}")
            return _stock_data_cache[stock_code]

    try:
        print(f"正在获取股票数据: {stock_code}")
        df = ak.stock_zh_a_spot_em()

        if df is None:
            print(f"警告: API返回None，尝试使用缓存")
            if stock_code in _stock_data_cache:
                return _stock_data_cache[stock_code]
            return None

        if not isinstance(df, pd.DataFrame) or df.empty:
            print(f"警告: 获取到的数据为空或格式错误，尝试使用缓存")
            if stock_code in _stock_data_cache:
                return _stock_data_cache[stock_code]
            return None

        if "代码" not in df.columns:
            print(f"警告: 数据列不包含'代码'，尝试使用缓存")
            if stock_code in _stock_data_cache:
                return _stock_data_cache[stock_code]
            return None

        stock = df[df["代码"] == stock_code]

        if stock.empty:
            print(f"未找到股票: {stock_code}")
            return None

        data = stock.iloc[0]

        result = {
            "code": data["代码"],
            "name": data["名称"],
            "price": float(data["最新价"]) if pd.notna(data["最新价"]) else 0.0,
            "price_change_pct": float(data["涨跌幅"]) if pd.notna(data["涨跌幅"]) else 0.0,
            "volume": float(data["成交额"]) if pd.notna(data["成交额"]) else 0.0,
            "turnover_rate": float(data["换手率"]) if pd.notna(data["换手率"]) else 0.0,
            "amplitude": float(data["振幅"]) if pd.notna(data["振幅"]) else 0.0,
            "volume_ratio": float(data["量比"]) if pd.notna(data["量比"]) else 0.0,
            "high": float(data["最高"]) if pd.notna(data["最高"]) else 0.0,
            "low": float(data["最低"]) if pd.notna(data["最低"]) else 0.0,
            "open": float(data["今开"]) if pd.notna(data["今开"]) else 0.0,
            "close": float(data["昨收"]) if pd.notna(data["昨收"]) else 0.0,
            "market_cap": float(data["总市值"]) if pd.notna(data.get("总市值")) else 0.0,
            "float_share": float(data["流通市值"]) if pd.notna(data.get("流通市值")) else 0.0,
            "limit_status": "涨停" if float(data["涨跌幅"]) >= 9.9 else ("跌停" if float(data["涨跌幅"]) <= -9.9 else "正常")
        }

        _stock_data_cache[stock_code] = result
        _stock_data_cache_time[stock_code] = current_time
        print(f"✅ 股票数据获取成功: {stock_code}")
        return result

    except Exception as e:
        print(f"获取股票数据失败: {e}")
        import traceback
        traceback.print_exc()
        if stock_code in _stock_data_cache:
            print(f"📦 获取失败，返回缓存数据")
            return _stock_data_cache[stock_code]
        return None


def get_stock_data_fast(stock_code, use_cache=True, target_date=None):
    """
    极速模式获取A股行情数据 - 使用历史数据API，速度更快
    注意：此函数获取的是指定日期或最近可用交易日的收盘数据，非实时数据
    
    Args:
        target_date: 目标日期，datetime对象或字符串(YYYY-MM-DD/YYYYMMDD)，None为最近交易日
    """
    global _stock_data_cache, _stock_data_cache_time

    current_time = time.time()
    
    date_str = "latest"
    if target_date is not None:
        if isinstance(target_date, str):
            if '-' in target_date:
                date_str = target_date.replace('-', '')
            else:
                date_str = target_date
        else:
            date_str = target_date.strftime('%Y%m%d')
    
    cache_key = f"{stock_code}_fast_{date_str}"
    if use_cache and cache_key in _stock_data_cache:
        if current_time - _stock_data_cache_time.get(cache_key, 0) < _stock_data_cache_ttl:
            print(f"📦 使用缓存的极速股票数据: {stock_code} @ {date_str}")
            return _stock_data_cache[cache_key]

    try:
        print(f"正在极速获取股票数据: {stock_code}")
        
        if target_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        else:
            if isinstance(target_date, str):
                if '-' in target_date:
                    end_date = target_date.replace('-', '')
                else:
                    end_date = target_date
            else:
                end_date = target_date.strftime('%Y%m%d')
        
        start_date = (datetime.now().replace(day=1)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=stock_code, period='daily', start_date=start_date, end_date=end_date, adjust='')

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            print(f"警告: 极速获取数据为空，尝试使用缓存")
            if cache_key in _stock_data_cache:
                return _stock_data_cache[cache_key]
            if stock_code in _stock_data_cache:
                return _stock_data_cache[stock_code]
            return None

        latest = df.iloc[-1]

        result = {
            "code": stock_code,
            "name": latest.get("股票代码", stock_code),
            "price": float(latest["收盘"]) if pd.notna(latest["收盘"]) else 0.0,
            "price_change_pct": float(latest["涨跌幅"]) if pd.notna(latest["涨跌幅"]) else 0.0,
            "volume": float(latest["成交额"]) if pd.notna(latest["成交额"]) else 0.0,
            "turnover_rate": float(latest["换手率"]) if pd.notna(latest["换手率"]) else 0.0,
            "amplitude": float(latest["振幅"]) if pd.notna(latest["振幅"]) else 0.0,
            "volume_ratio": 0.0,
            "high": float(latest["最高"]) if pd.notna(latest["最高"]) else 0.0,
            "low": float(latest["最低"]) if pd.notna(latest["最低"]) else 0.0,
            "open": float(latest["开盘"]) if pd.notna(latest["开盘"]) else 0.0,
            "close": float(latest["收盘"]) if pd.notna(latest["收盘"]) else 0.0,
            "market_cap": 0.0,
            "float_share": 0.0,
            "limit_status": "涨停" if float(latest["涨跌幅"]) >= 9.9 else ("跌停" if float(latest["涨跌幅"]) <= -9.9 else "正常")
        }

        _stock_data_cache[cache_key] = result
        _stock_data_cache_time[cache_key] = current_time
        print(f"✅ 极速股票数据获取成功: {stock_code}")
        return result

    except Exception as e:
        print(f"极速获取股票数据失败: {e}")
        import traceback
        traceback.print_exc()
        if cache_key in _stock_data_cache:
            print(f"📦 获取失败，返回缓存数据")
            return _stock_data_cache[cache_key]
        if stock_code in _stock_data_cache:
            return _stock_data_cache[stock_code]
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
