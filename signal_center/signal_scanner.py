import sqlite3
import os
from datetime import datetime
from typing import Dict, List

# 获取项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_DIR, "storage", "sqlite", "signals.db")


class SignalScanner:
    """信号扫描器 - 负责扫描股票并保存信号到数据库"""

    def __init__(self):
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def save_signal(self, code: str, name: str = "", signal_type: str = "breakout", 
                    direction: str = "up", strength: float = 0.88):
        """
        保存信号到数据库
        
        Args:
            code: 股票代码
            name: 股票名称
            signal_type: 信号类型
            direction: 方向 (up/down/neutral)
            strength: 强度 (0-1)
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO signals (
                code,
                name,
                signal_type,
                direction,
                strength,
                date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            name,
            signal_type,
            direction,
            strength,
            datetime.today().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        print(f"✅ {code} [{name}] 信号写入完成")

    def save_leader(self, code: str, name: str = "", leader_score: float = 0.0, 
                    leader_type: str = "强势股", sector: str = ""):
        """保存龙头信息到数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO leaders (
                code,
                name,
                leader_score,
                leader_type,
                sector,
                date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            name,
            leader_score,
            leader_type,
            sector,
            datetime.today().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        print(f"🐉 {code} [{name}] 龙头信息写入完成")

    def get_signals_by_code(self, code: str) -> List[Dict]:
        """获取指定股票的信号"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM signals 
            WHERE code = ? 
            ORDER BY date DESC, created_at DESC
        """, (code,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "signal_type": row[3],
            "direction": row[4],
            "strength": row[5],
            "date": row[6],
            "created_at": row[7]
        } for row in rows]

    def get_today_signals(self) -> List[Dict]:
        """获取今日信号"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM signals 
            WHERE date = ? 
            ORDER BY strength DESC
        """, (datetime.today().strftime("%Y-%m-%d"),))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "signal_type": row[3],
            "direction": row[4],
            "strength": row[5],
            "date": row[6],
            "created_at": row[7]
        } for row in rows]


if __name__ == "__main__":
    scanner = SignalScanner()
    scanner.save_signal("000001", "平安银行")
    scanner.save_signal("000002", "万科A")
    scanner.save_signal("600519", "贵州茅台")