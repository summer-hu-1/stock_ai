#!/usr/bin/env python3
"""测试数据库路径"""

import os
import sys

current_file_path = os.path.abspath(__file__)
print(f"当前文件路径: {current_file_path}")

script_dir = os.path.dirname(current_file_path)
print(f"脚本目录: {script_dir}")

project_dir = os.path.dirname(script_dir)
print(f"项目目录: {project_dir}")

db_path = os.path.join(project_dir, 'stock_history.db')
print(f"数据库路径: {db_path}")
print(f"文件存在: {os.path.exists(db_path)}")

# 测试连接数据库
import sqlite3
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\n数据库中的表: {[t[0] for t in tables]}")
    
    cursor.execute("SELECT COUNT(*) FROM market_sentiment")
    count = cursor.fetchone()[0]
    print(f"market_sentiment 表记录数: {count}")
    
    cursor.execute("SELECT COUNT(*) FROM market_snapshots")
    count = cursor.fetchone()[0]
    print(f"market_snapshots 表记录数: {count}")
    
    conn.close()
except Exception as e:
    print(f"错误: {e}")
