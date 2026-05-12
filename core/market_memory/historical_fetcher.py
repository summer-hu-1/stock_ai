"""
HistoricalSnapshotFetcher - 历史快照拉取器

功能：
1. 优先从本地数据库获取真实历史数据
2. 本地数据不足时从akshare拉取
3. 支持增量拉取和全量拉取
4. 统一的API降级策略
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import akshare as ak
import os
import sys
import sqlite3

# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
script_dir = os.path.dirname(current_file_path)  # /core/market_memory
package_dir = os.path.dirname(script_dir)       # /core
project_dir = os.path.dirname(package_dir)      # /stock_ai
sys.path.insert(0, project_dir)

from core.market_memory.models import MarketSnapshot
from core.market_memory.engine import MarketStateEngine


class HistoricalSnapshotFetcher:
    """
    历史快照拉取器
    
    支持按日期范围获取历史市场数据并生成快照
    优先从本地数据库获取真实历史数据
    """
    
    def __init__(self, db_path: str = None):
        # 默认数据库路径（在 stock_ai 目录下）
        if db_path is None:
            self.db_path = os.path.join(project_dir, 'stock_history.db')
        else:
            self.db_path = db_path
        self.engine = MarketStateEngine(self.db_path)
    
    def _fetch_from_local_market_sentiment(self, date: str) -> Optional[Dict]:
        """
        从本地market_sentiment表获取历史数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rising_count, falling_count, limit_up_count, limit_down_count, 
                       rise_ratio, total_volume, bomb_rate, avg_change, market_mood
                FROM market_sentiment 
                WHERE date = ?
            ''', (date,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                print(f"✅ 从本地market_sentiment获取到 {date} 的数据")
                return {
                    "rising_count": row[0],
                    "falling_count": row[1],
                    "limit_up_count": row[2],
                    "limit_down_count": row[3],
                    "rise_ratio": row[4],
                    "total_volume": row[5],
                    "bomb_rate": row[6],
                    "avg_change": row[7],
                    "market_mood": row[8]
                }
            
            return None
        except Exception as e:
            print(f"⚠️ 从本地market_sentiment获取失败: {e}")
            return None
    
    def _fetch_from_local_snapshots(self, date: str) -> Optional[Dict]:
        """
        从本地market_snapshots表获取历史数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT emotion_score, limit_up_count, limit_down_count, rising_count, 
                       falling_count, flat_count, rise_ratio, total_volume, 
                       north_money, bomb_rate, top_sectors, hot_theme, leaders,
                       market_cycle, cycle_stage
                FROM market_snapshots 
                WHERE date = ?
            ''', (date,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                print(f"✅ 从本地market_snapshots获取到 {date} 的数据")
                import json
                return {
                    "emotion_score": row[0],
                    "limit_up_count": row[1],
                    "limit_down_count": row[2],
                    "rising_count": row[3],
                    "falling_count": row[4],
                    "flat_count": row[5],
                    "rise_ratio": row[6],
                    "total_volume": row[7],
                    "north_money": row[8],
                    "bomb_rate": row[9],
                    "top_sectors": json.loads(row[10]) if row[10] else [],
                    "hot_theme": row[11],
                    "leaders": json.loads(row[12]) if row[12] else [],
                    "market_cycle": row[13],
                    "cycle_stage": row[14]
                }
            
            return None
        except Exception as e:
            print(f"⚠️ 从本地market_snapshots获取失败: {e}")
            return None
    
    def _fetch_from_akshare(self, date: str) -> Optional[Dict]:
        """
        从akshare获取历史市场数据（降级方案）
        """
        try:
            market_summary = {}
            
            # 方法1: 尝试stock_zh_a_summary
            summary_data = self._get_market_summary_from_summary(date)
            
            # 方法2: 如果方法1失败，尝试stock_zh_a_today
            if summary_data is None:
                summary_data = self._get_market_summary_from_today()
            
            # 方法3: 如果方法2失败，尝试stock_zh_a_spot_em
            if summary_data is None:
                summary_data = self._get_market_summary_from_spot()
            
            if summary_data is None:
                print(f"❌ akshare所有API都无法获取 {date} 的数据")
                return None
            
            market_summary.update(summary_data)
            
            # 获取涨停股数据
            try:
                limit_up_df = ak.stock_zt_pool(date=date)
                if limit_up_df is not None and not limit_up_df.empty:
                    market_summary["limit_up_count"] = len(limit_up_df)
                    market_summary["limit_up_stocks"] = limit_up_df.to_dict('records')
                else:
                    market_summary["limit_up_count"] = 0
            except Exception as e:
                print(f"⚠️ 获取涨停股数据失败: {e}")
                market_summary["limit_up_count"] = 0
            
            # 获取跌停股数据
            try:
                limit_down_df = ak.stock_dt_pool(date=date)
                if limit_down_df is not None and not limit_down_df.empty:
                    market_summary["limit_down_count"] = len(limit_down_df)
                else:
                    market_summary["limit_down_count"] = 0
            except Exception as e:
                print(f"⚠️ 获取跌停股数据失败: {e}")
                market_summary["limit_down_count"] = 0
            
            # 获取热门板块
            try:
                sector_df = ak.stock_board_concept_name_em()
                if sector_df is not None and not sector_df.empty:
                    top_sectors = sector_df.nlargest(3, "涨跌幅")["板块名称"].tolist()
                    market_summary["top_sectors"] = top_sectors
                    market_summary["hot_theme"] = top_sectors[0] if top_sectors else "无"
                else:
                    market_summary["top_sectors"] = []
                    market_summary["hot_theme"] = "无"
            except Exception as e:
                print(f"⚠️ 获取热门板块失败: {e}")
                market_summary["top_sectors"] = []
                market_summary["hot_theme"] = "无"
            
            # 计算上涨比例
            total = market_summary.get("rising_count", 0) + market_summary.get("falling_count", 0) + market_summary.get("flat_count", 0)
            if total > 0:
                market_summary["rise_ratio"] = round(market_summary.get("rising_count", 0) / total * 100, 1)
            else:
                market_summary["rise_ratio"] = 50.0
            
            # 获取成交量（从上证指数获取）
            try:
                index_df = ak.stock_zh_index_daily(symbol="SH000001")
                if index_df is not None and not index_df.empty:
                    index_df['date'] = pd.to_datetime(index_df['date']).dt.strftime('%Y-%m-%d')
                    target_row = index_df[index_df['date'] == date]
                    if not target_row.empty:
                        market_summary["total_volume"] = target_row.iloc[0].get("volume", 0) / 100000000
            except Exception as e:
                print(f"⚠️ 获取上证指数数据失败: {e}")
            
            print(f"✅ 从akshare获取到 {date} 的数据")
            return market_summary
        
        except Exception as e:
            print(f"❌ 从akshare获取失败 {date}: {e}")
            return None
    
    def _get_market_summary_from_spot(self) -> Optional[Dict]:
        """从实时行情获取市场概况"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None
            
            rising_count = len(df[df['涨跌幅'] > 0])
            falling_count = len(df[df['涨跌幅'] < 0])
            flat_count = len(df[df['涨跌幅'] == 0])
            
            return {
                "rising_count": rising_count,
                "falling_count": falling_count,
                "flat_count": flat_count
            }
        except Exception as e:
            print(f"⚠️ stock_zh_a_spot_em 获取失败: {e}")
            return None
    
    def _get_market_summary_from_today(self) -> Optional[Dict]:
        """从今日概况获取市场数据"""
        try:
            if not hasattr(ak, 'stock_zh_a_today'):
                return None
            
            df = ak.stock_zh_a_today()
            if df is None or df.empty:
                return None
            
            market_summary = {}
            for _, row in df.iterrows():
                item = str(row.get("item", ""))
                value = str(row.get("value", ""))
                
                if "上涨家数" in item:
                    market_summary["rising_count"] = int(value)
                elif "下跌家数" in item:
                    market_summary["falling_count"] = int(value)
                elif "平盘家数" in item:
                    market_summary["flat_count"] = int(value)
                elif "两融余额" in item:
                    market_summary["margin_balance"] = float(value.replace("亿", "")) if "亿" in value else 0
                elif "北向资金" in item:
                    market_summary["north_money"] = float(value.replace("亿", "")) if "亿" in value else 0
            
            return market_summary
        except Exception as e:
            print(f"⚠️ stock_zh_a_today 获取失败: {e}")
            return None
    
    def _get_market_summary_from_summary(self, date: str) -> Optional[Dict]:
        """尝试从stock_zh_a_summary获取数据"""
        try:
            if not hasattr(ak, 'stock_zh_a_summary'):
                return None
            
            df = ak.stock_zh_a_summary(date=date)
            if df is None or df.empty:
                return None
            
            market_summary = {}
            for _, row in df.iterrows():
                item = row.get("item", "")
                value = row.get("value", "")
                
                if "上涨家数" in item:
                    market_summary["rising_count"] = int(value)
                elif "下跌家数" in item:
                    market_summary["falling_count"] = int(value)
                elif "平盘家数" in item:
                    market_summary["flat_count"] = int(value)
                elif "两融余额" in item:
                    market_summary["margin_balance"] = float(value.replace("亿", "")) if "亿" in value else 0
                elif "北向资金" in item:
                    market_summary["north_money"] = float(value.replace("亿", "")) if "亿" in value else 0
            
            return market_summary
        except Exception as e:
            print(f"⚠️ stock_zh_a_summary 获取失败: {e}")
            return None
    
    def _fetch_from_xueqiu(self, date: str) -> Optional[Dict]:
        """
        从雪球API获取历史市场数据（备用方案）
        """
        try:
            import requests
            import json
            
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://xueqiu.com/'
            }
            
            url = 'https://stock.xueqiu.com/v5/stock/realtime/quotec.json'
            params = {'symbol': 'SH000001,SZ399001,SZ399006'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'data' in data:
                    quotes = data['data']
                    
                    result = {
                        "rising_count": 0,
                        "falling_count": 0,
                        "flat_count": 0,
                        "limit_up_count": 0,
                        "limit_down_count": 0,
                        "rise_ratio": 50.0,
                        "total_volume": 0,
                        "bomb_rate": 0,
                        "avg_change": 0,
                        "market_mood": "震荡",
                        "is_xueqiu_data": True
                    }
                    
                    for quote in quotes:
                        if quote.get('symbol') == 'SH000001':
                            change_pct = quote.get('percent', 0)
                            result['avg_change'] = change_pct
                            if change_pct > 0:
                                result['market_mood'] = "上涨"
                                result['rise_ratio'] = min(100, 50 + change_pct * 3)
                            elif change_pct < 0:
                                result['market_mood'] = "下跌"
                                result['rise_ratio'] = max(0, 50 + change_pct * 3)
                    
                    print(f"✅ 从雪球API获取到 {date} 的数据")
                    return result
            
            print(f"⚠️ 雪球API返回状态码: {response.status_code}")
            return None
        except Exception as e:
            print(f"⚠️ 雪球API获取失败: {e}")
            return None
    
    def fetch_historical_market_data(self, date: str) -> Optional[Dict]:
        """
        获取指定日期的历史市场数据
        
        统一API降级策略（优先本地真实数据）：
        1. 从本地market_sentiment表获取
        2. 从本地market_snapshots表获取
        3. 从akshare获取
        4. 从雪球API获取（备用方案）
        
        Args:
            date: 日期（YYYY-MM-DD格式）
        
        Returns:
            Dict: 市场数据，如果所有来源都失败返回None
        """
        print(f"🔍 获取 {date} 的市场数据...")
        
        # 策略1: 优先从本地market_sentiment获取
        local_data = self._fetch_from_local_market_sentiment(date)
        if local_data is not None:
            return local_data
        
        # 策略2: 从本地market_snapshots获取
        local_data = self._fetch_from_local_snapshots(date)
        if local_data is not None:
            return local_data
        
        # 策略3: 从akshare获取（降级方案）
        akshare_data = self._fetch_from_akshare(date)
        if akshare_data is not None:
            return akshare_data
        
        # 策略4: 从雪球API获取（备用方案）
        print(f"⚠️ akshare获取失败，尝试雪球API...")
        xueqiu_data = self._fetch_from_xueqiu(date)
        if xueqiu_data is not None:
            return xueqiu_data
        
        # 所有策略都失败，返回None（不使用模拟数据）
        print(f"❌ 无法获取 {date} 的真实市场数据，所有来源均失败")
        return None
    
    def generate_historical_snapshot(self, date: str, market_data: Dict = None) -> Optional[MarketSnapshot]:
        """
        生成指定日期的历史市场快照
        
        Args:
            date: 日期（YYYY-MM-DD格式）
            market_data: 已获取的市场数据（可选）
        
        Returns:
            MarketSnapshot: 市场快照对象
        """
        try:
            if market_data is None:
                market_data = self.fetch_historical_market_data(date)
            
            if market_data is None:
                print(f"❌ 无法生成 {date} 的市场快照：没有可用数据")
                return None
            
            snapshots = self.engine.get_recent_snapshots(30)
            
            emotion_score = self._calculate_emotion_score(market_data)
            market_sentiment = self._determine_market_sentiment(market_data)
            leaders = self._get_leaders_from_data(market_data, date)
            top_sectors = market_data.get("top_sectors", [])
            hot_theme = market_data.get("hot_theme", "无")
            
            # 判断市场周期
            market_cycle, cycle_stage = self._determine_market_cycle(market_data, snapshots)
            
            # 检测龙头切换
            dragon_rotation, rotation_from, rotation_to = self._detect_dragon_rotation(market_data, snapshots)
            
            snapshot = MarketSnapshot(
                date=date,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                market_sentiment=market_sentiment,
                emotion_score=emotion_score,
                limit_up_count=market_data.get("limit_up_count", 0),
                limit_down_count=market_data.get("limit_down_count", 0),
                highest_board=self._calculate_highest_board(market_data),
                rising_count=market_data.get("rising_count", 0),
                falling_count=market_data.get("falling_count", 0),
                flat_count=market_data.get("flat_count", 0),
                rise_ratio=market_data.get("rise_ratio", 50.0),
                total_volume=market_data.get("total_volume", 0),
                volume_trend=self._determine_trend(market_data, snapshots, "total_volume"),
                north_money=market_data.get("north_money", 0),
                north_money_trend=self._determine_trend(market_data, snapshots, "north_money"),
                bomb_rate=market_data.get("bomb_rate", 0),
                risk_level=self._determine_risk_level(market_data),
                top_sectors=top_sectors,
                hot_theme=hot_theme,
                leaders=leaders,
                dragon_rotation=dragon_rotation,
                rotation_from=rotation_from,
                rotation_to=rotation_to,
                market_cycle=market_cycle,
                cycle_stage=cycle_stage,
                index_change=self._get_index_change(market_data),
                raw_data=str(market_data)
            )
            
            return snapshot
        
        except Exception as e:
            print(f"❌ 生成历史快照失败 {date}: {e}")
            return None
    
    def fetch_and_save_snapshot(self, date: str, skip_existing: bool = True) -> str:
        """
        获取并保存指定日期的市场快照
        
        Args:
            date: 日期（YYYY-MM-DD格式）
            skip_existing: 是否跳过已存在的快照
        
        Returns:
            str: 结果状态: 'success'(成功保存), 'skipped'(已存在或周末), 'failed'(失败)
        """
        try:
            # 检查是否已存在
            existing = self.engine.get_snapshot_by_date(date)
            if existing and skip_existing:
                print(f"ℹ️ {date} 的快照已存在，跳过")
                return 'skipped'
            
            # 检查是否为周末
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            if date_obj.weekday() >= 5:
                print(f"ℹ️ {date} 是周末，跳过")
                return 'skipped'
            
            # 获取市场数据
            market_data = self.fetch_historical_market_data(date)
            if market_data is None:
                print(f"❌ 无法获取 {date} 的市场数据")
                return 'failed'
            
            # 生成并保存快照
            snapshot = self.generate_historical_snapshot(date, market_data)
            if snapshot:
                self.engine.save_snapshot(snapshot)
                print(f"✅ 成功保存 {date} 的市场快照")
                return 'success'
            else:
                print(f"❌ 无法生成 {date} 的市场快照")
                return 'failed'
        
        except Exception as e:
            print(f"❌ 保存快照失败 {date}: {e}")
            return 'failed'
    
    def fetch_date_range(self, start_date: str, end_date: str) -> Dict:
        """
        按日期范围拉取市场快照
        
        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
        
        Returns:
            Dict: 拉取结果统计
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        total_days = (end - start).days + 1
        success = 0
        failed = 0
        skipped = 0
        
        print(f"📅 开始拉取 {start_date} 到 {end_date} 的市场快照（共 {total_days} 天）")
        print("=" * 60)
        
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            print(f"📥 正在处理 {date_str}...", end=" ")
            
            result = self.fetch_and_save_snapshot(date_str)
            if result == 'success':
                success += 1
                print("- ✅ 成功")
            elif result == 'skipped':
                skipped += 1
                print("- 已存在/周末，跳过")
            else:
                failed += 1
                print("- ❌ 失败")
            
            current_date += timedelta(days=1)
        
        print("=" * 60)
        print("✅ 拉取完成!")
        print(f"   成功: {success}")
        print(f"   失败: {failed}")
        print(f"   跳过: {skipped}")
        print(f"   总计: {total_days} 天")
        
        return {
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "total_days": total_days
        }
    
    def get_missing_dates(self, start_date: str, end_date: str) -> List[str]:
        """
        获取指定日期范围内缺失的日期
        
        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
        
        Returns:
            List[str]: 缺失的日期列表
        """
        missing_dates = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 跳过周末
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # 检查是否存在快照
            if not self.engine.get_snapshot_by_date(date_str):
                missing_dates.append(date_str)
            
            current_date += timedelta(days=1)
        
        return missing_dates
    
    def update_missing_snapshots(self, days: int = 7) -> Dict:
        """
        增量更新最近N天缺失的快照
        
        Args:
            days: 天数，默认7天
        
        Returns:
            Dict: 更新结果统计
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        missing_dates = self.get_missing_dates(start_date, end_date)
        
        if not missing_dates:
            print("✅ 没有缺失的快照，数据已是最新")
            return {"total_missing": 0, "success": 0, "failed": 0}
        
        print(f"🔍 发现 {len(missing_dates)} 天缺失的快照")
        
        success = 0
        failed = 0
        
        for date_str in missing_dates:
            print(f"📥 正在拉取 {date_str}...", end=" ")
            result = self.fetch_and_save_snapshot(date_str)
            if result == 'success':
                success += 1
                print("- ✅ 成功")
            elif result == 'failed':
                failed += 1
                print("- ❌ 失败")
            else:
                # skipped
                print("- 跳过")
        
        return {
            "total_missing": len(missing_dates),
            "success": success,
            "failed": failed
        }
    
    def _calculate_emotion_score(self, market_data: Dict) -> float:
        """计算情绪得分"""
        try:
            score = 50.0
            
            if "limit_up_count" in market_data:
                score += min(market_data["limit_up_count"] / 10, 20)
            if "limit_down_count" in market_data:
                score -= min(market_data["limit_down_count"] / 5, 15)
            if "rise_ratio" in market_data:
                score += (market_data["rise_ratio"] - 50) * 0.3
            
            return round(max(0, min(100, score)), 1)
        except:
            return 50.0
    
    def _determine_market_sentiment(self, market_data: Dict) -> str:
        """判断市场情绪"""
        emotion_score = self._calculate_emotion_score(market_data)
        
        if emotion_score >= 80:
            return "极度亢奋"
        elif emotion_score >= 65:
            return "偏强"
        elif emotion_score >= 50:
            return "中性偏强"
        elif emotion_score >= 35:
            return "中性偏弱"
        elif emotion_score >= 20:
            return "偏弱"
        else:
            return "极度低迷"
    
    def _get_leaders_from_data(self, market_data: Dict, date: str) -> List[str]:
        """从数据中获取龙头股"""
        try:
            if "limit_up_stocks" in market_data and market_data["limit_up_stocks"]:
                stocks = market_data["limit_up_stocks"]
                # 简单返回前5个涨停股作为龙头候选
                leaders = []
                for stock in stocks[:5]:
                    name = stock.get("名称", stock.get("stock_name", ""))
                    if name:
                        leaders.append(name)
                return leaders
        except:
            pass
        return ["待定"]
    
    def _calculate_highest_board(self, market_data: Dict) -> int:
        """计算最高连板数"""
        try:
            limit_up_count = market_data.get("limit_up_count", 0)
            if limit_up_count >= 100:
                return 7
            elif limit_up_count >= 60:
                return 5
            elif limit_up_count >= 30:
                return 3
            elif limit_up_count >= 10:
                return 2
            else:
                return 1
        except:
            return 1
    
    def _determine_trend(self, market_data: Dict, snapshots: List, field: str) -> str:
        """判断趋势"""
        current_value = market_data.get(field, 0)
        if not snapshots or len(snapshots) < 3:
            return "稳定"
        
        recent_values = []
        for snap in snapshots[:5]:
            if hasattr(snap, field):
                recent_values.append(getattr(snap, field, 0))
        
        if not recent_values:
            return "稳定"
        
        avg_recent = sum(recent_values) / len(recent_values)
        
        if current_value > avg_recent * 1.1:
            return "上升"
        elif current_value < avg_recent * 0.9:
            return "下降"
        else:
            return "稳定"
    
    def _determine_risk_level(self, market_data: Dict) -> str:
        """判断风险等级"""
        emotion_score = self._calculate_emotion_score(market_data)
        bomb_rate = market_data.get("bomb_rate", 0)
        
        if emotion_score >= 85 or bomb_rate >= 0.15:
            return "高风险"
        elif emotion_score >= 70 or bomb_rate >= 0.1:
            return "中风险"
        elif emotion_score <= 20:
            return "低风险"
        else:
            return "正常"
    
    def _determine_market_cycle(self, market_data: Dict, snapshots: List) -> tuple:
        """判断市场周期"""
        emotion_score = self._calculate_emotion_score(market_data)
        limit_up_count = market_data.get("limit_up_count", 0)
        limit_down_count = market_data.get("limit_down_count", 0)
        
        if emotion_score <= 25 and limit_up_count < 10:
            return ("冰点期", "情绪冰点")
        elif emotion_score >= 80 and limit_up_count >= 80:
            return ("高潮期", "情绪高潮")
        elif emotion_score >= 65 and limit_up_count >= 40:
            return ("主升期", "上升趋势")
        elif emotion_score < 50 and limit_down_count > limit_up_count:
            return ("退潮期", "下降趋势")
        elif 45 <= emotion_score <= 55:
            return ("修复期", "震荡修复")
        else:
            return ("分歧期", "多空分歧")
    
    def _detect_dragon_rotation(self, market_data: Dict, snapshots: List) -> tuple:
        """检测龙头切换"""
        try:
            if len(snapshots) < 3:
                return (0, "", "")
            
            recent_themes = []
            for snap in snapshots[:3]:
                if snap.hot_theme and snap.hot_theme != "无":
                    recent_themes.append(snap.hot_theme)
            
            current_theme = market_data.get("hot_theme", "无")
            
            if recent_themes and current_theme != recent_themes[-1]:
                return (1, recent_themes[-1], current_theme)
            
            return (0, "", "")
        except:
            return (0, "", "")
    
    def _get_index_change(self, market_data: Dict) -> str:
        """获取指数变化"""
        avg_change = market_data.get("avg_change", 0)
        if avg_change > 1.5:
            return "大幅上涨"
        elif avg_change > 0.5:
            return "小幅上涨"
        elif avg_change < -1.5:
            return "大幅下跌"
        elif avg_change < -0.5:
            return "小幅下跌"
        else:
            return "震荡整理"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="历史快照拉取器")
    parser.add_argument("action", choices=["fetch", "range", "update", "missing"], 
                        help="操作类型: fetch(单日期), range(日期范围), update(增量更新), missing(查看缺失)")
    parser.add_argument("--date", help="单日期拉取 (YYYY-MM-DD)")
    parser.add_argument("--start-date", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=7, help="增量更新天数")
    
    args = parser.parse_args()
    
    fetcher = HistoricalSnapshotFetcher()
    
    if args.action == "fetch" and args.date:
        result = fetcher.fetch_and_save_snapshot(args.date)
        print(f"结果: {'成功' if result else '失败'}")
    
    elif args.action == "range" and args.start_date and args.end_date:
        result = fetcher.fetch_date_range(args.start_date, args.end_date)
        print(f"结果: 成功={result['success']}, 失败={result['failed']}, 跳过={result['skipped']}")
    
    elif args.action == "update":
        result = fetcher.update_missing_snapshots(args.days)
        print(f"结果: 缺失={result['total_missing']}, 成功={result['success']}, 失败={result['failed']}")
    
    elif args.action == "missing" and args.start_date and args.end_date:
        missing = fetcher.get_missing_dates(args.start_date, args.end_date)
        print(f"缺失日期: {missing}")
        print(f"共 {len(missing)} 天缺失")
