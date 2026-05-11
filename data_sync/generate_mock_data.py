#!/usr/bin/env python3
"""
生成完整的A股股票列表和模拟日线数据

功能：
1. 创建完整的A股股票列表（包含常见的股票代码和名称）
2. 按股票名称拼音排序
3. 为每只股票生成近三年的模拟日线数据
4. 支持断点续传
"""

import pandas as pd
import numpy as np
import os
import time
from tqdm import tqdm
from datetime import datetime, timedelta

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")
stock_list_path = os.path.join(project_dir, "data", "cn", "stock_list.csv")

os.makedirs(data_dir, exist_ok=True)

# 扩展的A股股票列表（按名称拼音排序）
STOCK_LIST = [
    {"code": "000001", "name": "平安银行"},
    {"code": "000002", "name": "万科A"},
    {"code": "000009", "name": "中国宝安"},
    {"code": "000063", "name": "中兴通讯"},
    {"code": "000066", "name": "中国长城"},
    {"code": "000157", "name": "中联重科"},
    {"code": "000333", "name": "美的集团"},
    {"code": "000538", "name": "云南白药"},
    {"code": "000568", "name": "泸州老窖"},
    {"code": "000651", "name": "格力电器"},
    {"code": "000725", "name": "京东方A"},
    {"code": "000768", "name": "中航沈飞"},
    {"code": "000858", "name": "五粮液"},
    {"code": "000895", "name": "双汇发展"},
    {"code": "000938", "name": "紫光国微"},
    {"code": "000963", "name": "华东医药"},
    {"code": "002001", "name": "新和成"},
    {"code": "002008", "name": "大族激光"},
    {"code": "002024", "name": "苏宁易购"},
    {"code": "002038", "name": "双鹭药业"},
    {"code": "002050", "name": "三花智控"},
    {"code": "002142", "name": "宁波银行"},
    {"code": "002156", "name": "通富微电"},
    {"code": "002230", "name": "科大讯飞"},
    {"code": "002252", "name": "上海莱士"},
    {"code": "002304", "name": "洋河股份"},
    {"code": "002311", "name": "海大集团"},
    {"code": "002352", "name": "顺丰控股"},
    {"code": "002371", "name": "北方华创"},
    {"code": "002415", "name": "海康威视"},
    {"code": "002456", "name": "欧菲光"},
    {"code": "002594", "name": "比亚迪"},
    {"code": "002601", "name": "龙佰集团"},
    {"code": "002624", "name": "完美世界"},
    {"code": "002714", "name": "牧原股份"},
    {"code": "002841", "name": "视源股份"},
    {"code": "002916", "name": "深南电路"},
    {"code": "002938", "name": "鹏鼎控股"},
    {"code": "002958", "name": "青农商行"},
    {"code": "300015", "name": "爱尔眼科"},
    {"code": "300033", "name": "同花顺"},
    {"code": "300059", "name": "东方财富"},
    {"code": "300122", "name": "智飞生物"},
    {"code": "300251", "name": "光线传媒"},
    {"code": "300347", "name": "泰格医药"},
    {"code": "300408", "name": "三环集团"},
    {"code": "300433", "name": "蓝思科技"},
    {"code": "300498", "name": "温氏股份"},
    {"code": "300601", "name": "康泰生物"},
    {"code": "300750", "name": "宁德时代"},
    {"code": "600000", "name": "浦发银行"},
    {"code": "600008", "name": "首创环保"},
    {"code": "600016", "name": "民生银行"},
    {"code": "600028", "name": "中国石化"},
    {"code": "600030", "name": "中信证券"},
    {"code": "600036", "name": "招商银行"},
    {"code": "600048", "name": "保利发展"},
    {"code": "600050", "name": "中国联通"},
    {"code": "600104", "name": "上汽集团"},
    {"code": "600131", "name": "岷江水电"},
    {"code": "600150", "name": "中国船舶"},
    {"code": "600161", "name": "天坛生物"},
    {"code": "600276", "name": "恒瑞医药"},
    {"code": "600298", "name": "安琪酵母"},
    {"code": "600309", "name": "万华化学"},
    {"code": "600332", "name": "白云山"},
    {"code": "600362", "name": "江西铜业"},
    {"code": "600383", "name": "金地集团"},
    {"code": "600436", "name": "片仔癀"},
    {"code": "600487", "name": "亨通光电"},
    {"code": "600519", "name": "贵州茅台"},
    {"code": "600547", "name": "山东黄金"},
    {"code": "600585", "name": "海螺水泥"},
    {"code": "600606", "name": "绿地控股"},
    {"code": "600690", "name": "海尔智家"},
    {"code": "600703", "name": "三安光电"},
    {"code": "600809", "name": "山西汾酒"},
    {"code": "600887", "name": "伊利股份"},
    {"code": "600900", "name": "长江电力"},
    {"code": "600919", "name": "江苏银行"},
    {"code": "600958", "name": "东方证券"},
    {"code": "600999", "name": "招商证券"},
    {"code": "601006", "name": "大秦铁路"},
    {"code": "601012", "name": "隆基绿能"},
    {"code": "601088", "name": "中国神华"},
    {"code": "601138", "name": "工业富联"},
    {"code": "601166", "name": "兴业银行"},
    {"code": "601186", "name": "中国铁建"},
    {"code": "601211", "name": "国泰君安"},
    {"code": "601288", "name": "农业银行"},
    {"code": "601318", "name": "中国平安"},
    {"code": "601328", "name": "交通银行"},
    {"code": "601336", "name": "新华保险"},
    {"code": "601390", "name": "中国中铁"},
    {"code": "601398", "name": "工商银行"},
    {"code": "601555", "name": "东吴证券"},
    {"code": "601601", "name": "中国太保"},
    {"code": "601628", "name": "中国人寿"},
    {"code": "601668", "name": "中国建筑"},
    {"code": "601688", "name": "华泰证券"},
    {"code": "601766", "name": "中国中车"},
    {"code": "601899", "name": "紫金矿业"},
    {"code": "601939", "name": "建设银行"},
    {"code": "601988", "name": "中国银行"},
    {"code": "601998", "name": "中信银行"},
    {"code": "603127", "name": "昭衍新药"},
    {"code": "603259", "name": "药明康德"},
    {"code": "603288", "name": "海天味业"},
    {"code": "603501", "name": "韦尔股份"},
    {"code": "603899", "name": "晨光文具"},
    {"code": "603986", "name": "兆易创新"},
]


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
    
    # 根据股票类型设置初始价格
    if code.startswith('3'):  # 创业板
        base_price = 30.0
    elif code.startswith('6'):  # 沪市
        base_price = 20.0
    else:  # 深市
        base_price = 15.0
    
    current_price = base_price
    date = start_date
    
    while date <= end_date:
        # 只保留工作日
        if date.weekday() < 5:
            # 随机波动
            change = (np.random.rand() - 0.5) * 2
            open_p = current_price * (1 + change * 0.01)
            close_p = open_p * (1 + (np.random.rand() - 0.5) * 0.04)
            high_p = max(open_p, close_p) * (1 + np.random.rand() * 0.02)
            low_p = min(open_p, close_p) * (1 - np.random.rand() * 0.02)
            
            dates.append(date.strftime('%Y-%m-%d'))
            open_prices.append(round(open_p, 2))
            high_prices.append(round(high_p, 2))
            low_prices.append(round(low_p, 2))
            close_prices.append(round(close_p, 2))
            volumes.append(int(np.random.randint(1000000, 50000000)))
            amounts.append(round(close_p * volumes[-1], 2))
            amplitudes.append(round(((high_p - low_p) / open_p) * 100, 2))
            price_changes.append(round(((close_p - current_price) / current_price) * 100, 2))
            turnover_rates.append(round(np.random.rand() * 8, 2))
            
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


def main():
    # 创建股票列表DataFrame并按名称排序
    stock_df = pd.DataFrame(STOCK_LIST)
    stock_df['code'] = stock_df['code'].apply(lambda x: str(x).zfill(6))
    stock_df = stock_df.sort_values('name')
    
    # 保存股票列表
    os.makedirs(os.path.dirname(stock_list_path), exist_ok=True)
    stock_df.to_csv(stock_list_path, index=False)
    print(f"✅ 股票列表已创建，共 {len(stock_df)} 只股票")
    
    # 统计已存在的文件
    existing_files = set()
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith('.csv'):
                existing_files.add(f.replace('.csv', ''))
    
    print(f"📂 已存在 {len(existing_files)} 个数据文件")
    
    # 按名称排序处理
    print("\n" + "=" * 70)
    print("开始按名称排序生成模拟日线数据")
    print(f"总计股票: {len(stock_df)} | 待生成: {len(stock_df) - len(existing_files)} | 已存在: {len(existing_files)}")
    print("=" * 70)
    
    success = 0
    skipped = 0
    
    for idx, row in tqdm(stock_df.iterrows(), desc="生成进度", total=len(stock_df)):
        code = str(row['code']).zfill(6)
        name = row['name']
        save_path = os.path.join(data_dir, f"{code}.csv")
        
        # 如果文件已存在，跳过
        if code in existing_files:
            skipped += 1
            continue
        
        # 生成模拟数据
        df = create_mock_data(code)
        df.to_csv(save_path, index=False)
        success += 1
        
        # 每处理10只股票显示一次进度
        if (success + skipped) % 10 == 0:
            print(f"\n📊 已处理 {success + skipped}/{len(stock_df)} 只股票")
            print(f"   成功: {success} | 跳过: {skipped}")
    
    print("\n" + "=" * 70)
    print(f"⏭️ 跳过: {skipped} 只（已存在）")
    print(f"✅ 成功生成: {success} 只股票的数据")
    print(f"📁 数据目录: {data_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()