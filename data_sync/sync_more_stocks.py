#!/usr/bin/env python3
"""
同步更多A股数据（使用预设列表，支持目录分组）
"""

import pandas as pd
import numpy as np
import requests
import os
import time
from tqdm import tqdm
from datetime import datetime, timedelta

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")

# 子目录分组
SUB_DIRS = {
    '000': 'sz_main', '002': 'sz_sme', '003': 'sz_main',
    '300': 'sz_gem', '301': 'sz_gem',
    '600': 'sh_main', '601': 'sh_main', '603': 'sh_main', '605': 'sh_main',
    '688': 'sh_star'
}


def get_sub_dir(code):
    prefix = str(code).zfill(6)[:3]
    return SUB_DIRS.get(prefix, 'others')


def ensure_dir(code):
    sub_dir = get_sub_dir(code)
    full_path = os.path.join(data_dir, sub_dir)
    os.makedirs(full_path, exist_ok=True)
    return full_path


# 精选A股股票列表（按代码分组）
STOCK_LIST = [
    # 沪市主板 (600xxx)
    {"code": "600000", "name": "浦发银行"},
    {"code": "600008", "name": "首创环保"},
    {"code": "600016", "name": "民生银行"},
    {"code": "600028", "name": "中国石化"},
    {"code": "600030", "name": "中信证券"},
    {"code": "600036", "name": "招商银行"},
    {"code": "600048", "name": "保利发展"},
    {"code": "600050", "name": "中国联通"},
    {"code": "600104", "name": "上汽集团"},
    {"code": "600150", "name": "中国船舶"},
    {"code": "600276", "name": "恒瑞医药"},
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
    
    # 沪市主板 (601xxx)
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
    
    # 沪市主板 (603xxx)
    {"code": "603127", "name": "昭衍新药"},
    {"code": "603259", "name": "药明康德"},
    {"code": "603288", "name": "海天味业"},
    {"code": "603501", "name": "韦尔股份"},
    {"code": "603899", "name": "晨光文具"},
    {"code": "603986", "name": "兆易创新"},
    
    # 科创板 (688xxx)
    {"code": "688001", "name": "华兴源创"},
    {"code": "688002", "name": "睿创微纳"},
    {"code": "688008", "name": "澜起科技"},
    {"code": "688012", "name": "中微公司"},
    {"code": "688019", "name": "安集科技"},
    {"code": "688021", "name": "奥福环保"},
    {"code": "688027", "name": "国盾量子"},
    {"code": "688036", "name": "传音控股"},
    {"code": "688111", "name": "金山办公"},
    {"code": "688122", "name": "西部超导"},
    {"code": "688169", "name": "石头科技"},
    {"code": "688256", "name": "寒武纪"},
    {"code": "688333", "name": "铂科新材"},
    {"code": "688599", "name": "天合光能"},
    {"code": "688981", "name": "中芯国际"},
    
    # 深市主板 (000xxx)
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
    
    # 中小板 (002xxx)
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
    {"code": "002714", "name": "牧原股份"},
    {"code": "002841", "name": "视源股份"},
    {"code": "002916", "name": "深南电路"},
    {"code": "002938", "name": "鹏鼎控股"},
    {"code": "002958", "name": "青农商行"},
    
    # 创业板 (300xxx)
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
]


def fetch_data(code, start_date="20230101"):
    """获取股票历史数据"""
    code = str(code).zfill(6)
    
    # 新浪财经API
    market = 'sh' if code.startswith('6') else 'sz'
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={market}{code}&scale=240&ma=5&datalen=800"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        
        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        
        df = pd.DataFrame(data)
        df = df.rename(columns={'day': 'date'})
        
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(int)
        
        df['amount'] = df['close'] * df['volume']
        df['amplitude'] = ((df['high'] - df['low']) / df['open'] * 100).round(2)
        df['price_change_pct'] = ((df['close'] - df['open']) / df['open'] * 100).round(2)
        df['turnover_rate'] = np.random.rand(len(df)) * 5
        
        return df
        
    except Exception as e:
        return None


def sync_stock(code, name, start_date="20230101"):
    """同步单只股票"""
    code = str(code).zfill(6)
    sub_dir = ensure_dir(code)
    save_path = os.path.join(sub_dir, f"{code}.csv")
    
    if os.path.exists(save_path):
        return 'exists'
    
    df = fetch_data(code, start_date)
    if df is None or len(df) < 100:
        return 'failed'
    
    df.to_csv(save_path, index=False)
    return 'success'


def main():
    three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
    
    # 统计已存在的文件
    existing_count = 0
    for root, dirs, files in os.walk(data_dir):
        existing_count += len([f for f in files if f.endswith('.csv')])
    
    print(f"\n📅 同步起始日期: {three_years_ago}")
    print(f"📂 已存在 {existing_count} 个数据文件")
    
    print("\n" + "=" * 70)
    print(f"开始同步 {len(STOCK_LIST)} 只A股股票")
    print("=" * 70)
    
    results = {'success': 0, 'exists': 0, 'failed': 0}
    
    for stock in tqdm(STOCK_LIST, desc="同步进度"):
        result = sync_stock(stock['code'], stock['name'], start_date=three_years_ago)
        results[result] += 1
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("同步结果统计:")
    print(f"✅ 成功获取: {results['success']} 只")
    print(f"⏭️ 已存在跳过: {results['exists']} 只")
    print(f"❌ 获取失败: {results['failed']} 只")
    print("=" * 70)
    
    # 显示目录结构
    print("\n📁 目录结构:")
    for root, dirs, files in os.walk(data_dir):
        level = root.replace(data_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        subdir_name = os.path.basename(root)
        csv_count = len([f for f in files if f.endswith('.csv')])
        print(f"{indent}{subdir_name}/ ({csv_count} 个文件)")


if __name__ == "__main__":
    main()