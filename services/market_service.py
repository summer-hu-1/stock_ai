"""市场服务 - 提供市场状态管理功能"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 获取项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_DIR, "storage", "sqlite", "signals.db")


class MarketService:
    """市场服务 - 提供市场状态管理和快照功能"""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_tables()

    def _init_tables(self):
        """初始化市场快照表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sentiment TEXT,
                sentiment_score REAL,
                market_cycle TEXT,
                main_sector TEXT,
                volatility REAL,
                date TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_market_snapshot(self, sentiment: Dict) -> bool:
        """保存市场快照"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO market_snapshots (
                    sentiment,
                    sentiment_score,
                    market_cycle,
                    main_sector,
                    volatility,
                    date,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sentiment.get("sentiment", "neutral"),
                sentiment.get("score", 0.5),
                sentiment.get("market_cycle", "unknown"),
                sentiment.get("main_sector", ""),
                sentiment.get("volatility", 0.0),
                datetime.today().strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存市场快照失败: {e}")
            return False

    def get_recent_snapshots(self, limit: int = 10) -> list:
        """获取最近的市场快照"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM market_snapshots
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "sentiment": row[1],
            "sentiment_score": row[2],
            "market_cycle": row[3],
            "main_sector": row[4],
            "volatility": row[5],
            "date": row[6],
            "created_at": row[7]
        } for row in rows]

    def get_market_cycle(self, days: int = 5) -> Dict:
        """获取市场周期信息"""
        snapshots = self.get_recent_snapshots(limit=days)

        if not snapshots:
            return {
                "cycle": "未知",
                "stage": "无数据",
                "description": "暂无市场周期数据"
            }

        avg_score = sum(s["sentiment_score"] for s in snapshots) / len(snapshots)

        if avg_score >= 0.6:
            cycle = "上升周期"
            stage = "强势"
            description = "市场情绪乐观，趋势向上"
        elif avg_score >= 0.4:
            cycle = "震荡周期"
            stage = "中性"
            description = "市场情绪中性，方向不明"
        else:
            cycle = "下降周期"
            stage = "弱势"
            description = "市场情绪悲观，趋势向下"

        return {
            "cycle": cycle,
            "stage": stage,
            "description": description,
            "avg_score": round(avg_score, 2),
            "snapshot_count": len(snapshots)
        }

    def get_emotion_trend(self, days: int = 5) -> Dict:
        """获取情绪趋势"""
        snapshots = self.get_recent_snapshots(limit=days)

        if not snapshots:
            return {"trend": "无数据", "change": 0}

        scores = [s["sentiment_score"] for s in snapshots]
        if len(scores) >= 2:
            change = scores[0] - scores[-1]
            if change > 0.1:
                trend = "上升"
            elif change < -0.1:
                trend = "下降"
            else:
                trend = "平稳"
        else:
            trend = "平稳"
            change = 0

        return {
            "trend": trend,
            "change": round(change, 2),
            "current_score": scores[0] if scores else 0,
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0
        }

    def get_sector_rotation(self, days: int = 5) -> Dict:
        """获取板块轮动信息"""
        snapshots = self.get_recent_snapshots(limit=days)

        if not snapshots:
            return {"rotation": "无数据", "main_sectors": []}

        sector_counts = {}
        for s in snapshots:
            sector = s.get("main_sector", "")
            if sector:
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

        if sector_counts:
            main_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            main_sectors = [s[0] for s in main_sectors]
        else:
            main_sectors = []

        return {
            "rotation": "正常" if len(main_sectors) > 0 else "无主线",
            "main_sectors": main_sectors,
            "sector_count": len(sector_counts)
        }

    def get_leader_rotation(self, days: int = 5) -> Dict:
        """获取龙头轮动信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT code, name, leader_score, leader_type, sector
            FROM leaders
            ORDER BY created_at DESC
            LIMIT ?
        """, (days * 5,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"rotation": "无数据", "leaders": []}

        leaders = [{
            "code": row[0],
            "name": row[1],
            "score": row[2],
            "type": row[3],
            "sector": row[4]
        } for row in rows]

        return {
            "rotation": "正常",
            "leaders": leaders[:10],
            "count": len(leaders)
        }

    def get_latest_insight(self) -> Dict:
        """获取最新的市场洞察"""
        snapshots = self.get_recent_snapshots(limit=5)
        signals_data = self._get_recent_signals(limit=10)

        if not snapshots:
            return {
                "current_state": "未知",
                "state_description": "暂无足够数据生成洞察",
                "confidence": 0
            }

        latest = snapshots[0]
        avg_score = sum(s["sentiment_score"] for s in snapshots) / len(snapshots)

        if avg_score >= 0.6:
            current_state = "上升趋势"
            state_description = "市场情绪乐观，多头占优，建议关注强势股"
        elif avg_score >= 0.4:
            current_state = "震荡整理"
            state_description = "市场情绪中性，建议观望或轻仓操作"
        else:
            current_state = "下降趋势"
            state_description = "市场情绪悲观，建议控制风险或空仓"

        confidence = min(0.9, 0.5 + len(snapshots) * 0.08)

        if signals_data:
            strong_signals = [s for s in signals_data if s.get("strength", 0) > 0.8]
            if strong_signals:
                state_description += f" 今日有 {len(strong_signals)} 个强势信号。"

        return {
            "current_state": current_state,
            "state_description": state_description,
            "confidence": round(confidence, 2),
            "sentiment_score": latest["sentiment_score"],
            "snapshot_count": len(snapshots)
        }

    def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        """获取最近的市场洞察列表"""
        snapshots = self.get_recent_snapshots(limit=limit)

        insights = []
        for snapshot in snapshots:
            avg_score = snapshot["sentiment_score"]

            if avg_score >= 0.6:
                state = "上升趋势"
                emoji = "📈"
            elif avg_score >= 0.4:
                state = "震荡整理"
                emoji = "➡️"
            else:
                state = "下降趋势"
                emoji = "📉"

            insights.append({
                "date": snapshot.get("date", ""),
                "created_at": snapshot.get("created_at", ""),
                "state": state,
                "emoji": emoji,
                "sentiment_score": snapshot["sentiment_score"],
                "main_sector": snapshot.get("main_sector", "未知")
            })

        return insights

    def _get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """获取最近的信号数据"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT code, name, signal_type, direction, strength, date
            FROM signals
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [{
            "code": row[0],
            "name": row[1],
            "signal_type": row[2],
            "direction": row[3],
            "strength": row[4],
            "date": row[5]
        } for row in rows]


# 全局单例
_market_service_instance = None

def get_market_service() -> MarketService:
    """获取市场服务单例"""
    global _market_service_instance
    if _market_service_instance is None:
        _market_service_instance = MarketService()
    return _market_service_instance