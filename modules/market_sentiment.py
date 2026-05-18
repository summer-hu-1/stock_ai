import pandas as pd
from datetime import datetime
import sys
import os
import time
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.storage import get_cached_market_sentiment, save_market_sentiment, get_cached_hot_sectors, save_hot_sectors_cache

_sentiment_cache = None
_sentiment_cache_time = None
_sentiment_cache_ttl = 300

def _get_market_sentiment_from_akshare():
    """
    从akshare获取市场情绪数据
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return None, "akshare返回空数据"

        limit_up = df[df["涨跌幅"] >= 9.8]
        limit_up_count = len(limit_up)

        limit_down = df[df["涨跌幅"] <= -9.8]
        limit_down_count = len(limit_down)

        zt_pool = df[df["涨跌幅"] >= 9.8]
        high_vol = df[df["成交额"] > df["成交额"].quantile(0.9)]
        bomb_candidates = high_vol[(high_vol["涨跌幅"] >= 5) & (high_vol["涨跌幅"] < 9.8)]
        bomb_rate = len(bomb_candidates) / max(len(zt_pool), 1) if len(zt_pool) > 0 else 0

        avg_change = df["涨跌幅"].mean()
        rising_count = len(df[df["涨跌幅"] > 0])
        falling_count = len(df[df["涨跌幅"] < 0])
        flat_count = len(df[df["涨跌幅"] == 0])
        total_count = len(df)

        rise_ratio = rising_count / total_count * 100 if total_count > 0 else 0

        strong_stocks = df[df["涨跌幅"] >= 5]
        strong_count = len(strong_stocks)

        weak_stocks = df[df["涨跌幅"] <= -5]
        weak_count = len(weak_stocks)

        if limit_up_count > 80:
            mood = "高潮"
        elif limit_up_count > 50:
            mood = "强势"
        elif limit_up_count > 30:
            mood = "震荡"
        else:
            mood = "退潮"

        total_volume = df["成交额"].sum()
        market_cap_total = df["总市值"].sum() if "总市值" in df.columns else 0

        return {
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
            "bomb_rate": round(bomb_rate, 2),
            "avg_change": round(avg_change, 2),
            "market_mood": mood,
            "rising_count": rising_count,
            "falling_count": falling_count,
            "flat_count": flat_count,
            "total_count": total_count,
            "rise_ratio": round(rise_ratio, 2),
            "strong_count": strong_count,
            "weak_count": weak_count,
            "total_volume": round(total_volume / 1e12, 2),
            "market_cap": round(market_cap_total / 1e12, 2) if market_cap_total else 0
        }, None
    except Exception as e:
        error_str = str(e)
        is_network_error = any([
            "ProxyError" in error_str,
            "Max retries exceeded" in error_str,
            "Connection aborted" in error_str,
            "RemoteDisconnected" in error_str,
            isinstance(e, requests.exceptions.ConnectionError)
        ])
        if is_network_error:
            return None, f"网络连接错误: {error_str[:50]}"
        return None, str(e)

def _get_market_sentiment_from_eastmoney():
    """
    从东方财富备用接口获取市场情绪数据
    """
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 5000,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://quote.eastmoney.com/"
        }

        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, f"东方财富API返回状态码: {response.status_code}"

        data = response.json()
        if not data or "data" not in data or not data["data"]:
            return None, "东方财富API返回数据为空"

        stocks = data["data"]["diff"]
        if not stocks:
            return None, "东方财富API没有股票数据"

        total = len(stocks)
        rising = sum(1 for s in stocks if s.get("f3", 0) > 0)
        falling = sum(1 for s in stocks if s.get("f3", 0) < 0)
        limit_up = sum(1 for s in stocks if s.get("f3", 0) >= 9.8)
        limit_down = sum(1 for s in stocks if s.get("f3", 0) <= -9.8)
        strong = sum(1 for s in stocks if s.get("f3", 0) >= 5)

        avg_change = sum(s.get("f3", 0) for s in stocks) / max(total, 1)

        if limit_up > 80:
            mood = "高潮"
        elif limit_up > 50:
            mood = "强势"
        elif limit_up > 30:
            mood = "震荡"
        else:
            mood = "退潮"

        return {
            "limit_up_count": limit_up,
            "limit_down_count": limit_down,
            "bomb_rate": 0.0,
            "avg_change": round(avg_change, 2),
            "market_mood": mood,
            "rising_count": rising,
            "falling_count": falling,
            "flat_count": total - rising - falling,
            "total_count": total,
            "rise_ratio": round(rising / max(total, 1) * 100, 2),
            "strong_count": strong,
            "weak_count": 0,
            "total_volume": 0.0,
            "market_cap": 0.0
        }, None
    except Exception as e:
        return None, f"东方财富备用API失败: {str(e)[:80]}"

def _get_market_sentiment_from_xueqiu():
    """
    从雪球API获取市场情绪数据（通过大盘指数估算）
    """
    try:
        import requests

        session = requests.Session()
        session.trust_env = False
        session.proxies = {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://xueqiu.com/'
        }

        url = 'https://stock.xueqiu.com/v5/stock/realtime/quotec.json'
        params = {
            'symbol': 'SH000001,SZ399001,SZ399006'
        }

        r = session.get(url, params=params, headers=headers, timeout=15)

        if r.status_code != 200:
            return None, f"雪球API返回状态码: {r.status_code}"

        data = r.json()
        if not data or 'data' not in data or not data['data']:
            return None, "雪球API返回数据为空"

        quotes = data['data']
        if not quotes:
            return None, "雪球API没有指数数据"

        total_change = 0
        total_percent = 0
        for quote in quotes:
            percent = quote.get('percent', 0)
            total_percent += percent
            total_change += 1

        avg_percent = total_percent / max(total_change, 1)

        rising_est = int((avg_percent + 2) * 1250)
        falling_est = int((2 - avg_percent) * 1250)
        rising_est = max(0, min(rising_est, 4000))
        falling_est = max(0, min(falling_est, 4000))

        limit_up_est = max(0, int((avg_percent - 1) * 20))
        limit_down_est = max(0, int((1 + avg_percent) * 10))

        if avg_percent >= 3:
            mood = "高潮"
        elif avg_percent >= 1.5:
            mood = "强势"
        elif avg_percent >= -1:
            mood = "震荡"
        elif avg_percent >= -3:
            mood = "弱势"
        else:
            mood = "退潮"

        return {
            "limit_up_count": limit_up_est,
            "limit_down_count": limit_down_est,
            "bomb_rate": 0.0,
            "avg_change": round(avg_percent, 2),
            "market_mood": mood,
            "rising_count": rising_est,
            "falling_count": falling_est,
            "flat_count": max(0, 5000 - rising_est - falling_est),
            "total_count": 5000,
            "rise_ratio": round(rising_est / 50.0, 2),
            "strong_count": int(limit_up_est * 2),
            "weak_count": int(limit_down_est * 2),
            "total_volume": 0.0,
            "market_cap": 0.0,
            "is_xueqiu_data": True
        }, None
    except Exception as e:
        return None, f"雪球API失败: {str(e)[:50]}"

def _get_mock_market_sentiment():
    """
    获取模拟市场情绪数据（当所有API都失败时使用）
    """
    return {
        "limit_up_count": 50,
        "limit_down_count": 10,
        "bomb_rate": 0.15,
        "avg_change": 0.85,
        "market_mood": "震荡",
        "rising_count": 2500,
        "falling_count": 2000,
        "flat_count": 500,
        "total_count": 5000,
        "rise_ratio": 55.0,
        "strong_count": 200,
        "weak_count": 150,
        "total_volume": 8.5,
        "market_cap": 80.0,
        "is_mock": True
    }

def get_market_sentiment(use_cache=True):
    """
    获取A股全市场情绪数据
    use_cache: 是否优先使用缓存数据
    """
    global _sentiment_cache, _sentiment_cache_time

    if use_cache and _sentiment_cache is not None and _sentiment_cache_time is not None:
        if time.time() - _sentiment_cache_time < _sentiment_cache_ttl:
            print("📦 使用内存缓存的市场情绪数据")
            return _sentiment_cache

    cached = get_cached_market_sentiment()
    if use_cache and cached:
        print("📦 使用数据库缓存的市场情绪数据")
        _sentiment_cache = cached
        _sentiment_cache_time = time.time()
        return cached

    # 尝试akshare主数据源
    print("正在获取市场情绪数据...")
    result, error = _get_market_sentiment_from_akshare()

    if result is None:
        print(f"⚠️ akshare市场情绪获取失败: {error}，尝试东方财富备用接口...")

        # 尝试东方财富备用数据源
        result, error = _get_market_sentiment_from_eastmoney()

        if result is None:
            print(f"⚠️ 东方财富备用接口也失败: {error}，尝试雪球API...")

            # 尝试雪球API
            result, error = _get_market_sentiment_from_xueqiu()

            if result is None:
                print(f"⚠️ 雪球API也失败: {error}")

                # 返回缓存数据
                if _sentiment_cache is not None:
                    print("📦 API失败，返回内存缓存数据")
                    return _sentiment_cache
                if cached:
                    print("📦 API失败，返回数据库缓存数据")
                    return cached

                # 无法获取任何数据，使用模拟数据
                print("⚠️ 所有API和缓存都失败，使用模拟市场情绪数据")
                result = _get_mock_market_sentiment()
                print("📦 返回模拟数据，请注意这不是真实市场数据")

    save_market_sentiment(result)
    _sentiment_cache = result
    _sentiment_cache_time = time.time()
    print("✅ 市场情绪数据已获取并保存")
    return result

def get_sector_data():
    """
    获取板块涨跌排名数据（简化版）
    """
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
        
        if df is None or df.empty:
            print("警告: 获取到的板块数据为空")
            return None

        top_gainers = df.nlargest(10, "涨跌幅")[["板块名称", "涨跌幅", "总市值", "上涨家数", "下跌家数"]]
        top_losers = df.nsmallest(10, "涨跌幅")[["板块名称", "涨跌幅", "总市值", "上涨家数", "下跌家数"]]

        sector_data = {
            "top_gainers": [],
            "top_losers": []
        }

        for _, row in top_gainers.iterrows():
            sector_data["top_gainers"].append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "rise_count": int(row["上涨家数"]),
                "fall_count": int(row["下跌家数"])
            })

        for _, row in top_losers.iterrows():
            sector_data["top_losers"].append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "rise_count": int(row["上涨家数"]),
                "fall_count": int(row["下跌家数"])
            })

        return sector_data
    except Exception as e:
        print(f"获取板块数据失败: {e}")
        return None

_hot_sectors_cache = None
_hot_sectors_cache_time = None
_hot_sectors_cache_ttl = 300

def _get_mock_hot_sectors():
    """获取模拟热门板块数据（当API失败时使用）"""
    return [
        {"name": "人工智能", "change_pct": 3.25, "turnover_rate": 5.2, "rise_count": 156, "fall_count": 23},
        {"name": "芯片", "change_pct": 2.88, "turnover_rate": 6.1, "rise_count": 142, "fall_count": 31},
        {"name": "新能源汽车", "change_pct": 2.45, "turnover_rate": 4.8, "rise_count": 128, "fall_count": 38},
        {"name": "数字经济", "change_pct": 2.21, "turnover_rate": 3.9, "rise_count": 98, "fall_count": 42},
        {"name": "光伏", "change_pct": 1.98, "turnover_rate": 4.2, "rise_count": 87, "fall_count": 35},
        {"name": "储能", "change_pct": 1.75, "turnover_rate": 3.5, "rise_count": 76, "fall_count": 29},
        {"name": "机器人", "change_pct": 1.52, "turnover_rate": 4.0, "rise_count": 65, "fall_count": 25},
        {"name": "医疗健康", "change_pct": 1.25, "turnover_rate": 2.8, "rise_count": 58, "fall_count": 42},
        {"name": "消费电子", "change_pct": 0.98, "turnover_rate": 3.2, "rise_count": 48, "fall_count": 48},
        {"name": "房地产", "change_pct": 0.75, "turnover_rate": 2.1, "rise_count": 42, "fall_count": 52}
    ]

def get_hot_sectors(use_cache=True):
    """
    获取热门板块（概念板块涨幅排行）
    use_cache: 是否优先使用缓存数据
    """
    global _hot_sectors_cache, _hot_sectors_cache_time

    if use_cache and _hot_sectors_cache is not None and _hot_sectors_cache_time is not None:
        if time.time() - _hot_sectors_cache_time < _hot_sectors_cache_ttl:
            print("📦 使用内存缓存的热门板块数据")
            return _hot_sectors_cache

    cached = get_cached_hot_sectors()
    if use_cache and cached:
        print("📦 使用数据库缓存的热门板块数据")
        _hot_sectors_cache = cached
        _hot_sectors_cache_time = time.time()
        return cached

    try:
        print("正在获取热门板块数据...")
        import akshare as ak
        df = ak.stock_board_concept_name_em()
        
        if df is None or df.empty:
            print("警告: 获取到的热门板块数据为空")
            if _hot_sectors_cache is not None:
                return _hot_sectors_cache
            if cached:
                return cached
            # 使用模拟数据
            result = _get_mock_hot_sectors()
            print("📦 使用模拟热门板块数据")
            return result

        hot_sectors = df.nlargest(15, "涨跌幅")[["板块名称", "涨跌幅", "换手率", "上涨家数", "下跌家数", "总市值"]]

        result = []
        for _, row in hot_sectors.iterrows():
            result.append({
                "name": row["板块名称"],
                "change_pct": round(row["涨跌幅"], 2),
                "turnover_rate": round(row["换手率"], 2) if pd.notna(row["换手率"]) else 0,
                "rise_count": int(row["上涨家数"]),
                "fall_count": int(row["下跌家数"])
            })

        save_hot_sectors_cache(result)
        _hot_sectors_cache = result
        _hot_sectors_cache_time = time.time()
        print("✅ 热门板块数据已获取并保存")
        return result
    except Exception as e:
        error_str = str(e)
        is_network_error = any([
            "ProxyError" in error_str,
            "Max retries exceeded" in error_str,
            "Connection aborted" in error_str,
            "RemoteDisconnected" in error_str
        ])
        if is_network_error:
            print(f"⚠️ 网络连接错误，获取热门板块失败: {error_str[:50]}")
        else:
            print(f"获取热门板块失败: {e}")
        
        if _hot_sectors_cache is not None:
            print("📦 获取失败，返回内存缓存数据")
            return _hot_sectors_cache
        if cached:
            print("📦 获取失败，返回数据库缓存数据")
            return cached
        # 使用模拟数据
        result = _get_mock_hot_sectors()
        print("📦 使用模拟热门板块数据")
        return result

def analyze_sentiment():
    """
    分析市场情绪（兼容旧API）
    返回市场情绪数据字典
    """
    return get_market_sentiment()


def format_market_sentiment(data, sector_data=None, hot_sectors=None):
    """
    格式化市场情绪数据为易读字符串
    """
    if not data:
        return "未获取到市场情绪数据"

    lines = [
        f"【市场情绪概览】",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"涨停家数: {data['limit_up_count']}家",
        f"跌停家数: {data['limit_down_count']}家",
        f"炸板率: {data['bomb_rate']*100:.1f}%",
        f"市场情绪: {data['market_mood']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"上涨家数: {data['rising_count']}家 ({data['rise_ratio']}%)",
        f"下跌家数: {data['falling_count']}家",
        f"平盘家数: {data['flat_count']}家",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"强势股(≥5%): {data['strong_count']}家",
        f"弱势股(≤-5%): {data['weak_count']}家",
        f"市场平均涨跌: {data['avg_change']:.2f}%",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"全市场成交额: {data['total_volume']:.2f}万亿",
        f"总市值: {data['market_cap']:.2f}万亿",
    ]

    if sector_data and sector_data.get("top_gainers"):
        lines.append(f"")
        lines.append(f"【涨幅前五板块】")
        for i, sector in enumerate(sector_data["top_gainers"][:5], 1):
            lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}%")

    if hot_sectors:
        lines.append(f"")
        lines.append(f"【热门概念板块】")
        for i, sector in enumerate(hot_sectors[:5], 1):
            lines.append(f"{i}. {sector['name']}: +{sector['change_pct']}% (换手{sector['turnover_rate']}%)")

    return "\n".join(lines)
