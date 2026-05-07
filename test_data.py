import sys
sys.path.append('/Users/alittle/Documents/repo/ai/review_your_life/stock_ai')

from modules.market_data import get_stock_data, format_stock_data

print("正在获取股票数据...")

data = get_stock_data("601360")

if data:
    print("\n=== 获取成功 ===")
    print(format_stock_data(data))
else:
    print("获取失败")
