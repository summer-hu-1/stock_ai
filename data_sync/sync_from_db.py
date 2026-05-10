#!/usr/bin/env python3
"""
快速同步本地数据库中的股票日线数据

运行: python data_sync/sync_from_db.py
"""

import akshare as ak
import pandas as pd
import os
import time
import sqlite3

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
data_dir = os.path.join(project_dir, "data", "cn", "daily")
db_path = os.path.join(project_dir, "data", "stocks_cn.db")

os.makedirs(data_dir, exist_ok=True)

# 列名映射
COLUMN_MAPPING = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "price_change_pct",
    "换手率": "turnover_rate"
}

KEEP_COLUMNS = [
    "date", "open", "high", "low", "close",
    "volume", "amount", "amplitude", "price_change_pct", "turnover_rate"
]


def sync_stock(code, start_date="20230101", max_retries=3):
    """
    同步单只股票的日线数据
    """
    save_path = f"{data_dir}/{code}.csv"

    # 如果文件已存在，跳过
    if os.path.exists(save_path):
        print(f"⏭️  {code}: 已存在，跳过")
        return True

    for attempt in range(max_retries):
        try:
            # 禁用代理
            os.environ['HTTP_PROXY'] = ''
            os.environ['HTTPS_PROXY'] = ''
            os.environ['http_proxy'] = ''
            os.environ['https_proxy'] = ''

            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                adjust="qfq"
            )

            if df is None or df.empty:
                print(f"❌ {code}: 无数据")
                return False

            # 重命名列
            df = df.rename(columns=COLUMN_MAPPING)

            # 只保留需要的列
            available_cols = [col for col in KEEP_COLUMNS if col in df.columns]
            df = df[available_cols]

            # 保存
            df.to_csv(save_path, index=False)
            print(f"✅ {code}: 同步成功 ({len(df)} 条记录)")
            return True

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print(f"❌ {code} 失败: {e}")
                return False

    return False


def main():
    # 从数据库获取股票列表
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM stocks')
        stocks = [str(row[0]).zfill(6) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"❌ 读取数据库失败: {e}")
        return

    print("=" * 50)
    print(f"开始同步A股日线数据，共 {len(stocks)} 只股票")
    print(f"数据保存目录: {data_dir}")
    print("=" * 50)

    success = 0
    failed = []

    for i, code in enumerate(stocks, 1):
        print(f"[{i}/{len(stocks)}] ", end="")
        ok = sync_stock(code)
        if ok:
            success += 1
        else:
            failed.append(code)

        # 避免请求过快
        time.sleep(0.2)

    print("\n" + "=" * 50)
    print(f"✅ 同步完成: {success} 只股票")
    if failed:
        print(f"❌ 失败: {len(failed)} 只股票")
        print(f"失败股票: {failed[:10]}..." if len(failed) > 10 else f"失败股票: {failed}")
    print("=" * 50)


if __name__ == "__main__":
    main()
