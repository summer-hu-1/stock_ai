"""
API端点注册器

集中配置所有API端点及其降级策略
"""

import logging
from typing import Dict, Callable, Any
from .manager import (
    APIFallbackManager,
    get_fallback_manager,
    MarketType,
    DataType,
    RunMode,
    api_fallback
)

logger = logging.getLogger(__name__)


def register_default_apis():
    """
    注册默认API端点

    此函数注册系统中所有可用的API端点及其降级策略
    """
    manager = get_fallback_manager()

    # ========== A股 API ==========

    # A股 - 个股数据
    def akshare_a_stock_data(code: str, **kwargs) -> Dict[str, Any]:
        """akshare A股个股数据"""
        import akshare as ak
        import os

        # 禁用代理
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return None

        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()
        row = df[df["代码"] == pure_code]

        if row.empty:
            return None

        return {
            "code": pure_code,
            "name": row["名称"].values[0],
            "price": float(row["最新价"].values[0]),
            "change_pct": float(row["涨跌幅"].values[0]),
            "turnover": float(row["换手率"].values[0]),
            "volume": float(row["成交额"].values[0]),
            "high": float(row["最高"].values[0]),
            "low": float(row["最低"].values[0]),
            "open": float(row["今开"].values[0]),
            "close": float(row["昨收"].values[0]),
            "amplitude": float(row["振幅"].values[0]),
            "volume_ratio": float(row["量比"].values[0]),
            "market": "A",
        }

    def akshare_a_stock_hist(code: str, **kwargs) -> Any:
        """akshare A股历史数据"""
        import akshare as ak
        import os
        from datetime import datetime, timedelta

        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        start_date = kwargs.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
        end_date = kwargs.get('end_date', datetime.now().strftime('%Y%m%d'))

        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()
        df = ak.stock_zh_a_hist(symbol=pure_code, period='daily', start_date=start_date, end_date=end_date, adjust='')

        if df is None or df.empty:
            return None
        return df

    def xueqiu_a_stock_data(code: str, **kwargs) -> Dict[str, Any]:
        """雪球API A股数据"""
        import requests
        import os

        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        session = requests.Session()
        session.trust_env = False
        session.proxies = {}

        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()

        # 判断市场
        if pure_code.startswith('6'):
            market = 'SH'
        else:
            market = 'SZ'

        url = f'https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol={market}{pure_code}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': f'https://xueqiu.com/S/{market}{pure_code}'
        }

        r = session.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        quote = data.get('data', []).get('quote', {})

        if not quote:
            return None

        return {
            "code": pure_code,
            "name": quote.get('name', ''),
            "price": float(quote.get('current', 0)),
            "change_pct": float(quote.get('percent', 0)),
            "turnover": float(quote.get('turnover_rate', 0)),
            "volume": float(quote.get('amount', 0)),
            "high": float(quote.get('high', 0)),
            "low": float(quote.get('low', 0)),
            "open": float(quote.get('open', 0)),
            "close": float(quote.get('last_close', 0)),
            "amplitude": 0.0,
            "volume_ratio": float(quote.get('volume_ratio', 0)),
            "market": "A",
        }

    def csv_a_stock_data(code: str, **kwargs) -> Dict[str, Any]:
        """本地CSV A股数据"""
        import os
        import pandas as pd
        from datetime import datetime

        pure_code = code.replace(".SH", "").replace(".SZ", "").strip()

        # 查找CSV文件
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'cn', 'daily')
        csv_path = os.path.join(data_dir, f'{pure_code}.csv')

        if not os.path.exists(csv_path):
            return None

        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                return None

            # 获取最新数据
            latest = df.iloc[-1]

            # 尝试获取股票名称
            stock_name = kwargs.get('name', pure_code)

            return {
                "code": pure_code,
                "name": stock_name,
                "price": float(latest['close']),
                "change_pct": float(latest['price_change_pct']),
                "volume": float(latest['amount']),
                "turnover": float(latest.get('turnover_rate', 0)),
                "high": float(latest['high']),
                "low": float(latest['low']),
                "open": float(latest['open']),
                "close": float(latest['close']),
                "amplitude": float(latest.get('amplitude', 0)),
                "volume_ratio": 0.0,
                "market": "A",
            }
        except Exception as e:
            logger.warning(f"读取CSV失败: {csv_path}, 错误: {e}")
            return None

    # A股 - 市场情绪
    def akshare_a_sentiment(**kwargs) -> Dict[str, Any]:
        """akshare A股市场情绪"""
        import akshare as ak
        import os

        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return None

        limit_up = df[df["涨跌幅"] >= 9.8]
        limit_up_count = len(limit_up)

        limit_down = df[df["涨跌幅"] <= -9.8]
        limit_down_count = len(limit_down)

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

        total_volume = df["成交额"].sum()

        if limit_up_count > 80:
            mood = "高潮"
        elif limit_up_count > 50:
            mood = "强势"
        elif limit_up_count > 30:
            mood = "震荡"
        else:
            mood = "退潮"

        return {
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
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
            "market": "A",
        }

    # A股 - 板块数据
    def akshare_a_sectors(**kwargs) -> list:
        """akshare A股板块数据"""
        import akshare as ak
        import os

        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        df = ak.stock_board_industry_name_em()
        if df is None or df.empty:
            return []

        sectors = []
        for _, row in df.head(10).iterrows():
            sectors.append({
                "name": row.get("板块名称", ""),
                "change_pct": float(row.get("涨跌幅", 0)),
                "volume": float(row.get("成交额", 0)),
                "stock_count": int(row.get("上涨家数", 0)) + int(row.get("下跌家数", 0)),
                "up_count": int(row.get("上涨家数", 0)),
                "down_count": int(row.get("下跌家数", 0)),
            })
        return sectors

    # A股 - 股票列表
    def akshare_a_stock_list(**kwargs) -> list:
        """akshare A股股票列表"""
        import akshare as ak
        import os

        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        df = ak.stock_info_a_code_name()
        if df is None or df.empty:
            return []

        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                "code": str(row.get("code", row.get("代码", ""))),
                "name": str(row.get("name", row.get("名称", ""))),
            })
        return stocks

    # ========== 注册API端点 ==========

    # A股 - 个股数据
    manager.register_api(
        name="akshare_a_stock_data",
        provider=akshare_a_stock_data,
        market=MarketType.A_STOCK,
        data_type=DataType.STOCK_DATA,
        run_mode=RunMode.STANDARD,
        priority=0,
        timeout=15.0,
        retry_count=2
    )

    manager.register_api(
        name="xueqiu_a_stock_data",
        provider=xueqiu_a_stock_data,
        market=MarketType.A_STOCK,
        data_type=DataType.STOCK_DATA,
        run_mode=RunMode.STANDARD,
        priority=1,
        timeout=10.0,
        retry_count=2
    )

    manager.register_api(
        name="csv_a_stock_data",
        provider=csv_a_stock_data,
        market=MarketType.A_STOCK,
        data_type=DataType.STOCK_DATA,
        run_mode=RunMode.FAST,
        priority=0,
        timeout=5.0,
        retry_count=1
    )

    # A股 - 历史数据
    manager.register_api(
        name="akshare_a_stock_hist",
        provider=akshare_a_stock_hist,
        market=MarketType.A_STOCK,
        data_type=DataType.HISTORICAL_DATA,
        run_mode=RunMode.STANDARD,
        priority=0,
        timeout=30.0,
        retry_count=2
    )

    # A股 - 市场情绪
    manager.register_api(
        name="akshare_a_sentiment",
        provider=akshare_a_sentiment,
        market=MarketType.A_STOCK,
        data_type=DataType.MARKET_SENTIMENT,
        run_mode=RunMode.STANDARD,
        priority=0,
        timeout=30.0,
        retry_count=2
    )

    # A股 - 板块数据
    manager.register_api(
        name="akshare_a_sectors",
        provider=akshare_a_sectors,
        market=MarketType.A_STOCK,
        data_type=DataType.SECTOR_DATA,
        run_mode=RunMode.STANDARD,
        priority=0,
        timeout=30.0,
        retry_count=2
    )

    # A股 - 股票列表
    manager.register_api(
        name="akshare_a_stock_list",
        provider=akshare_a_stock_list,
        market=MarketType.A_STOCK,
        data_type=DataType.STOCK_LIST,
        run_mode=RunMode.NORMAL,
        priority=0,
        timeout=60.0,
        retry_count=2
    )

    logger.info("✅ 默认API端点注册完成")


def get_stock_data_with_fallback(code: str, market: MarketType = MarketType.A_STOCK, **kwargs) -> Dict[str, Any]:
    """
    获取股票数据（带自动降级）

    Args:
        code: 股票代码
        market: 市场类型
        **kwargs: 额外参数

    Returns:
        Dict[str, Any]: 股票数据
    """
    manager = get_fallback_manager()
    result = manager.call_with_fallback(market, DataType.STOCK_DATA, RunMode.STANDARD, code, **kwargs)
    return result.data if result.success else None


def get_market_sentiment_with_fallback(market: MarketType = MarketType.A_STOCK) -> Dict[str, Any]:
    """
    获取市场情绪数据（带自动降级）

    Args:
        market: 市场类型

    Returns:
        Dict[str, Any]: 市场情绪数据
    """
    manager = get_fallback_manager()
    result = manager.call_with_fallback(market, DataType.MARKET_SENTIMENT, RunMode.STANDARD)
    return result.data if result.success else None


def get_sectors_with_fallback(market: MarketType = MarketType.A_STOCK) -> list:
    """
    获取板块数据（带自动降级）

    Args:
        market: 市场类型

    Returns:
        list: 板块数据列表
    """
    manager = get_fallback_manager()
    result = manager.call_with_fallback(market, DataType.SECTOR_DATA, RunMode.STANDARD)
    return result.data if result.success else []


def get_stock_list_with_fallback(market: MarketType = MarketType.A_STOCK) -> list:
    """
    获取股票列表（带自动降级）

    Args:
        market: 市场类型

    Returns:
        list: 股票列表
    """
    manager = get_fallback_manager()
    result = manager.call_with_fallback(market, DataType.STOCK_LIST, RunMode.NORMAL)
    return result.data if result.success else []
