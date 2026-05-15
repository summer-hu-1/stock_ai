import akshare as ak
import pandas as pd
from datetime import datetime
import time
import os
import requests
import json
import urllib3

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

urllib3.disable_warnings()

ak_session = requests.Session()
ak_session.trust_env = False
ak_session.proxies = {}

original_session_request = requests.Session.request

def no_proxy_session_request(self, method, url, **kwargs):
    kwargs.pop('proxies', None)
    return original_session_request(self, method, url, proxies={}, **kwargs)

requests.Session.request = no_proxy_session_request

_stock_data_cache = {}
_stock_data_cache_time = {}
_stock_data_cache_ttl = 60

_USE_MOCK_DATA = False

# 备用数据源配置
_ALTERNATE_DATA_SOURCES = {
    'xueqiu': {
        'enabled': True,
        'name': '雪球API',
        'base_url': 'https://stock.xueqiu.com'
    }
}


def set_mock_data_mode(enable):
    """设置是否使用模拟数据模式"""
    global _USE_MOCK_DATA
    _USE_MOCK_DATA = enable
    return _USE_MOCK_DATA


def get_mock_stock_data(stock_code):
    """获取模拟股票数据（用于测试或网络不可用时）"""
    mock_data = {
        "000002": {
            "code": "000002",
            "name": "万科A",
            "price": 12.58,
            "price_change_pct": 2.35,
            "volume": 156800000,
            "turnover_rate": 1.85,
            "amplitude": 4.20,
            "volume_ratio": 1.25,
            "high": 12.80,
            "low": 12.25,
            "open": 12.35,
            "close": 12.30,
            "market_cap": 285000000000,
            "float_share": 228000000000,
            "limit_status": "正常"
        },
        "600519": {
            "code": "600519",
            "name": "贵州茅台",
            "price": 1685.00,
            "price_change_pct": -1.25,
            "volume": 285000000,
            "turnover_rate": 0.35,
            "amplitude": 2.15,
            "volume_ratio": 0.85,
            "high": 1705.00,
            "low": 1678.00,
            "open": 1700.00,
            "close": 1706.00,
            "market_cap": 2110000000000,
            "float_share": 2110000000000,
            "limit_status": "正常"
        },
        "000020": {
            "code": "000020",
            "name": "深华发A",
            "price": 8.25,
            "price_change_pct": 1.58,
            "volume": 35600000,
            "turnover_rate": 3.25,
            "amplitude": 5.30,
            "volume_ratio": 1.45,
            "high": 8.45,
            "low": 8.05,
            "open": 8.10,
            "close": 8.12,
            "market_cap": 18500000000,
            "float_share": 18500000000,
            "limit_status": "正常"
        },
        "000858": {
            "code": "000858",
            "name": "五粮液",
            "price": 145.80,
            "price_change_pct": 0.85,
            "volume": 185000000,
            "turnover_rate": 0.65,
            "amplitude": 2.80,
            "volume_ratio": 1.10,
            "high": 147.50,
            "low": 143.80,
            "open": 144.50,
            "close": 144.60,
            "market_cap": 785000000000,
            "float_share": 785000000000,
            "limit_status": "正常"
        },
        "601318": {
            "code": "601318",
            "name": "中国平安",
            "price": 48.50,
            "price_change_pct": -0.65,
            "volume": 256000000,
            "turnover_rate": 0.95,
            "amplitude": 1.85,
            "volume_ratio": 0.95,
            "high": 49.20,
            "low": 48.00,
            "open": 48.80,
            "close": 48.82,
            "market_cap": 720000000000,
            "float_share": 720000000000,
            "limit_status": "正常"
        }
    }
    
    if stock_code in mock_data:
        return mock_data[stock_code]
    
    return {
        "code": stock_code,
        "name": f"股票{stock_code}",
        "price": 10.00,
        "price_change_pct": 0.00,
        "volume": 100000000,
        "turnover_rate": 1.00,
        "amplitude": 3.00,
        "volume_ratio": 1.00,
        "high": 10.30,
        "low": 9.70,
        "open": 10.00,
        "close": 10.00,
        "market_cap": 50000000000,
        "float_share": 50000000000,
        "limit_status": "正常"
    }


def test_api_connection():
    """测试API连接状态"""
    results = []
    
    # 测试东方财富API
    try:
        import requests
        session = requests.Session()
        session.trust_env = False
        session.proxies = {}
        
        start_time = time.time()
        r = session.get('https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.000001', timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                results.append({
                    'name': '东方财富K线API',
                    'status': 'success',
                    'response_time': f'{response_time:.2f}ms',
                    'message': '连接成功'
                })
            else:
                results.append({
                    'name': '东方财富K线API',
                    'status': 'warning',
                    'response_time': f'{response_time:.2f}ms',
                    'message': '返回数据异常'
                })
        else:
            results.append({
                'name': '东方财富K线API',
                'status': 'error',
                'response_time': f'{response_time:.2f}ms',
                'message': f'HTTP错误: {r.status_code}'
            })
    except Exception as e:
        error_msg = str(e)
        if 'ProxyError' in error_msg:
            results.append({
                'name': '东方财富K线API',
                'status': 'error',
                'response_time': '-',
                'message': '代理错误：请检查代理设置'
            })
        elif 'ConnectionError' in error_msg or 'timeout' in error_msg.lower():
            results.append({
                'name': '东方财富K线API',
                'status': 'error',
                'response_time': '-',
                'message': '连接超时：网络可能不可用'
            })
        else:
            results.append({
                'name': '东方财富K线API',
                'status': 'error',
                'response_time': '-',
                'message': f'连接失败: {str(e)[:50]}'
            })
    
    # 测试实时行情API
    try:
        import requests
        session = requests.Session()
        session.trust_env = False
        session.proxies = {}
        
        start_time = time.time()
        r = session.get('https://push.eastmoney.com/api/qt/stock/get?secid=1.600519', timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                results.append({
                    'name': '东方财富实时行情API',
                    'status': 'success',
                    'response_time': f'{response_time:.2f}ms',
                    'message': '连接成功'
                })
            else:
                results.append({
                    'name': '东方财富实时行情API',
                    'status': 'warning',
                    'response_time': f'{response_time:.2f}ms',
                    'message': '返回数据异常'
                })
        else:
            results.append({
                'name': '东方财富实时行情API',
                'status': 'error',
                'response_time': f'{response_time:.2f}ms',
                'message': f'HTTP错误: {r.status_code}'
            })
    except Exception as e:
        results.append({
            'name': '东方财富实时行情API',
            'status': 'error',
            'response_time': '-',
            'message': f'连接失败: {str(e)[:50]}'
        })
    
    # 测试akshare
    try:
        start_time = time.time()
        df = ak.stock_zh_a_spot_em()
        response_time = (time.time() - start_time) * 1000
        
        if df is not None and not df.empty:
            results.append({
                'name': 'akshare A股行情接口',
                'status': 'success',
                'response_time': f'{response_time:.2f}ms',
                'message': f'成功获取 {len(df)} 条股票数据'
            })
        else:
            results.append({
                'name': 'akshare A股行情接口',
                'status': 'warning',
                'response_time': f'{response_time:.2f}ms',
                'message': '返回数据为空'
            })
    except Exception as e:
        results.append({
            'name': 'akshare A股行情接口',
            'status': 'error',
            'response_time': '-',
            'message': f'调用失败: {str(e)[:50]}'
        })
    
    # 测试雪球API（备用数据源）
    try:
        start_time = time.time()
        xueqiu_data = get_stock_data_from_xueqiu('600519')
        response_time = (time.time() - start_time) * 1000
        
        if xueqiu_data:
            results.append({
                'name': '雪球API（备用数据源）',
                'status': 'success',
                'response_time': f'{response_time:.2f}ms',
                'message': f'连接成功，股票: {xueqiu_data.get("name", "未知")} {xueqiu_data.get("price", 0)}元'
            })
        else:
            results.append({
                'name': '雪球API（备用数据源）',
                'status': 'error',
                'response_time': f'{response_time:.2f}ms',
                'message': '返回数据为空'
            })
    except Exception as e:
        results.append({
            'name': '雪球API（备用数据源）',
            'status': 'error',
            'response_time': '-',
            'message': f'连接失败: {str(e)[:50]}'
        })
    
    return results

def get_stock_data(stock_code, market="cn", use_cache=True, target_date=None):
    """
    获取股票行情数据（支持多市场）
    
    Args:
        stock_code: 股票代码
        market: 市场（cn/hk/us）
        use_cache: 是否使用缓存
        target_date: 目标日期，datetime 对象或字符串 (YYYY-MM-DD/YYYYMMDD)，None 为最近交易日
    
    Returns:
        Dict: 股票数据
    """
    global _stock_data_cache, _stock_data_cache_time, _USE_MOCK_DATA

    if _USE_MOCK_DATA:
        print(f"📋 使用模拟数据：{stock_code}")
        return get_mock_stock_data(stock_code)

    # 如果指定了日期，优先使用极速模式获取历史数据
    if target_date is not None:
        print(f"📅 指定日期 {target_date}，使用极速模式获取历史数据")
        # 有指定日期时不使用缓存，确保获取最新选择的数据
        return get_stock_data_fast(stock_code, market, use_cache=False, target_date=target_date)

    # 根据市场选择不同的数据源
    if market == "cn":
        return _get_cn_stock_data(stock_code, use_cache)
    elif market == "hk":
        return _get_hk_stock_data(stock_code, use_cache)
    elif market == "us":
        return _get_us_stock_data(stock_code, use_cache)
    else:
        print(f"⚠️ 不支持的市场：{market}，默认使用 A 股数据源")
        return _get_cn_stock_data(stock_code, use_cache)


def _get_cn_stock_data(stock_code, use_cache=True):
    """获取 A 股数据"""
    current_time = time.time()
    if use_cache and stock_code in _stock_data_cache:
        if current_time - _stock_data_cache_time.get(stock_code, 0) < _stock_data_cache_ttl:
            print(f"📦 使用缓存的股票数据：{stock_code}")
            return _stock_data_cache[stock_code]

    try:
        print(f"正在获取 A 股股票数据：{stock_code}")
        df = ak.stock_zh_a_spot_em()

        # akshare 可能在内部捕获异常并返回 None，需要检查
        if df is None:
            print(f"警告: API返回None，尝试使用备用数据源（雪球API）")
            xueqiu_data = get_stock_data_from_xueqiu(stock_code)
            if xueqiu_data:
                _stock_data_cache[stock_code] = xueqiu_data
                _stock_data_cache_time[stock_code] = current_time
                return xueqiu_data
            print(f"❌ 备用数据源也失败，尝试使用极速模式")
            return get_stock_data_fast(stock_code, use_cache=False)

        if not isinstance(df, pd.DataFrame) or df.empty:
            print(f"警告: 获取到的数据为空或格式错误，尝试使用备用数据源（雪球API）")
            xueqiu_data = get_stock_data_from_xueqiu(stock_code)
            if xueqiu_data:
                _stock_data_cache[stock_code] = xueqiu_data
                _stock_data_cache_time[stock_code] = current_time
                return xueqiu_data
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
        
        # 检查是否是网络相关错误
        error_str = str(e)
        is_network_error = any([
            "ProxyError" in error_str,
            "Max retries exceeded" in error_str,
            "Connection aborted" in error_str,
            "RemoteDisconnected" in error_str,
            isinstance(e, requests.exceptions.ConnectionError)
        ])
        
        if is_network_error:
            print(f"⚠️ 网络连接错误，尝试使用备用数据源（雪球API）")
            xueqiu_data = get_stock_data_from_xueqiu(stock_code)
            if xueqiu_data:
                _stock_data_cache[stock_code] = xueqiu_data
                _stock_data_cache_time[stock_code] = current_time
                return xueqiu_data
            print(f"❌ 备用数据源也失败，尝试使用极速模式")
            return get_stock_data_fast(stock_code, use_cache=False)
        
        if stock_code in _stock_data_cache:
            print(f"📦 获取失败，返回缓存数据")
            return _stock_data_cache[stock_code]
        return None


def _get_hk_stock_data(stock_code, use_cache=True):
    """获取港股数据"""
    current_time = time.time()
    if use_cache and stock_code in _stock_data_cache:
        if current_time - _stock_data_cache_time.get(stock_code, 0) < _stock_data_cache_ttl:
            print(f"📦 使用缓存的港股数据：{stock_code}")
            return _stock_data_cache[stock_code]

    try:
        print(f"正在获取港股股票数据：{stock_code}")
        # 使用 akshare 获取港股数据
        df = ak.stock_hk_spot_em()
        
        if df is None or df.empty:
            print(f"⚠️ 港股 API 返回为空，尝试备用数据源")
            return None
        
        # 港股代码需要补零到 5 位
        stock_code_padded = str(stock_code).zfill(5)
        
        # 查找对应的股票
        stock = df[df["代码"] == stock_code_padded]
        
        if stock.empty:
            print(f"未找到港股：{stock_code_padded}")
            return None
        
        data = stock.iloc[0]
        
        result = {
            "code": stock_code_padded,
            "name": data.get("名称", "未知"),
            "price": float(data.get("最新价", 0)) if pd.notna(data.get("最新价")) else 0.0,
            "price_change_pct": float(data.get("涨跌幅", 0)) if pd.notna(data.get("涨跌幅")) else 0.0,
            "volume": float(data.get("成交额", 0)) if pd.notna(data.get("成交额")) else 0.0,
            "turnover_rate": 0.0,  # 港股 API 不提供换手率
            "amplitude": float(data.get("振幅", 0)) if pd.notna(data.get("振幅")) else 0.0,
            "volume_ratio": 0.0,  # 港股 API 不提供量比
            "high": float(data.get("最高", 0)) if pd.notna(data.get("最高")) else 0.0,
            "low": float(data.get("最低", 0)) if pd.notna(data.get("最低")) else 0.0,
            "open": float(data.get("今开", 0)) if pd.notna(data.get("今开")) else 0.0,
            "close": float(data.get("昨收", 0)) if pd.notna(data.get("昨收")) else 0.0,
            "market_cap": float(data.get("总市值", 0)) if pd.notna(data.get("总市值")) else 0.0,
            "limit_status": "正常"  # 港股无涨跌幅限制
        }
        
        _stock_data_cache[stock_code] = result
        _stock_data_cache_time[stock_code] = current_time
        print(f"✅ 港股数据获取成功：{stock_code}")
        return result
        
    except Exception as e:
        print(f"获取港股数据失败：{e}")
        if stock_code in _stock_data_cache:
            return _stock_data_cache[stock_code]
        return None


def _get_us_stock_data(stock_code, use_cache=True):
    """获取美股数据"""
    current_time = time.time()
    if use_cache and stock_code in _stock_data_cache:
        if current_time - _stock_data_cache_time.get(stock_code, 0) < _stock_data_cache_ttl:
            print(f"📦 使用缓存的美股数据：{stock_code}")
            return _stock_data_cache[stock_code]

    try:
        print(f"正在获取美股股票数据：{stock_code}")
        # 使用 akshare 获取美股数据
        df = ak.stock_us_spot_em()
        
        if df is None or df.empty:
            print(f"⚠️ 美股 API 返回为空，尝试备用数据源")
            return None
        
        # 查找对应的股票（美股使用代码或名称匹配）
        stock = df[df["代码"] == stock_code]
        
        if stock.empty:
            # 尝试用名称匹配
            stock = df[df["名称"] == stock_code]
        
        if stock.empty:
            print(f"未找到美股：{stock_code}")
            return None
        
        data = stock.iloc[0]
        
        result = {
            "code": stock_code,
            "name": data.get("名称", "未知"),
            "price": float(data.get("最新价", 0)) if pd.notna(data.get("最新价")) else 0.0,
            "price_change_pct": float(data.get("涨跌幅", 0)) if pd.notna(data.get("涨跌幅")) else 0.0,
            "volume": float(data.get("成交量", 0)) if pd.notna(data.get("成交量")) else 0.0,
            "turnover_rate": 0.0,  # 美股 API 不提供换手率
            "amplitude": 0.0,  # 美股 API 不提供振幅
            "volume_ratio": 0.0,  # 美股 API 不提供量比
            "high": float(data.get("最高价", 0)) if pd.notna(data.get("最高价")) else 0.0,
            "low": float(data.get("最低价", 0)) if pd.notna(data.get("最低价")) else 0.0,
            "open": float(data.get("开盘价", 0)) if pd.notna(data.get("开盘价")) else 0.0,
            "close": float(data.get("昨收价", 0)) if pd.notna(data.get("昨收价")) else 0.0,
            "market_cap": float(data.get("总市值", 0)) if pd.notna(data.get("总市值")) else 0.0,
            "limit_status": "正常"  # 美股无涨跌幅限制
        }
        
        _stock_data_cache[stock_code] = result
        _stock_data_cache_time[stock_code] = current_time
        print(f"✅ 美股数据获取成功：{stock_code}")
        return result
        
    except Exception as e:
        print(f"获取美股数据失败：{e}")
        if stock_code in _stock_data_cache:
            return _stock_data_cache[stock_code]
        return None


def get_stock_data_fast(stock_code, market="cn", use_cache=True, target_date=None):
    """
    极速模式获取股票行情数据 - 优先使用本地 CSV 数据，支持历史日期
    
    Args:
        stock_code: 股票代码
        market: 市场（cn/hk/us）
        use_cache: 是否使用缓存
        target_date: 目标日期，datetime 对象或字符串 (YYYY-MM-DD/YYYYMMDD)，None 为最近交易日
    """
    global _stock_data_cache, _stock_data_cache_time, _USE_MOCK_DATA

    if _USE_MOCK_DATA:
        print(f"📋 使用模拟数据：{stock_code}")
        return get_mock_stock_data(stock_code)

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
    
    cache_key = f"{stock_code}_fast_{market}_{date_str}"
    if use_cache and cache_key in _stock_data_cache:
        if current_time - _stock_data_cache_time.get(cache_key, 0) < _stock_data_cache_ttl:
            print(f"📦 使用缓存的极速股票数据：{stock_code} @ {date_str}")
            return _stock_data_cache[cache_key]

    # 优先使用本地 CSV 数据
    try:
        print(f"📂 尝试从本地 CSV 获取数据：{stock_code} (市场：{market})")
        from data import get_datahub

        datahub = get_datahub()
        csv_df = datahub.get_ohlcv_dataframe(stock_code, market)
        
        if csv_df is not None and not csv_df.empty:
            print(f"✅ 本地 CSV 数据可用")
            
            # 根据target_date筛选数据
            if target_date is not None:
                target_date_str = date_str
                # CSV中的日期格式是YYYY-MM-DD字符串，需要先转换为datetime再格式化
                csv_df['date_str'] = pd.to_datetime(csv_df['date']).dt.strftime('%Y%m%d')
                matching_rows = csv_df[csv_df['date_str'] == target_date_str]
                if not matching_rows.empty:
                    selected_row = matching_rows.iloc[0]
                    print(f"✅ 使用指定日期数据: {target_date_str}")
                else:
                    # 如果没有找到匹配的日期，使用最近的一个
                    selected_row = csv_df.iloc[-1]
                    print(f"⚠️ 未找到日期 {target_date_str}，使用最近交易日: {selected_row['date'].date()}")
            else:
                # 没有指定日期，使用最近的
                selected_row = csv_df.iloc[-1]
            
            # 从数据库获取股票名称
            stock_name = _get_stock_name_from_db(stock_code)
            
            result = {
                "code": stock_code,
                "name": stock_name,
                "price": float(selected_row["close"]) if pd.notna(selected_row["close"]) else 0.0,
                "price_change_pct": float(selected_row["price_change_pct"]) if pd.notna(selected_row["price_change_pct"]) else 0.0,
                "volume": float(selected_row["amount"]) if pd.notna(selected_row["amount"]) else 0.0,
                "turnover_rate": float(selected_row["turnover_rate"]) if pd.notna(selected_row["turnover_rate"]) else 0.0,
                "amplitude": float(selected_row["amplitude"]) if pd.notna(selected_row["amplitude"]) else 0.0,
                "volume_ratio": 0.0,
                "high": float(selected_row["high"]) if pd.notna(selected_row["high"]) else 0.0,
                "low": float(selected_row["low"]) if pd.notna(selected_row["low"]) else 0.0,
                "open": float(selected_row["open"]) if pd.notna(selected_row["open"]) else 0.0,
                "close": float(selected_row["close"]) if pd.notna(selected_row["close"]) else 0.0,
                "market_cap": 0.0,
                "float_share": 0.0,
                "limit_status": "涨停" if float(selected_row["price_change_pct"]) >= 9.9 else ("跌停" if float(selected_row["price_change_pct"]) <= -9.9 else "正常")
            }
            
            _stock_data_cache[cache_key] = result
            _stock_data_cache_time[cache_key] = current_time
            print(f"✅ 从CSV获取成功: {stock_code}")
            return result
    except Exception as e:
        print(f"⚠️ 本地CSV获取失败: {e}")
    
    # 本地CSV不可用，尝试使用akshare
    try:
        print(f"🌐 尝试从akshare获取数据: {stock_code}")
        
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

        # 根据target_date筛选数据
        if target_date is not None:
            # 确保日期列是字符串格式进行匹配
            df['日期'] = df['日期'].astype(str)
            target_date_str = date_str
            # 查找匹配的日期
            matching_rows = df[df['日期'] == target_date_str]
            if not matching_rows.empty:
                selected_row = matching_rows.iloc[0]
                print(f"✅ 使用指定日期数据: {target_date_str}")
            else:
                # 如果没有找到匹配的日期，使用最近的一个
                selected_row = df.iloc[-1]
                print(f"⚠️ 未找到日期 {target_date_str}，使用最近交易日: {selected_row['日期']}")
        else:
            # 没有指定日期，使用最近的
            selected_row = df.iloc[-1]

        # 从数据库获取股票名称
        stock_name = _get_stock_name_from_db(stock_code)

        result = {
            "code": stock_code,
            "name": stock_name,
            "price": float(selected_row["收盘"]) if pd.notna(selected_row["收盘"]) else 0.0,
            "price_change_pct": float(selected_row["涨跌幅"]) if pd.notna(selected_row["涨跌幅"]) else 0.0,
            "volume": float(selected_row["成交额"]) if pd.notna(selected_row["成交额"]) else 0.0,
            "turnover_rate": float(selected_row["换手率"]) if pd.notna(selected_row["换手率"]) else 0.0,
            "amplitude": float(selected_row["振幅"]) if pd.notna(selected_row["振幅"]) else 0.0,
            "volume_ratio": 0.0,
            "high": float(selected_row["最高"]) if pd.notna(selected_row["最高"]) else 0.0,
            "low": float(selected_row["最低"]) if pd.notna(selected_row["最低"]) else 0.0,
            "open": float(selected_row["开盘"]) if pd.notna(selected_row["开盘"]) else 0.0,
            "close": float(selected_row["收盘"]) if pd.notna(selected_row["收盘"]) else 0.0,
            "market_cap": 0.0,
            "float_share": 0.0,
            "limit_status": "涨停" if float(selected_row["涨跌幅"]) >= 9.9 else ("跌停" if float(selected_row["涨跌幅"]) <= -9.9 else "正常")
        }

        _stock_data_cache[cache_key] = result
        _stock_data_cache_time[cache_key] = current_time
        print(f"✅ 极速股票数据获取成功: {stock_code}")
        return result

    except Exception as e:
        print(f"极速获取股票数据失败: {e}")
        
        # 检查是否是网络相关错误
        error_str = str(e)
        is_network_error = any([
            "ProxyError" in error_str,
            "Max retries exceeded" in error_str,
            "Connection aborted" in error_str,
            "RemoteDisconnected" in error_str,
            "ConnectionError" in error_str,
            isinstance(e, requests.exceptions.ConnectionError)
        ])
        
        if is_network_error:
            print(f"⚠️ 网络连接错误，尝试使用备用数据源（雪球API）")
            xueqiu_data = get_stock_data_from_xueqiu(stock_code)
            if xueqiu_data:
                _stock_data_cache[cache_key] = xueqiu_data
                _stock_data_cache_time[cache_key] = current_time
                return xueqiu_data
        
        if cache_key in _stock_data_cache:
            print(f"📦 获取失败，返回缓存数据")
            return _stock_data_cache[cache_key]
        if stock_code in _stock_data_cache:
            return _stock_data_cache[stock_code]
        return None

def get_stock_data_from_xueqiu(stock_code):
    """
    从雪球API获取股票数据（备用数据源）
    """
    try:
        print(f"尝试从雪球获取股票数据: {stock_code}")
        
        # 从数据库获取股票名称
        stock_name = _get_stock_name_from_db(stock_code)
        
        session = requests.Session()
        session.trust_env = False
        session.proxies = {}
        
        # 确定市场类型
        if stock_code.startswith('6'):
            market = 'SH'
        else:
            market = 'SZ'
        
        url = f'https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol={market}{stock_code}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': f'https://xueqiu.com/S/{market}{stock_code}'
        }
        
        r = session.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            # 雪球API返回的data是列表格式
            data_list = data.get('data', [])
            
            if data_list and len(data_list) > 0:
                quote = data_list[0]
                
                result = {
                    "code": stock_code,
                    "name": stock_name,
                    "price": float(quote.get('current', 0)),
                    "price_change_pct": float(quote.get('percent', 0)),
                    "volume": float(quote.get('amount', 0)) * 10000,  # 金额(亿)转成交金额
                    "turnover_rate": float(quote.get('turnover_rate', 0)),
                    "amplitude": float(quote.get('amplitude', 0)),
                    "volume_ratio": 0.0,  # 雪球API不提供量比
                    "high": float(quote.get('high', 0)),
                    "low": float(quote.get('low', 0)),
                    "open": float(quote.get('open', 0)),
                    "close": float(quote.get('last_close', 0)),
                    "market_cap": float(quote.get('market_capital', 0)),
                    "float_share": float(quote.get('float_market_capital', 0)),
                    "limit_status": "涨停" if float(quote.get('percent', 0)) >= 9.9 else ("跌停" if float(quote.get('percent', 0)) <= -9.9 else "正常")
                }
                print(f"✅ 雪球API获取成功: {stock_code} ({stock_name})")
                return result
        
        print(f"❌ 雪球API返回数据异常")
        return None
        
    except Exception as e:
        print(f"雪球API获取失败: {e}")
        return None


def _get_stock_name_from_db(stock_code):
    """
    从本地数据库获取股票名称
    """
    try:
        import sqlite3
        import os
        
        # 尝试多个可能的数据库路径
        db_paths = [
            os.path.join(os.path.dirname(__file__), '../data/stocks_cn.db'),
            os.path.join(os.path.dirname(__file__), '../../data/stocks_cn.db'),
            os.path.join(os.path.dirname(__file__), '../../core/data/stocks_cn.db'),
            'data/stocks_cn.db',
            'stocks_cn.db'
        ]
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM stocks WHERE code = ?', (stock_code,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return row[0]
        
        # 如果数据库中没有找到，返回股票代码作为名称
        return stock_code
    except Exception as e:
        print(f"从数据库获取股票名称失败: {e}")
        return stock_code


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
