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

    def bulk_add_stocks(self, stocks: List[Dict], incremental=True):
        """
        批量添加股票，支持增量更新

        Args:
            stocks: 股票列表，每个元素包含 code, name
            incremental: True=增量更新（只添加新股票），False=全量替换
        """
        if not stocks:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if incremental:
            # 增量更新：只插入不存在的股票
            added_count = 0
            for stock in stocks:
                # 检查股票是否已存在
                cursor.execute("SELECT code FROM stocks WHERE code = ?", (stock["code"],))
                exists = cursor.fetchone()

                if not exists:
                    cursor.execute("""
                        INSERT INTO stocks (code, name, name_en, market, sector, industry)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        stock["code"],
                        stock.get("name", ""),
                        stock.get("name_en"),
                        self.market_config["code"],
                        stock.get("sector"),
                        stock.get("industry")
                    ))
                    added_count += 1

            conn.commit()
            conn.close()

            # 清除缓存
            if hasattr(self, '_stocks_cache'):
                del self._stocks_cache

            return added_count
        else:
            # 全量替换：删除旧数据，插入新数据
            cursor.execute("DELETE FROM stocks WHERE market = ?", (self.market_config["code"],))

            for stock in stocks:
                cursor.execute("""
                    INSERT INTO stocks (code, name, name_en, market, sector, industry)
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

            # 清除缓存
            if hasattr(self, '_stocks_cache'):
                del self._stocks_cache

            return len(stocks)

    def get_all_stocks(self, use_cache=True) -> List[Dict]:
        """获取所有股票，按代码排序，优先使用本地缓存"""
        # 如果启用缓存且已有数据，直接返回
        if use_cache and hasattr(self, '_stocks_cache') and self._stocks_cache:
            return self._stocks_cache

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

        # 缓存结果
        self._stocks_cache = results
        return results

    def get_stock_count(self) -> int:
        """获取本地数据库中的股票数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """搜索股票（支持中文名称、代码）"""
        if not keyword:
            return self.get_all_stocks()[:limit]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 清理关键词，只保留数字、字母和中文
        import re
        clean_keyword = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]', '', keyword)

        # 优先精确匹配代码
        cursor.execute("""
            SELECT code, name, sector FROM stocks
            WHERE code = ?
            LIMIT 1
        """, (clean_keyword,))
        exact_match = cursor.fetchone()
        if exact_match:
            conn.close()
            return [{
                "code": exact_match[0],
                "name": exact_match[1],
                "sector": exact_match[2]
            }]

        # 模糊搜索 - 处理中文名称中的特殊字符
        # 将关键词分割成单个中文字符
        chinese_chars = [c for c in clean_keyword if re.search(r'[\u4e00-\u9fff]', c)]

        # 构建搜索条件：代码匹配 或 名称包含所有中文字符
        code_pattern = f'%{clean_keyword}%'

        if chinese_chars:
            name_conditions = ' OR '.join([f"name LIKE ?" for _ in chinese_chars])
            name_patterns = [f'%{c}%' for c in chinese_chars]
            cursor.execute(f"""
                SELECT code, name, sector FROM stocks
                WHERE code LIKE ? OR ({name_conditions})
                ORDER BY
                    CASE WHEN code = ? THEN 0
                         WHEN code LIKE ? THEN 1
                         ELSE 2 END,
                    code
                LIMIT ?
            """, (code_pattern,) + tuple(name_patterns) + (clean_keyword, clean_keyword+'%', limit))
        else:
            cursor.execute("""
                SELECT code, name, sector FROM stocks
                WHERE code LIKE ?
                ORDER BY
                    CASE WHEN code = ? THEN 0
                         WHEN code LIKE ? THEN 1
                         ELSE 2 END,
                    code
                LIMIT ?
            """, (code_pattern, clean_keyword, clean_keyword+'%', limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "code": row[0],
                "name": row[1],
                "sector": row[2]
            })

        conn.close()
        return results
