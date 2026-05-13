import sqlite3
import os
from datetime import datetime
from typing import Dict, List

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_DIR, "storage", "sqlite", "signals.db")


class WatchlistBuilder:
    """关注列表构建器 - 自动构建高强度信号股票列表"""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    def add_to_watchlist(self, code: str, name: str = "", reason: str = "", 
                         priority: int = 1, tags: str = ""):
        """
        添加股票到关注列表
        
        Args:
            code: 股票代码
            name: 股票名称
            reason: 加入理由
            priority: 优先级 (1-5，1最高)
            tags: 标签（逗号分隔）
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO watchlist (
                code,
                name,
                reason,
                priority,
                tags,
                added_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            name,
            reason,
            priority,
            tags,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        print(f"📋 {code} [{name}] 已加入关注列表")

    def remove_from_watchlist(self, code: str):
        """从关注列表移除股票"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM watchlist WHERE code = ?", (code,))
        conn.commit()
        conn.close()

        print(f"🗑️ {code} 已从关注列表移除")

    def build_watchlist_from_signals(self, min_strength: float = 0.85, limit: int = 20):
        """
        从信号自动构建关注列表
        
        Args:
            min_strength: 最小信号强度
            limit: 最大数量
            
        Returns:
            关注列表
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 获取高强度信号
        cursor.execute("""
            SELECT code, name, signal_type, direction, strength 
            FROM signals 
            WHERE strength >= ? AND direction = 'up'
            ORDER BY strength DESC 
            LIMIT ?
        """, (min_strength, limit))

        rows = cursor.fetchall()
        conn.close()

        watchlist = []
        for row in rows:
            code, name, signal_type, direction, strength = row
            reason = f"{signal_type}信号，强度{strength:.2f}"
            priority = 1 if strength >= 0.95 else 2 if strength >= 0.9 else 3
            
            # 先移除旧记录，再添加新记录
            self.remove_from_watchlist(code)
            self.add_to_watchlist(
                code=code,
                name=name if name else f"股票{code}",
                reason=reason,
                priority=priority,
                tags=f"{signal_type},high_strength"
            )
            
            watchlist.append({
                "code": code,
                "name": name if name else f"股票{code}",
                "reason": reason,
                "priority": priority,
                "strength": strength
            })

        print(f"✅ 关注列表构建完成，共 {len(watchlist)} 只股票")
        return watchlist

    def get_watchlist(self, priority: int = None) -> List[Dict]:
        """获取关注列表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if priority:
            cursor.execute("""
                SELECT * FROM watchlist 
                WHERE priority = ?
                ORDER BY priority, added_at DESC
            """, (priority,))
        else:
            cursor.execute("""
                SELECT * FROM watchlist 
                ORDER BY priority, added_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "reason": row[3],
            "priority": row[4],
            "tags": row[5],
            "added_at": row[6],
            "updated_at": row[7]
        } for row in rows]

    def update_watchlist(self, code: str, reason: str = None, priority: int = None):
        """更新关注列表中的股票信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        updates = []
        params = []

        if reason:
            updates.append("reason = ?")
            params.append(reason)
        if priority:
            updates.append("priority = ?")
            params.append(priority)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            params.append(code)

            cursor.execute(f"""
                UPDATE watchlist 
                SET {', '.join(updates)} 
                WHERE code = ?
            """, tuple(params))

            conn.commit()
            print(f"🔄 {code} 关注列表信息已更新")

        conn.close()


if __name__ == "__main__":
    builder = WatchlistBuilder()
    builder.build_watchlist_from_signals(min_strength=0.85)