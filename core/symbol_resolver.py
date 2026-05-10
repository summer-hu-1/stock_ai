"""
股票解析器
负责将股票名称/代码转换为标准股票代码

核心功能：
1. 根据名称模糊搜索股票
2. 将名称解析为标准代码
3. 支持多市场查询
"""

import sqlite3
import os
from typing import List, Dict, Optional


class SymbolResolver:
    """
    股票符号解析器
    支持名称搜索和代码解析
    """

    def __init__(self, market_config: Dict):
        """
        初始化解析器
        
        Args:
            market_config: 市场配置字典，包含 db 字段
        """
        self.market_config = market_config
        self.db_path = self._get_db_path()
        self._ensure_db()

    def _get_db_path(self) -> str:
        """获取数据库文件路径"""
        db_dir = os.path.join(os.path.dirname(__file__), "../data")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, self.market_config["db"])

    def _ensure_db(self):
        """确保数据库和表存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建股票表
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
        
        conn.commit()
        conn.close()

    def search(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        根据名称或代码模糊搜索股票
        
        Args:
            keyword: 搜索关键词（名称或代码）
            limit: 返回结果数量限制
            
        Returns:
            股票列表，包含 code 和 name
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 支持中英文名称搜索
        cursor.execute("""
            SELECT code, name, name_en, sector
            FROM stocks
            WHERE name LIKE ? OR code LIKE ? OR name_en LIKE ?
            ORDER BY name
            LIMIT ?
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "code": row[0],
                "name": row[1],
                "name_en": row[2],
                "sector": row[3]
            })
        
        conn.close()
        return results

    def resolve(self, name_or_code: str) -> Optional[Dict]:
        """
        将名称或代码解析为标准股票信息
        
        Args:
            name_or_code: 股票名称或代码
            
        Returns:
            股票信息字典（code, name），未找到返回 None
        """
        results = self.search(name_or_code, limit=5)
        
        if not results:
            return None
        
        # 优先匹配完全一致的代码
        for result in results:
            if result["code"].upper() == name_or_code.upper():
                return result
        
        # 返回第一个结果
        return results[0]

    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        """
        根据代码精确查询股票
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息字典，未找到返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT code, name, name_en, sector, industry
            FROM stocks
            WHERE code = ?
        """, (code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "code": row[0],
                "name": row[1],
                "name_en": row[2],
                "sector": row[3],
                "industry": row[4]
            }
        
        return None

    def add_stock(self, code: str, name: str, name_en: str = None, sector: str = None, industry: str = None):
        """
        添加股票到数据库
        
        Args:
            code: 股票代码
            name: 中文名称
            name_en: 英文名称
            sector: 所属板块
            industry: 所属行业
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO stocks (code, name, name_en, market, sector, industry)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, name, name_en, self.market_config["code"], sector, industry))
        
        conn.commit()
        conn.close()

    def bulk_add_stocks(self, stocks: List[Dict]):
        """
        批量添加股票
        
        Args:
            stocks: 股票列表，每个元素包含 code, name
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for stock in stocks:
            cursor.execute("""
                INSERT OR REPLACE INTO stocks (code, name, name_en, market, sector, industry)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                stock["code"],
                stock.get("name", ""),
                stock.get("name_en"),
                self.market_config["code"],
                stock.get("sector"),
                stock.get("industry")
            ))
        
        conn.commit()
        conn.close()

    def get_all_stocks(self) -> List[Dict]:
        """获取所有股票，按代码排序"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT code, name, sector FROM stocks ORDER BY code")
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "code": row[0],
                "name": row[1],
                "sector": row[2]
            })
        
        conn.close()
        return results
