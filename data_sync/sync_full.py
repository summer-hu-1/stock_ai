#!/usr/bin/env python3
"""
全量同步A股日线数据

使用 DataSyncManager 统一管理
默认从 2023-01-13 开始同步

运行:
    python sync_full.py              # 全量同步所有股票
    python sync_full.py --code 000001  # 单只股票全量同步
    python sync_full.py --start-date 20230101  # 指定起点日期
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_sync.data_sync_manager import DataSyncManager, DEFAULT_START_DATE

def main():
    import argparse
    parser = argparse.ArgumentParser(description='全量同步A股日线数据')
    parser.add_argument('--code', type=str, help='股票代码（可选，单只股票）')
    parser.add_argument('--start-date', type=str, default=DEFAULT_START_DATE,
                        help=f'数据起点日期，默认 {DEFAULT_START_DATE}')
    args = parser.parse_args()

    manager = DataSyncManager(start_date=args.start_date)

    if args.code:
        code = str(args.code).zfill(6)
        success, msg, count = manager.sync_stock_full(code)
        print(f"{'✅' if success else '❌'} {code}: {msg}")
    else:
        manager.sync_all_full()

if __name__ == "__main__":
    main()
