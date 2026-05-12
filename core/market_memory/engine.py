from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
import os
from .models import MarketSnapshot, MarketTrend, MarketInsight


class MarketStateEngine:
    """
    市场状态引擎 - 核心大脑
    
    功能：
    1. 分析市场周期（冰点→修复→高潮→分歧→退潮）
    2. 分析情绪趋势
    3. 分析板块轮动
    4. 分析龙头切换
    5. 分析风险变化
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "stock_history.db")
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 市场快照表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            timestamp TEXT,
            market_sentiment TEXT,
            emotion_score REAL,
            limit_up_count INTEGER,
            limit_down_count INTEGER,
            highest_board INTEGER,
            rising_count INTEGER,
            falling_count INTEGER,
            flat_count INTEGER,
            rise_ratio REAL,
            total_volume REAL,
            volume_trend TEXT,
            north_money REAL,
            north_money_trend TEXT,
            bomb_rate REAL,
            risk_level TEXT,
            top_sectors TEXT,
            hot_theme TEXT,
            leaders TEXT,
            dragon_rotation INTEGER,
            rotation_from TEXT,
            rotation_to TEXT,
            market_cycle TEXT,
            cycle_stage TEXT,
            index_change TEXT,
            raw_data TEXT,
            created_at TEXT
        )
        """)
        
        # 市场洞察表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            timestamp TEXT,
            current_state TEXT,
            state_description TEXT,
            trend_analysis TEXT,
            risk_alert TEXT,
            opportunity TEXT,
            action_suggestion TEXT,
            key_changes TEXT,
            confidence REAL,
            created_at TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def analyze_market_cycle(self, snapshots: List[MarketSnapshot]) -> Dict:
        """
        分析市场周期
        
        周期阶段：
        - 冰点期：涨停<20家，情绪得分<30
        - 修复期：涨停20-50家，情绪得分30-60
        - 主升期：涨停50-80家，情绪得分60-80
        - 分歧期：涨停80-100家，情绪得分80-90，但炸板率高
        - 高潮期：涨停>100家，情绪得分>90
        - 退潮期：涨停家数下降，炸板率上升
        """
        if not snapshots:
            return {"cycle": "未知", "stage": "未知", "description": "数据不足"}
        
        latest = snapshots[0]
        limit_up = latest.limit_up_count
        emotion = latest.emotion_score
        bomb_rate = latest.bomb_rate
        
        # 判断周期阶段
        if limit_up < 20 or emotion < 30:
            cycle = "冰点期"
            stage = "晚期" if limit_up < 10 else "中期"
            description = "市场情绪极度低迷，涨停家数稀少，风险极高，建议观望"
        elif limit_up < 50 or emotion < 60:
            cycle = "修复期"
            stage = "早期" if limit_up < 30 else "中期"
            description = "市场开始修复，情绪逐步回暖，可以小仓位试错"
        elif limit_up < 80 or emotion < 80:
            cycle = "主升期"
            stage = "早期" if limit_up < 60 else "中期"
            description = "市场进入主升阶段，情绪良好，可以积极参与主线"
        elif bomb_rate > 0.3:
            cycle = "分歧期"
            stage = "中期"
            description = "市场出现分歧，涨停家数多但炸板率高，注意风险控制"
        else:
            cycle = "高潮期"
            stage = "中期"
            description = "市场情绪高潮，涨停家数爆量，但需警惕随时退潮"
        
        # 检查是否进入退潮期
        if len(snapshots) >= 3:
            prev_limit_up = [s.limit_up_count for s in snapshots[:3]]
            if prev_limit_up[0] < prev_limit_up[1] and prev_limit_up[1] < prev_limit_up[2]:
                cycle = "退潮期"
                stage = "早期"
                description = "市场开始退潮，涨停家数连续下降，建议降低仓位"
        
        return {
            "cycle": cycle,
            "stage": stage,
            "description": description,
            "limit_up": limit_up,
            "emotion_score": emotion,
            "bomb_rate": bomb_rate
        }
    
    def analyze_emotion_trend(self, snapshots: List[MarketSnapshot], days: int = 5) -> Dict:
        """
        分析情绪趋势
        """
        if len(snapshots) < days:
            days = len(snapshots)
        
        if days == 0:
            return {"trend": [], "direction": "未知", "change_rate": 0}
        
        recent = snapshots[:days]
        emotion_scores = [s.emotion_score for s in recent]
        limit_ups = [s.limit_up_count for s in recent]
        
        # 判断方向
        if len(emotion_scores) >= 3:
            if emotion_scores[0] > emotion_scores[-1]:
                direction = "上升"
            elif emotion_scores[0] < emotion_scores[-1]:
                direction = "下降"
            else:
                direction = "震荡"
        else:
            direction = "震荡"
        
        # 计算变化率
        if len(emotion_scores) >= 2:
            change_rate = (emotion_scores[0] - emotion_scores[-1]) / emotion_scores[-1] * 100
        else:
            change_rate = 0
        
        # 生成描述
        if direction == "上升":
            desc = f"情绪持续回暖，近{days}天从{emotion_scores[-1]:.0f}提升到{emotion_scores[0]:.0f}"
        elif direction == "下降":
            desc = f"情绪持续降温，近{days}天从{emotion_scores[-1]:.0f}下降到{emotion_scores[0]:.0f}"
        else:
            desc = f"情绪震荡，近{days}天在{min(emotion_scores):.0f}-{max(emotion_scores):.0f}之间波动"
        
        return {
            "trend": emotion_scores,
            "limit_up_trend": limit_ups,
            "direction": direction,
            "change_rate": round(change_rate, 2),
            "description": desc
        }
    
    def analyze_sector_rotation(self, snapshots: List[MarketSnapshot], days: int = 7) -> Dict:
        """
        分析板块轮动
        """
        if len(snapshots) < days:
            days = len(snapshots)
        
        if days == 0:
            return {"rotation_history": {}, "has_rotation": False, "description": "数据不足"}
        
        recent = snapshots[:days]
        
        # 收集板块历史
        sector_history = {}
        for i, snapshot in enumerate(recent):
            day_label = f"T-{i}"
            sector_history[day_label] = snapshot.top_sectors
        
        # 检测板块切换
        has_rotation = False
        rotation_from = None
        rotation_to = None
        
        if len(recent) >= 2:
            today_top = set(recent[0].top_sectors[:2])
            yesterday_top = set(recent[1].top_sectors[:2])
            
            if not today_top.intersection(yesterday_top):
                has_rotation = True
                rotation_from = list(yesterday_top)[0] if yesterday_top else "未知"
                rotation_to = list(today_top)[0] if today_top else "未知"
        
        # 生成描述
        if has_rotation:
            desc = f"主线发生切换，从【{rotation_from}】切换到【{rotation_to}】"
        else:
            desc = f"主线延续，当前热点：{', '.join(snapshots[0].top_sectors[:3])}"
        
        return {
            "rotation_history": sector_history,
            "has_rotation": has_rotation,
            "rotation_from": rotation_from,
            "rotation_to": rotation_to,
            "description": desc
        }
    
    def analyze_leader_rotation(self, snapshots: List[MarketSnapshot], days: int = 5) -> Dict:
        """
        分析龙头切换
        """
        if len(snapshots) < days:
            days = len(snapshots)
        
        if days == 0:
            return {"rotation_history": [], "has_rotation": False, "description": "数据不足"}
        
        recent = snapshots[:days]
        
        # 收集龙头历史
        leader_history = []
        for i, snapshot in enumerate(recent):
            day_label = f"T-{i}"
            leader_history.append({
                "day": day_label,
                "leaders": snapshot.leaders
            })
        
        # 检测龙头切换
        has_rotation = False
        rotation_desc = ""
        
        if len(recent) >= 2:
            today_leaders = set(recent[0].leaders[:2])
            yesterday_leaders = set(recent[1].leaders[:2])
            
            if not today_leaders.intersection(yesterday_leaders):
                has_rotation = True
                rotation_desc = f"龙头发生切换，昨日{yesterday_leaders}→今日{today_leaders}"
            else:
                rotation_desc = f"龙头延续，当前龙头：{', '.join(snapshots[0].leaders[:2])}"
        
        return {
            "rotation_history": leader_history,
            "has_rotation": has_rotation,
            "description": rotation_desc
        }
    
    def analyze_risk_change(self, snapshots: List[MarketSnapshot], days: int = 5) -> Dict:
        """
        分析风险变化
        """
        if len(snapshots) < days:
            days = len(snapshots)
        
        if days == 0:
            return {"risk_history": [], "trend": "未知", "description": "数据不足"}
        
        recent = snapshots[:days]
        risk_history = [s.risk_level for s in recent]
        bomb_rates = [s.bomb_rate for s in recent]
        
        # 风险等级映射
        risk_map = {"低": 1, "中": 2, "高": 3}
        risk_scores = [risk_map.get(r, 2) for r in risk_history]
        
        # 判断趋势
        if len(risk_scores) >= 3:
            if risk_scores[0] > risk_scores[-1]:
                trend = "上升"
            elif risk_scores[0] < risk_scores[-1]:
                trend = "下降"
            else:
                trend = "稳定"
        else:
            trend = "稳定"
        
        # 炸板率趋势
        if len(bomb_rates) >= 2:
            bomb_trend = "上升" if bomb_rates[0] > bomb_rates[-1] else "下降"
        else:
            bomb_trend = "稳定"
        
        # 生成描述
        if trend == "上升":
            desc = f"风险上升，当前风险等级：{risk_history[0]}，炸板率{bomb_rates[0]*100:.1f}%"
        elif trend == "下降":
            desc = f"风险下降，当前风险等级：{risk_history[0]}，炸板率{bomb_rates[0]*100:.1f}%"
        else:
            desc = f"风险稳定，当前风险等级：{risk_history[0]}，炸板率{bomb_rates[0]*100:.1f}%"
        
        return {
            "risk_history": risk_history,
            "bomb_rate_history": bomb_rates,
            "trend": trend,
            "bomb_trend": bomb_trend,
            "description": desc
        }
    
    def save_snapshot(self, snapshot: MarketSnapshot) -> bool:
        """保存市场快照"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import json
            cursor.execute("""
            INSERT OR REPLACE INTO market_snapshots (
                date, timestamp, market_sentiment, emotion_score,
                limit_up_count, limit_down_count, highest_board,
                rising_count, falling_count, flat_count, rise_ratio,
                total_volume, volume_trend, north_money, north_money_trend,
                bomb_rate, risk_level, top_sectors, hot_theme,
                leaders, dragon_rotation, rotation_from, rotation_to,
                market_cycle, cycle_stage, index_change, raw_data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.date,
                snapshot.timestamp,
                snapshot.market_sentiment,
                snapshot.emotion_score,
                snapshot.limit_up_count,
                snapshot.limit_down_count,
                snapshot.highest_board,
                snapshot.rising_count,
                snapshot.falling_count,
                snapshot.flat_count,
                snapshot.rise_ratio,
                snapshot.total_volume,
                snapshot.volume_trend,
                snapshot.north_money,
                snapshot.north_money_trend,
                snapshot.bomb_rate,
                snapshot.risk_level,
                json.dumps(snapshot.top_sectors, ensure_ascii=False),
                snapshot.hot_theme,
                json.dumps(snapshot.leaders, ensure_ascii=False),
                1 if snapshot.dragon_rotation else 0,
                snapshot.rotation_from,
                snapshot.rotation_to,
                snapshot.market_cycle,
                snapshot.cycle_stage,
                json.dumps(snapshot.index_change, ensure_ascii=False),
                json.dumps(snapshot.raw_data, ensure_ascii=False) if snapshot.raw_data else None,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存市场快照失败: {e}")
            return False
    
    def get_recent_snapshots(self, days: int = 30) -> List[MarketSnapshot]:
        """获取最近N天的市场快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT date, timestamp, market_sentiment, emotion_score,
               limit_up_count, limit_down_count, highest_board,
               rising_count, falling_count, flat_count, rise_ratio,
               total_volume, volume_trend, north_money, north_money_trend,
               bomb_rate, risk_level, top_sectors, hot_theme,
               leaders, dragon_rotation, rotation_from, rotation_to,
               market_cycle, cycle_stage, index_change, raw_data
        FROM market_snapshots
        ORDER BY date DESC
        LIMIT ?
        """, (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        import json
        snapshots = []
        for row in rows:
            snapshots.append(MarketSnapshot(
                date=row[0],
                timestamp=row[1],
                market_sentiment=row[2],
                emotion_score=row[3],
                limit_up_count=row[4],
                limit_down_count=row[5],
                highest_board=row[6],
                rising_count=row[7],
                falling_count=row[8],
                flat_count=row[9],
                rise_ratio=row[10],
                total_volume=row[11],
                volume_trend=row[12],
                north_money=row[13],
                north_money_trend=row[14],
                bomb_rate=row[15],
                risk_level=row[16],
                top_sectors=json.loads(row[17]) if row[17] else [],
                hot_theme=row[18],
                leaders=json.loads(row[19]) if row[19] else [],
                dragon_rotation=bool(row[20]),
                rotation_from=row[21],
                rotation_to=row[22],
                market_cycle=row[23],
                cycle_stage=row[24],
                index_change=json.loads(row[25]) if row[25] else {},
                raw_data=json.loads(row[26]) if row[26] else None
            ))
        
        return snapshots
    
    def get_snapshot_by_date(self, date: str) -> Optional[MarketSnapshot]:
        """根据日期获取市场快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT date, timestamp, market_sentiment, emotion_score,
               limit_up_count, limit_down_count, highest_board,
               rising_count, falling_count, flat_count, rise_ratio,
               total_volume, volume_trend, north_money, north_money_trend,
               bomb_rate, risk_level, top_sectors, hot_theme,
               leaders, dragon_rotation, rotation_from, rotation_to,
               market_cycle, cycle_stage, index_change, raw_data
        FROM market_snapshots
        WHERE date = ?
        """, (date,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            import json
            return MarketSnapshot(
                date=row[0],
                timestamp=row[1],
                market_sentiment=row[2],
                emotion_score=row[3],
                limit_up_count=row[4],
                limit_down_count=row[5],
                highest_board=row[6],
                rising_count=row[7],
                falling_count=row[8],
                flat_count=row[9],
                rise_ratio=row[10],
                total_volume=row[11],
                volume_trend=row[12],
                north_money=row[13],
                north_money_trend=row[14],
                bomb_rate=row[15],
                risk_level=row[16],
                top_sectors=json.loads(row[17]) if row[17] else [],
                hot_theme=row[18],
                leaders=json.loads(row[19]) if row[19] else [],
                dragon_rotation=bool(row[20]),
                rotation_from=row[21],
                rotation_to=row[22],
                market_cycle=row[23],
                cycle_stage=row[24],
                index_change=json.loads(row[25]) if row[25] else {},
                raw_data=json.loads(row[26]) if row[26] else None
            )
        return None
    
    def generate_market_trend(self, days: int = 7) -> MarketTrend:
        """生成市场趋势分析"""
        snapshots = self.get_recent_snapshots(days)
        
        emotion_trend = self.analyze_emotion_trend(snapshots, days)
        sector_rotation = self.analyze_sector_rotation(snapshots, days)
        leader_rotation = self.analyze_leader_rotation(snapshots, days)
        risk_change = self.analyze_risk_change(snapshots, days)
        
        # 综合结论
        conclusions = []
        conclusions.append(f"市场周期：{emotion_trend['direction']}")
        conclusions.append(f"情绪得分：{emotion_trend['description']}")
        conclusions.append(f"板块轮动：{sector_rotation['description']}")
        conclusions.append(f"龙头切换：{leader_rotation['description']}")
        conclusions.append(f"风险变化：{risk_change['description']}")
        
        return MarketTrend(
            emotion_trend=emotion_trend['trend'],
            emotion_direction=emotion_trend['direction'],
            limit_up_trend=emotion_trend['limit_up_trend'],
            limit_up_direction=emotion_trend['direction'],
            volume_trend=[],
            volume_direction="未知",
            sector_rotation=sector_rotation['rotation_history'],
            leader_rotation=leader_rotation['rotation_history'],
            market_cycle_history=[],
            conclusion="；".join(conclusions)
        )
