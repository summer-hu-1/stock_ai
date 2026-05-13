import sqlite3
import os
from datetime import datetime
from typing import Dict, List

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_DIR, "storage", "sqlite", "signals.db")


class SectorStrength:
    """板块强度分析器 - 识别主线板块和轮动趋势"""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def save_sector_strength(self, sector: str, strength: float = 0.0, 
                            trend: str = "up", stocks_count: int = 0,
                            avg_score: float = 0.0, description: str = ""):
        """
        保存板块强度信息到数据库
        
        Args:
            sector: 板块名称
            strength: 板块强度 (0-1)
            trend: 趋势方向 (up/down/sideways)
            stocks_count: 板块内股票数量
            avg_score: 平均评分
            description: 板块描述
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sector_strength (
                sector,
                strength,
                trend,
                stocks_count,
                avg_score,
                description,
                date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sector,
            strength,
            trend,
            stocks_count,
            avg_score,
            description,
            datetime.today().strftime("%Y-%m-%d"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        print(f"📈 {sector} 板块强度写入完成")

    def analyze_sectors(self) -> List[Dict]:
        """
        分析板块强度
        
        Returns:
            板块强度列表
        """
        # 预设板块列表
        sectors = [
            {"name": "AI", "description": "人工智能、大模型、算力"},
            {"name": "半导体", "description": "芯片设计、制造、设备"},
            {"name": "新能源", "description": "光伏、锂电、储能"},
            {"name": "消费", "description": "白酒、食品饮料、家电"},
            {"name": "金融", "description": "银行、券商、保险"},
            {"name": "医药", "description": "创新药、医疗器械"},
            {"name": "军工", "description": "国防军工、航天"},
            {"name": "周期", "description": "有色、化工、煤炭"},
        ]

        results = []
        for i, sector_info in enumerate(sectors):
            # 模拟强度计算
            base_strength = 0.5 + (i % 5) * 0.1
            strength = round(min(1.0, base_strength + (datetime.now().hour % 3) * 0.05), 2)
            
            # 确定趋势
            if strength >= 0.75:
                trend = "up"
            elif strength <= 0.45:
                trend = "down"
            else:
                trend = "sideways"
            
            sector_data = {
                "sector": sector_info["name"],
                "strength": strength,
                "trend": trend,
                "stocks_count": 50 + i * 10,
                "avg_score": round(strength * 80 + 20, 1),
                "description": sector_info["description"]
            }
            
            self.save_sector_strength(**sector_data)
            results.append(sector_data)

        print(f"✅ 板块强度分析完成，共 {len(results)} 个板块")
        return results

    def get_main_sectors(self, threshold: float = 0.7) -> List[Dict]:
        """获取主线板块（强度高于阈值）"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sector_strength 
            WHERE strength >= ? AND date = ?
            ORDER BY strength DESC
        """, (threshold, datetime.today().strftime("%Y-%m-%d")))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "sector": row[1],
            "strength": row[2],
            "trend": row[3],
            "stocks_count": row[4],
            "avg_score": row[5],
            "description": row[6],
            "date": row[7],
            "created_at": row[8]
        } for row in rows]

    def get_sector_rotation(self) -> List[Dict]:
        """获取板块轮动趋势"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sector, AVG(strength) as avg_strength, MAX(strength) as max_strength
            FROM sector_strength
            WHERE date >= date('now', '-7 days')
            GROUP BY sector
            ORDER BY avg_strength DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [{
            "sector": row[0],
            "avg_strength": round(row[1], 2),
            "max_strength": round(row[2], 2)
        } for row in rows]

    def get_market_state(self) -> Dict:
        """获取市场状态摘要"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 获取今日板块强度
        cursor.execute("""
            SELECT AVG(strength) as avg_strength, COUNT(*) as sector_count
            FROM sector_strength
            WHERE date = ?
        """, (datetime.today().strftime("%Y-%m-%d"),))

        row = cursor.fetchone()
        avg_strength = round(row[0], 2) if row and row[0] else 0.5
        sector_count = row[1] if row else 0

        # 获取主线板块数量
        cursor.execute("""
            SELECT COUNT(*) FROM sector_strength
            WHERE date = ? AND strength >= 0.7
        """, (datetime.today().strftime("%Y-%m-%d"),))

        main_sector_count = cursor.fetchone()[0]

        conn.close()

        # 确定市场状态
        if avg_strength >= 0.7:
            market_state = "牛市"
            emoji = "🐂"
        elif avg_strength >= 0.5:
            market_state = "震荡市"
            emoji = "📊"
        else:
            market_state = "熊市"
            emoji = "🐻"

        return {
            "market_state": market_state,
            "emoji": emoji,
            "avg_sector_strength": avg_strength,
            "total_sectors": sector_count,
            "main_sectors": main_sector_count,
            "rotation_active": main_sector_count >= 2,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


if __name__ == "__main__":
    analyzer = SectorStrength()
    analyzer.analyze_sectors()
    print("\n主线板块:")
    for sector in analyzer.get_main_sectors():
        print(f"  {sector['sector']}: {sector['strength']}")
    print("\n市场状态:")
    print(analyzer.get_market_state())