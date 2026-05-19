import sqlite3
from datetime import datetime, timedelta
import os

DB_NAME = "stock_history.db"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", DB_NAME)


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT,
        stock_name TEXT,
        price REAL,
        change_pct REAL,
        volume REAL,
        turnover REAL,
        amplitude REAL,
        market_mood TEXT,
        ai_summary TEXT,
        mode TEXT,
        username TEXT DEFAULT 'guest',
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_sentiment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        limit_up_count INTEGER,
        limit_down_count INTEGER,
        bomb_rate REAL,
        avg_change REAL,
        market_mood TEXT,
        rising_count INTEGER,
        falling_count INTEGER,
        rise_ratio REAL,
        strong_count INTEGER,
        weak_count INTEGER,
        total_volume REAL,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hot_sectors_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sector_name TEXT,
        change_pct REAL,
        turnover_rate REAL,
        rise_count INTEGER,
        fall_count INTEGER,
        cached_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metadata (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT UNIQUE,
        stock_name TEXT,
        industry TEXT,
        market_cap REAL,
        updated_at TEXT
    )
    """)

    conn.commit()

    cursor.execute("PRAGMA table_info(stock_analysis)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'mode' not in columns:
        cursor.execute("ALTER TABLE stock_analysis ADD COLUMN mode TEXT")
        conn.commit()
        print("✅ 已添加 mode 列到 stock_analysis 表")
    if 'username' not in columns:
        cursor.execute("ALTER TABLE stock_analysis ADD COLUMN username TEXT DEFAULT 'guest'")
        conn.commit()
        print("✅ 已添加 username 列到 stock_analysis 表")

    conn.close()

    cleanup_old_data_if_needed()


def cleanup_old_data_if_needed():
    """按需清理旧数据 - 只在需要时才清理（一周一次）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now()

    try:
        cursor.execute("SELECT value FROM system_metadata WHERE key = 'last_cleanup_date'")
        result = cursor.fetchone()
        last_cleanup_date = result[0] if result else None

        need_cleanup = False
        if not last_cleanup_date:
            need_cleanup = True
            print("🗑️ 首次运行，执行清理")
        else:
            try:
                last_cleanup = datetime.strptime(last_cleanup_date, "%Y-%m-%d")
                days_since = (now - last_cleanup).days
                if days_since >= 7:
                    need_cleanup = True
                    print(f"🗑️ 距离上次清理已 {days_since} 天，执行清理")
            except (ValueError, TypeError):
                need_cleanup = True
                print("🗑️ 上次清理日期格式错误，执行清理")

        if need_cleanup:
            cursor.execute("DELETE FROM market_sentiment WHERE date < ?", (today,))
            cursor.execute("DELETE FROM hot_sectors_cache WHERE cached_at < ?", (today,))

            cursor.execute("""
            INSERT OR REPLACE INTO system_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
            """, ("last_cleanup_date", today, now.strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            print("✅ 清理完成")
        else:
            print("📦 不需要清理，数据较新")

    except Exception as e:
        print(f"清理数据失败: {e}")
    finally:
        conn.close()


def save_analysis(stock_data, ai_result, market_mood="", mode="", username="guest"):
    """保存个股分析记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO stock_analysis (
            stock_code,
            stock_name,
            price,
            change_pct,
            volume,
            turnover,
            amplitude,
            market_mood,
            ai_summary,
            mode,
            username,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock_data["code"],
            stock_data["name"],
            stock_data["price"],
            stock_data["price_change_pct"],
            stock_data["volume"],
            stock_data["turnover_rate"],
            stock_data["amplitude"],
            market_mood,
            ai_result,
            mode,
            username,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()
        print(f"✅ 分析记录已保存: {stock_data['name']}({stock_data['code']}) [用户: {username}]")
        return True
    except Exception as e:
        print(f"❌ 保存分析记录失败: {e}")
        return False


def save_market_sentiment(sentiment_data):
    """保存市场情绪记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        cursor.execute("""
        INSERT OR REPLACE INTO market_sentiment (
            date,
            limit_up_count,
            limit_down_count,
            bomb_rate,
            avg_change,
            market_mood,
            rising_count,
            falling_count,
            rise_ratio,
            strong_count,
            weak_count,
            total_volume,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            today,
            sentiment_data["limit_up_count"],
            sentiment_data["limit_down_count"],
            sentiment_data["bomb_rate"],
            sentiment_data["avg_change"],
            sentiment_data["market_mood"],
            sentiment_data["rising_count"],
            sentiment_data["falling_count"],
            sentiment_data["rise_ratio"],
            sentiment_data["strong_count"],
            sentiment_data["weak_count"],
            sentiment_data["total_volume"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
    except Exception as e:
        print(f"保存市场情绪失败: {e}")
    finally:
        conn.close()


def get_cached_market_sentiment():
    """获取当天的缓存市场情绪数据"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT date, limit_up_count, limit_down_count, bomb_rate, avg_change,
           market_mood, rising_count, falling_count, rise_ratio,
           strong_count, weak_count, total_volume, created_at
    FROM market_sentiment
    WHERE date = ?
    ORDER BY created_at DESC
    LIMIT 1
    """, (today,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "date": row[0],
            "limit_up_count": row[1],
            "limit_down_count": row[2],
            "bomb_rate": row[3],
            "avg_change": row[4],
            "market_mood": row[5],
            "rising_count": row[6],
            "falling_count": row[7],
            "rise_ratio": row[8],
            "strong_count": row[9],
            "weak_count": row[10],
            "total_volume": row[11],
            "created_at": row[12]
        }
    return None


def save_hot_sectors_cache(hot_sectors):
    """保存热门板块到缓存"""
    if not hot_sectors:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM hot_sectors_cache WHERE cached_at < ?", (today,))

        for sector in hot_sectors:
            cursor.execute("""
            INSERT INTO hot_sectors_cache (
                sector_name, change_pct, turnover_rate, rise_count, fall_count, cached_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sector.get("name", ""),
                sector.get("change_pct", 0),
                sector.get("turnover_rate", 0),
                sector.get("rise_count", 0),
                sector.get("fall_count", 0),
                today
            ))

        conn.commit()
        print(f"✅ 热门板块缓存已更新: {len(hot_sectors)} 个板块")
    except Exception as e:
        print(f"保存热门板块缓存失败: {e}")
    finally:
        conn.close()


def get_cached_hot_sectors():
    """获取缓存的热门板块数据"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT sector_name, change_pct, turnover_rate, rise_count, fall_count
    FROM hot_sectors_cache
    WHERE cached_at = ?
    ORDER BY change_pct DESC
    LIMIT 15
    """, (today,))

    rows = cursor.fetchall()
    conn.close()

    if rows:
        return [
            {
                "name": row[0],
                "change_pct": row[1],
                "turnover_rate": row[2],
                "rise_count": row[3],
                "fall_count": row[4]
            }
            for row in rows
        ]
    return None


def get_stock_history(stock_code, limit=20, username=None):
    """获取股票历史分析记录，可按用户过滤"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if username:
        cursor.execute("""
        SELECT id, stock_code, stock_name, price, change_pct, volume, turnover, 
               amplitude, market_mood, ai_summary, mode, created_at
        FROM stock_analysis
        WHERE stock_code = ? AND username = ?
        ORDER BY created_at DESC
        LIMIT ?
        """, (stock_code, username, limit))
    else:
        cursor.execute("""
        SELECT id, stock_code, stock_name, price, change_pct, volume, turnover, 
               amplitude, market_mood, ai_summary, mode, created_at
        FROM stock_analysis
        WHERE stock_code = ?
        ORDER BY created_at DESC
        LIMIT ?
        """, (stock_code, limit))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "stock_code": row[1],
            "stock_name": row[2],
            "price": row[3],
            "change_pct": row[4],
            "volume": row[5],
            "turnover": row[6],
            "amplitude": row[7],
            "market_mood": row[8],
            "ai_summary": row[9],
            "mode": row[10],
            "created_at": row[11]
        })

    return result


def get_market_sentiment_history(limit=30):
    """获取市场情绪历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT date, limit_up_count, limit_down_count, bomb_rate, avg_change, 
           market_mood, rising_count, falling_count, rise_ratio, 
           strong_count, weak_count, total_volume, created_at
    FROM market_sentiment
    ORDER BY date DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "date": row[0],
            "limit_up_count": row[1],
            "limit_down_count": row[2],
            "bomb_rate": row[3],
            "avg_change": row[4],
            "market_mood": row[5],
            "rising_count": row[6],
            "falling_count": row[7],
            "rise_ratio": row[8],
            "strong_count": row[9],
            "weak_count": row[10],
            "total_volume": row[11],
            "created_at": row[12]
        })

    return result


def get_all_stocks(username=None):
    """获取所有分析过的股票，可按用户过滤"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if username:
        cursor.execute("""
        SELECT DISTINCT stock_code, stock_name
        FROM stock_analysis
        WHERE username = ?
        ORDER BY stock_code
        """, (username,))
    else:
        cursor.execute("""
        SELECT DISTINCT stock_code, stock_name
        FROM stock_analysis
        ORDER BY stock_code
        """)

    rows = cursor.fetchall()
    conn.close()

    return [{"code": row[0], "name": row[1]} for row in rows]


def format_history_for_display(history):
    """格式化历史记录用于显示"""
    if not history:
        return []

    formatted = []
    for h in history:
        formatted.append({
            "时间": h["created_at"],
            "股票": f"{h['stock_name']}({h['stock_code']})",
            "价格": f"{h['price']:.2f}",
            "涨跌": f"{h['change_pct']:.2f}%",
            "成交额": f"{h['volume']/1e8:.2f}亿",
            "换手率": f"{h['turnover']:.2f}%",
            "市场情绪": h["market_mood"]
        })

    return formatted


def delete_stock_history(record_id):
    """删除指定的股票分析历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM stock_analysis
    WHERE id = ?
    """, (record_id,))

    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()

    return deleted_rows > 0


def get_all_companies(market: str = "cn"):
    """获取所有公司信息，可按市场筛选
    
    Args:
        market: 市场代码，cn=A股，hk=港股，us=美股
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if market == "hk":
        conn.close()
        return []
    elif market == "us":
        conn.close()
        return []
    
    cursor.execute("""
    SELECT stock_code, stock_name, industry
    FROM company_info
    ORDER BY stock_code
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{"code": row[0], "name": row[1], "industry": row[2]} for row in rows]


def save_company_info(companies):
    """批量保存公司信息"""
    if not companies:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for company in companies:
        cursor.execute("""
        INSERT OR REPLACE INTO company_info (stock_code, stock_name, industry, updated_at)
        VALUES (?, ?, ?, ?)
        """, (
            company.get("code", ""),
            company.get("name", ""),
            company.get("industry", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()
    print(f"✅ 已保存 {len(companies)} 条公司信息")
    return True


def get_company_by_code(stock_code):
    """根据代码获取公司信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT stock_code, stock_name
    FROM company_info
    WHERE stock_code = ?
    """, (stock_code,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {"code": row[0], "name": row[1]}
    return None
