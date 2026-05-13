import sqlite3
import os
from datetime import datetime
from typing import Dict, List

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_DIR, "storage", "sqlite", "signals.db")


class LeaderScanner:
    """龙头识别扫描器 - 负责识别总龙头、板块龙头、补涨龙并保存到数据库"""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def save_leader(self, code: str, name: str = "", leader_score: float = 0.0, 
                    leader_type: str = "强势股", sector: str = "", rank: int = 0):
        """
        保存龙头信息到数据库
        
        Args:
            code: 股票代码
            name: 股票名称
            leader_score: 龙头评分 (0-1)
            leader_type: 龙头类型 (总龙头/板块龙头/补涨龙/强势股)
            sector: 所属板块
            rank: 排名
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO leaders (
                code,
                name,
                leader_score,
                leader_type,
                sector,
                rank,
                date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            name,
            leader_score,
            leader_type,
            sector,
            rank,
            datetime.today().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        print(f"🐉 {code} [{name}] 龙头信息写入完成")

    def scan_leaders(self, stock_codes: List[str]) -> List[Dict]:
        """
        扫描龙头股
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            龙头股列表
        """
        leaders = []
        
        for i, code in enumerate(stock_codes[:20], 1):  # 取前20只作为龙头候选
            # 模拟龙头评分（基于排名）
            leader_score = 1.0 - (i * 0.03)
            
            # 确定龙头类型
            if i == 1:
                leader_type = "总龙头"
                sector = "市场主线"
            elif i <= 5:
                leader_type = "板块龙头"
                sector = ["AI", "半导体", "新能源", "消费", "金融"][(i-2) % 5]
            elif i <= 10:
                leader_type = "补涨龙"
                sector = ["AI", "半导体", "新能源", "消费", "金融"][(i-6) % 5]
            else:
                leader_type = "强势股"
                sector = "其他"
            
            leader = {
                "code": code,
                "name": f"股票{i}",
                "leader_score": round(leader_score, 2),
                "leader_type": leader_type,
                "sector": sector,
                "rank": i
            }
            
            self.save_leader(**leader)
            leaders.append(leader)
        
        return leaders

    def get_leaders_by_type(self, leader_type: str = None) -> List[Dict]:
        """获取指定类型的龙头股"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if leader_type:
            cursor.execute("""
                SELECT * FROM leaders 
                WHERE leader_type = ? 
                ORDER BY rank, created_at DESC
            """, (leader_type,))
        else:
            cursor.execute("""
                SELECT * FROM leaders 
                ORDER BY rank, created_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "leader_score": row[3],
            "leader_type": row[4],
            "sector": row[5],
            "rank": row[6],
            "date": row[7],
            "created_at": row[8]
        } for row in rows]

    def get_today_leaders(self) -> List[Dict]:
        """获取今日龙头股"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM leaders 
            WHERE date = ? 
            ORDER BY rank
        """, (datetime.today().strftime("%Y-%m-%d"),))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "leader_score": row[3],
            "leader_type": row[4],
            "sector": row[5],
            "rank": row[6],
            "date": row[7],
            "created_at": row[8]
        } for row in rows]


if __name__ == "__main__":
    scanner = LeaderScanner()
    scanner.scan_leaders(["000001", "000002", "600519", "000858", "300750", "601318"])