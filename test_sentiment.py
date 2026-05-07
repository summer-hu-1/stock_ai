import sys
sys.path.append('/Users/alittle/Documents/repo/ai/review_your_life/stock_ai')

from modules.market_sentiment import get_market_sentiment, get_sector_data, get_hot_sectors, format_market_sentiment

print("正在获取市场情绪数据...\n")

sentiment = get_market_sentiment()

if sentiment:
    print("=== 市场情绪数据获取成功 ===")
    print(format_market_sentiment(sentiment))
else:
    print("市场情绪数据获取失败")

print("\n" + "="*50 + "\n")

print("正在获取板块数据...\n")

sectors = get_sector_data()
if sectors:
    print("=== 板块数据获取成功 ===")
    if sectors["top_gainers"]:
        print("涨幅前五板块:")
        for s in sectors["top_gainers"][:5]:
            print(f"  {s['name']}: +{s['change_pct']}%")
    if sectors["top_losers"]:
        print("\n跌幅前五板块:")
        for s in sectors["top_losers"][:5]:
            print(f"  {s['name']}: {s['change_pct']}%")
else:
    print("板块数据获取失败")

print("\n" + "="*50 + "\n")

print("正在获取热门概念板块...\n")

hot = get_hot_sectors()
if hot:
    print("=== 热门概念板块获取成功 ===")
    for i, s in enumerate(hot[:10], 1):
        print(f"{i}. {s['name']}: +{s['change_pct']}% (换手{s['turnover_rate']}%)")
else:
    print("热门概念板块获取失败")
