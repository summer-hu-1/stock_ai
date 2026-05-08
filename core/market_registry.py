"""
市场配置注册表
定义所有支持的市场及其配置信息
"""

MARKETS = {
    "A股": {
        "code": "CN",
        "db": "stocks_cn.db",
        "provider": "ashare",
        "description": "中国大陆A股市场",
        "suffix": ".SH",
        "example": "贵州茅台 / 600519",
        "enabled": True
    },
    "港股": {
        "code": "HK",
        "db": "stocks_hk.db",
        "provider": "hk",
        "description": "香港联合交易所",
        "suffix": ".HK",
        "example": "腾讯控股 / 00700",
        "enabled": True
    },
    "美股": {
        "code": "US",
        "db": "stocks_us.db",
        "provider": "us",
        "description": "美国股票市场",
        "suffix": "",
        "example": "Apple / AAPL",
        "enabled": True
    }
}


def get_market_names():
    """获取所有可用市场名称"""
    return [name for name, config in MARKETS.items() if config.get("enabled", True)]


def get_market_config(market_name: str):
    """获取指定市场的配置"""
    return MARKETS.get(market_name)


def get_all_markets():
    """获取所有市场配置"""
    return MARKETS
