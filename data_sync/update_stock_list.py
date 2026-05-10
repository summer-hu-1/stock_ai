#!/usr/bin/env python3
"""
更新A股股票列表 - 支持主备数据源

功能：
1. 从akshare获取股票列表（主数据源）
2. 如果akshare失败，使用雪球API（备用数据源）
3. 保存到数据库和CSV文件
4. 支持增量更新

运行: python data_sync/update_stock_list.py
"""

import akshare as ak
import pandas as pd
import sqlite3
import os
import time
import requests

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn")
db_path = os.path.join(project_dir, "data", "stocks_cn.db")  # 使用统一的数据库路径

os.makedirs(data_dir, exist_ok=True)


def get_stock_list_from_akshare():
    """
    从akshare获取股票列表（主数据源）
    """
    try:
        print("📡 尝试从akshare获取股票列表...")
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        df = ak.stock_info_a_code_name()
        df.columns = ["code", "name"]
        print(f"✅ akshare成功，获取 {len(df)} 只股票")
        return df
    except Exception as e:
        print(f"❌ akshare失败: {e}")
        return None


def get_stock_list_from_xueqiu():
    """
    从雪球API获取股票列表（备用数据源）
    """
    try:
        print("📡 尝试从雪球API获取股票列表...")
        session = requests.Session()
        session.trust_env = False
        session.proxies = {}

        # 雪球API获取A股列表
        url = "https://stock.xueqiu.com/v5/stock/screener/quote/list.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://xueqiu.com'
        }

        all_stocks = []
        page = 1
        page_size = 100

        while True:
            params = {
                'page': page,
                'size': page_size,
                'order': 'desc',
                'orderby': 'percent',
                'market': 'CN',
                'type': 'sh_sz'
            }

            r = session.get(url, headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                print(f"❌ 雪球API返回错误: {r.status_code}")
                break

            data = r.json()
            stocks = data.get('data', {}).get('list', [])
            if not stocks:
                break

            for stock in stocks:
                all_stocks.append({
                    'code': stock.get('symbol', '').replace('SH', '').replace('SZ', ''),
                    'name': stock.get('name', '')
                })

            # 检查是否还有更多数据
            total = data.get('data', {}).get('count', 0)
            if page * page_size >= total:
                break

            page += 1
            time.sleep(0.1)

        if all_stocks:
            df = pd.DataFrame(all_stocks)
            print(f"✅ 雪球API成功，获取 {len(df)} 只股票")
            return df

        return None
    except Exception as e:
        print(f"❌ 雪球API失败: {e}")
        return None


def save_to_csv(df, path):
    """保存到CSV文件"""
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"💾 已保存到CSV: {path}")


def save_to_db(df, db_path):
    """保存到SQLite数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_en TEXT,
            market TEXT NOT NULL,
            sector TEXT,
            industry TEXT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 清空旧数据
    cursor.execute("DELETE FROM stocks")

    # 插入新数据
    for _, row in df.iterrows():
        code = row['code']
        # 根据代码判断市场
        if code.startswith('6'):
            market = 'SH'
        else:
            market = 'SZ'

        cursor.execute(
            "INSERT INTO stocks (code, name, market) VALUES (?, ?, ?)",
            (code, row['name'], market)
        )

    conn.commit()
    conn.close()
    print(f"💾 已保存到数据库: {db_path}")


def get_existing_codes(db_path):
    """获取数据库中已存在的股票代码"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM stocks')
        codes = {row[0] for row in cursor.fetchall()}
        conn.close()
        return codes
    except:
        return set()


def main():
    print("=" * 60)
    print("🔄 A股股票列表更新工具")
    print("=" * 60)

    # 尝试从akshare获取
    df = get_stock_list_from_akshare()

    # 如果失败，使用雪球API
    if df is None or df.empty:
        print("\n⚠️ akshare不可用，尝试备用数据源...")
        df = get_stock_list_from_xueqiu()

    if df is None or df.empty:
        print("\n❌ 所有数据源都失败了")
        print("💡 建议：检查网络连接，或稍后重试")
        return

    # 数据清洗
    df['code'] = df['code'].astype(str).str.zfill(6)
    df = df.drop_duplicates(subset=['code'], keep='first')
    df = df.sort_values('code')

    print(f"\n📊 共获取 {len(df)} 只股票")

    # 保存到CSV
    csv_path = os.path.join(data_dir, "stock_list.csv")
    save_to_csv(df, csv_path)

    # 保存到数据库
    save_to_db(df, db_path)

    # 显示统计信息
    print("\n📈 股票代码统计:")
    sh_count = len(df[df['code'].str.startswith('6')])
    sz_count = len(df[df['code'].str.startswith(('0', '3'))])
    print(f"   上海交易所: {sh_count} 只")
    print(f"   深圳交易所: {sz_count} 只")

    # 显示前20只股票
    print("\n前20只股票:")
    print(df.head(20).to_string(index=False))

    print("\n" + "=" * 60)
    print("✅ 更新完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
