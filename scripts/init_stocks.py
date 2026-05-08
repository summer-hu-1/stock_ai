"""
初始化股票数据库
向各个市场的数据库添加示例股票数据
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.symbol_resolver import SymbolResolver
from core.market_registry import MARKETS


def init_cn_stocks():
    """初始化A股股票数据"""
    resolver = SymbolResolver(MARKETS["A股"])
    
    stocks = [
        {"code": "600519", "name": "贵州茅台", "sector": "白酒"},
        {"code": "000858", "name": "五粮液", "sector": "白酒"},
        {"code": "601318", "name": "中国平安", "sector": "保险"},
        {"code": "000002", "name": "万科A", "sector": "房地产"},
        {"code": "600036", "name": "招商银行", "sector": "银行"},
        {"code": "601398", "name": "工商银行", "sector": "银行"},
        {"code": "600030", "name": "中信证券", "sector": "证券"},
        {"code": "300750", "name": "宁德时代", "sector": "新能源"},
        {"code": "002594", "name": "比亚迪", "sector": "汽车"},
        {"code": "601360", "name": "三六零", "sector": "计算机"},
        {"code": "000063", "name": "中兴通讯", "sector": "通信"},
        {"code": "600585", "name": "海螺水泥", "sector": "建材"},
        {"code": "601899", "name": "紫金矿业", "sector": "有色"},
        {"code": "600000", "name": "浦发银行", "sector": "银行"},
        {"code": "601628", "name": "中国人寿", "sector": "保险"},
    ]
    
    resolver.bulk_add_stocks(stocks)
    print("✅ A股股票数据初始化完成")


def init_hk_stocks():
    """初始化港股股票数据"""
    resolver = SymbolResolver(MARKETS["港股"])
    
    stocks = [
        {"code": "00700", "name": "腾讯控股", "name_en": "Tencent"},
        {"code": "00005", "name": "汇丰控股", "name_en": "HSBC"},
        {"code": "0001", "name": "长和", "name_en": "CK Hutchison"},
        {"code": "0006", "name": "电能实业", "name_en": "Power Assets"},
        {"code": "0011", "name": "恒生银行", "name_en": "Hang Seng Bank"},
        {"code": "0016", "name": "新鸿基地产", "name_en": "Sun Hung Kai"},
        {"code": "0083", "name": "信和置业", "name_en": "Sino Land"},
        {"code": "0101", "name": "恒基地产", "name_en": "Hang Lung"},
        {"code": "0151", "name": "中国旺旺", "name_en": "Want Want"},
        {"code": "0175", "name": "吉利汽车", "name_en": "Geely"},
        {"code": "0267", "name": "中信股份", "name_en": "CITIC"},
        {"code": "0288", "name": "大新金融", "name_en": "Dah Sing"},
        {"code": "0386", "name": "中国石油", "name_en": "PetroChina"},
        {"code": "0388", "name": "香港交易所", "name_en": "HKEX"},
        {"code": "0688", "name": "中国海外发展", "name_en": "COLI"},
    ]
    
    resolver.bulk_add_stocks(stocks)
    print("✅ 港股股票数据初始化完成")


def init_us_stocks():
    """初始化美股股票数据"""
    resolver = SymbolResolver(MARKETS["美股"])
    
    stocks = [
        {"code": "AAPL", "name": "苹果", "name_en": "Apple"},
        {"code": "MSFT", "name": "微软", "name_en": "Microsoft"},
        {"code": "GOOGL", "name": "谷歌", "name_en": "Google"},
        {"code": "AMZN", "name": "亚马逊", "name_en": "Amazon"},
        {"code": "META", "name": "Meta", "name_en": "Meta"},
        {"code": "TSLA", "name": "特斯拉", "name_en": "Tesla"},
        {"code": "NVDA", "name": "英伟达", "name_en": "NVIDIA"},
        {"code": "JPM", "name": "摩根大通", "name_en": "JPMorgan"},
        {"code": "V", "name": "Visa", "name_en": "Visa"},
        {"code": "JNJ", "name": "强生", "name_en": "Johnson & Johnson"},
        {"code": "WMT", "name": "沃尔玛", "name_en": "Walmart"},
        {"code": "PG", "name": "宝洁", "name_en": "Procter & Gamble"},
        {"code": "KO", "name": "可口可乐", "name_en": "Coca-Cola"},
        {"code": "DIS", "name": "迪士尼", "name_en": "Disney"},
        {"code": "BABA", "name": "阿里巴巴", "name_en": "Alibaba"},
    ]
    
    resolver.bulk_add_stocks(stocks)
    print("✅ 美股股票数据初始化完成")


if __name__ == "__main__":
    print("🚀 开始初始化股票数据库...")
    init_cn_stocks()
    init_hk_stocks()
    init_us_stocks()
    print("\n🎉 所有股票数据库初始化完成！")
