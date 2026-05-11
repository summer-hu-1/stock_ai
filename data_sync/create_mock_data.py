#!/usr/bin/env python3
"""
测试数据同步 - 创建模拟数据用于测试
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")

os.makedirs(data_dir, exist_ok=True)

# 模拟股票列表
STOCKS = [
    {"code": "000001", "name": "平安银行"},
    {"code": "000002", "name": "万科A"},
    {"code": "600519", "name": "贵州茅台"},
    {"code": "000858", "name": "五粮液"},
    {"code": "601318", "name": "中国平安"},
]

# 创建股票列表文件
stock_list_path = os.path.join(project_dir, "data", "cn", "stock_list.csv")
os.makedirs(os.path.dirname(stock_list_path), exist_ok=True)
pd.DataFrame(STOCKS).to_csv(stock_list_path, index=False)
print(f"✅ 股票列表已创建: {stock_list_path}")


def create_mock_data(code, years=3):
    """创建模拟历史数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    dates = []
    open_prices = []
    high_prices = []
    low_prices = []
    close_prices = []
    volumes = []
    amounts = []
    amplitudes = []
    price_changes = []
    turnover_rates = []
    
    # 初始价格
    base_price = 10.0 if code.startswith('0') else 100.0
    
    current_price = base_price
    date = start_date
    
    while date <= end_date:
        # 只保留工作日
        if date.weekday() < 5:
            # 随机波动
            change = (np.random.rand() - 0.5) * 2  # -1 to +1
            open_p = current_price * (1 + change * 0.01)
            close_p = open_p * (1 + (np.random.rand() - 0.5) * 0.04)
            high_p = max(open_p, close_p) * (1 + np.random.rand() * 0.02)
            low_p = min(open_p, close_p) * (1 - np.random.rand() * 0.02)
            
            dates.append(date.strftime('%Y-%m-%d'))
            open_prices.append(round(open_p, 2))
            high_prices.append(round(high_p, 2))
            low_prices.append(round(low_p, 2))
            close_prices.append(round(close_p, 2))
            volumes.append(int(np.random.randint(1000000, 10000000)))
            amounts.append(round(close_p * volumes[-1], 2))
            amplitudes.append(round(((high_p - low_p) / open_p) * 100, 2))
            price_changes.append(round(((close_p - current_price) / current_price) * 100, 2))
            turnover_rates.append(round(np.random.rand() * 5, 2))
            
            current_price = close_p
        
        date += timedelta(days=1)
    
    df = pd.DataFrame({
        'date': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes,
        'amount': amounts,
        'amplitude': amplitudes,
        'price_change_pct': price_changes,
        'turnover_rate': turnover_rates
    })
    
    return df


# 创建模拟数据
print("\n📊 创建模拟数据...")
for stock in STOCKS:
    code = stock['code']
    save_path = os.path.join(data_dir, f"{code}.csv")
    
    if os.path.exists(save_path):
        print(f"⏭️ 跳过已存在: {code}")
        continue
    
    df = create_mock_data(code)
    df.to_csv(save_path, index=False)
    print(f"✅ {code} ({stock['name']}): {len(df)} 条记录")

print("\n🎉 模拟数据创建完成！")
print(f"数据目录: {data_dir}")