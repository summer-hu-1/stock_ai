#!/usr/bin/env python3
"""
增量更新A股日线数据

使用 DataSyncManager 统一管理
只更新已有文件的股票，从最新日期到今天

运行:
    python update_cn_daily.py                    # 增量更新所有已有文件
    python update_cn_daily.py --code 000001      # 单只股票增量更新
    python update_cn_daily.py --target-date 2026-05-10  # 指定目标日期
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_sync.data_sync_manager import DataSyncManager

def main():
    import argparse
    parser = argparse.ArgumentParser(description='增量更新A股日线数据')
    parser.add_argument('--code', type=str, help='股票代码（可选，单只股票）')
    parser.add_argument('--target-date', type=str, help='目标日期 YYYY-MM-DD，默认今天')
    args = parser.parse_args()

    manager = DataSyncManager()

    if args.code:
        code = str(args.code).zfill(6)
        success, msg, count = manager.update_stock_incremental(code, args.target_date)
        print(f"{'✅' if success else '❌'} {code}: {msg}")
    else:
        manager.update_all_incremental()

if __name__ == "__main__":
    main()
