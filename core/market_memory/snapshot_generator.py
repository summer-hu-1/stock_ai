from typing import Dict, Optional
from datetime import datetime
import akshare as ak
import pandas as pd
from .models import MarketSnapshot
from .engine import MarketStateEngine


class MarketSnapshotGenerator:
    """
    市场快照生成器
    
    每天收盘后生成完整的市场快照，包括：
    - 市场情绪
    - 涨跌停统计
    - 龙头股
    - 热点板块
    - 成交量
    - 北向资金
    - 风险指标
    """
    
    def __init__(self, engine: MarketStateEngine = None):
        self.engine = engine or MarketStateEngine()
    
    def _calculate_emotion_score(self, sentiment_data: Dict) -> float:
        """
        计算情绪得分（0-100）
        
        因素：
        - 涨停家数（权重40%）
        - 涨跌比例（权重30%）
        - 成交量（权重20%）
        - 炸板率（权重10%，反向）
        """
        limit_up = sentiment_data.get("limit_up_count", 0)
        rise_ratio = sentiment_data.get("rise_ratio", 0)
        total_volume = sentiment_data.get("total_volume", 0)
        bomb_rate = sentiment_data.get("bomb_rate", 0)
        
        # 涨停家数得分（0-40分）
        if limit_up >= 100:
            limit_up_score = 40
        elif limit_up >= 80:
            limit_up_score = 35
        elif limit_up >= 50:
            limit_up_score = 25
        elif limit_up >= 30:
            limit_up_score = 15
        elif limit_up >= 20:
            limit_up_score = 10
        else:
            limit_up_score = 5
        
        # 涨跌比例得分（0-30分）
        if rise_ratio >= 70:
            rise_ratio_score = 30
        elif rise_ratio >= 60:
            rise_ratio_score = 25
        elif rise_ratio >= 50:
            rise_ratio_score = 20
        elif rise_ratio >= 40:
            rise_ratio_score = 15
        else:
            rise_ratio_score = 10
        
        # 成交量得分（0-20分）
        if total_volume >= 12:
            volume_score = 20
        elif total_volume >= 10:
            volume_score = 18
        elif total_volume >= 8:
            volume_score = 15
        elif total_volume >= 6:
            volume_score = 12
        else:
            volume_score = 8
        
        # 炸板率得分（0-10分，反向）
        if bomb_rate <= 0.1:
            bomb_score = 10
        elif bomb_rate <= 0.2:
            bomb_score = 8
        elif bomb_rate <= 0.3:
            bomb_score = 5
        else:
            bomb_score = 2
        
        total_score = limit_up_score + rise_ratio_score + volume_score + bomb_score
        return round(total_score, 1)
    
    def _determine_market_sentiment(self, sentiment_data: Dict) -> str:
        """判断市场情绪（冰点/修复/高潮/分歧/退潮）"""
        limit_up = sentiment_data.get("limit_up_count", 0)
        bomb_rate = sentiment_data.get("bomb_rate", 0)
        rise_ratio = sentiment_data.get("rise_ratio", 0)
        
        if limit_up < 20:
            return "冰点"
        elif limit_up < 50:
            return "修复"
        elif bomb_rate > 0.3:
            return "分歧"
        elif limit_up > 80:
            return "高潮"
        else:
            return "震荡"
    
    def _get_highest_board(self) -> int:
        """获取最高连板高度"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return 0
            
            # 获取涨停股
            limit_up_stocks = df[df["涨跌幅"] >= 9.8]
            
            if limit_up_stocks.empty:
                return 0
            
            # 计算连板高度（这里简化处理，实际需要获取历史数据）
            # 暂时返回涨停家数作为替代
            return len(limit_up_stocks)
        except Exception as e:
            print(f"获取最高连板失败: {e}")
            return 0
    
    def _get_leaders(self, top_n: int = 3) -> list:
        """获取龙头股（前N只涨停股）"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return []
            
            # 按成交额排序，取前N只涨停股
            limit_up_stocks = df[df["涨跌幅"] >= 9.8]
            if limit_up_stocks.empty:
                return []
            
            top_leaders = limit_up_stocks.nlargest(top_n, "成交额")
            
            leaders = []
            for _, row in top_leaders.iterrows():
                name = row.get("名称", "")
                code = row.get("代码", "")
                leaders.append(f"{name}({code})")
            
            return leaders
        except Exception as e:
            print(f"获取龙头股失败: {e}")
            return []
    
    def _get_top_sectors(self, top_n: int = 3) -> list:
        """获取前N个热门板块"""
        try:
            df = ak.stock_board_concept_name_em()
            if df is None or df.empty:
                return []
            
            top_sectors = df.nlargest(top_n, "涨跌幅")
            return top_sectors["板块名称"].tolist()
        except Exception as e:
            print(f"获取热门板块失败: {e}")
            return []
    
    def _get_hot_theme(self, top_sectors: list) -> str:
        """获取最热主题"""
        if not top_sectors:
            return "无"
        return top_sectors[0]
    
    def _determine_volume_trend(self, current_volume: float, snapshots: list) -> str:
        """判断成交量趋势"""
        if not snapshots:
            return "平量"
        
        prev_volume = snapshots[0].total_volume if snapshots else 0
        
        if current_volume > prev_volume * 1.1:
            return "放量"
        elif current_volume < prev_volume * 0.9:
            return "缩量"
        else:
            return "平量"
    
    def _get_north_money(self) -> tuple:
        """获取北向资金（模拟数据）"""
        # 这里应该调用真实的北向资金API
        # 暂时返回模拟数据
        return 52.0, "流入"
    
    def _determine_risk_level(self, sentiment_data: Dict) -> str:
        """判断风险等级"""
        limit_up = sentiment_data.get("limit_up_count", 0)
        bomb_rate = sentiment_data.get("bomb_rate", 0)
        
        if bomb_rate > 0.3 or limit_up < 20:
            return "高"
        elif bomb_rate > 0.2 or limit_up < 30:
            return "中"
        else:
            return "低"
    
    def _detect_dragon_rotation(self, current_sectors: list, snapshots: list) -> tuple:
        """检测龙头切换"""
        if not snapshots:
            return False, None, None
        
        prev_sectors = snapshots[0].top_sectors if snapshots else []
        
        if not prev_sectors or not current_sectors:
            return False, None, None
        
        # 检查前两大板块是否发生变化
        current_top = set(current_sectors[:2])
        prev_top = set(prev_sectors[:2])
        
        if not current_top.intersection(prev_top):
            return True, prev_top[0] if prev_top else None, current_top[0] if current_top else None
        
        return False, None, None
    
    def _get_index_change(self) -> dict:
        """获取各大指数涨跌幅"""
        try:
            indices = {
                "上证指数": "SH000001",
                "深证成指": "SZ399001",
                "创业板指": "SZ399006"
            }
            
            changes = {}
            for name, code in indices.items():
                try:
                    df = ak.stock_zh_index_daily(symbol=code)
                    if df is not None and not df.empty:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
                        change = (latest['close'] - prev['close']) / prev['close'] * 100
                        changes[name] = round(change, 2)
                except:
                    changes[name] = 0.0
            
            return changes
        except Exception as e:
            print(f"获取指数涨跌失败: {e}")
            return {}
    
    def _determine_market_cycle(self, sentiment_data: Dict, emotion_score: float) -> tuple:
        """判断市场周期和阶段"""
        limit_up = sentiment_data.get("limit_up_count", 0)
        bomb_rate = sentiment_data.get("bomb_rate", 0)
        
        if limit_up < 20 or emotion_score < 30:
            return "冰点期", "晚期" if limit_up < 10 else "中期"
        elif limit_up < 50 or emotion_score < 60:
            return "修复期", "早期" if limit_up < 30 else "中期"
        elif limit_up < 80 or emotion_score < 80:
            return "主升期", "早期" if limit_up < 60 else "中期"
        elif bomb_rate > 0.3:
            return "分歧期", "中期"
        else:
            return "高潮期", "中期"
    
    def generate_snapshot(self, sentiment_data: Dict) -> Optional[MarketSnapshot]:
        """
        生成市场快照
        
        Args:
            sentiment_data: 市场情绪数据（从get_market_sentiment获取）
        
        Returns:
            MarketSnapshot: 市场快照对象
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 获取历史快照（用于对比）
            snapshots = self.engine.get_recent_snapshots(7)
            
            # 计算情绪得分
            emotion_score = self._calculate_emotion_score(sentiment_data)
            
            # 判断市场情绪
            market_sentiment = self._determine_market_sentiment(sentiment_data)
            
            # 获取最高连板
            highest_board = self._get_highest_board()
            
            # 获取龙头股
            leaders = self._get_leaders(top_n=3)
            
            # 获取热门板块
            top_sectors = self._get_top_sectors(top_n=3)
            hot_theme = self._get_hot_theme(top_sectors)
            
            # 判断成交量趋势
            volume_trend = self._determine_volume_trend(sentiment_data.get("total_volume", 0), snapshots)
            
            # 获取北向资金
            north_money, north_money_trend = self._get_north_money()
            
            # 判断风险等级
            risk_level = self._determine_risk_level(sentiment_data)
            
            # 检测龙头切换
            dragon_rotation, rotation_from, rotation_to = self._detect_dragon_rotation(top_sectors, snapshots)
            
            # 获取指数涨跌
            index_change = self._get_index_change()
            
            # 判断市场周期
            market_cycle, cycle_stage = self._determine_market_cycle(sentiment_data, emotion_score)
            
            # 创建快照
            snapshot = MarketSnapshot(
                date=today,
                timestamp=timestamp,
                market_sentiment=market_sentiment,
                emotion_score=emotion_score,
                limit_up_count=sentiment_data.get("limit_up_count", 0),
                limit_down_count=sentiment_data.get("limit_down_count", 0),
                highest_board=highest_board,
                rising_count=sentiment_data.get("rising_count", 0),
                falling_count=sentiment_data.get("falling_count", 0),
                flat_count=sentiment_data.get("flat_count", 0),
                rise_ratio=sentiment_data.get("rise_ratio", 0),
                total_volume=sentiment_data.get("total_volume", 0),
                volume_trend=volume_trend,
                north_money=north_money,
                north_money_trend=north_money_trend,
                bomb_rate=sentiment_data.get("bomb_rate", 0),
                risk_level=risk_level,
                top_sectors=top_sectors,
                hot_theme=hot_theme,
                leaders=leaders,
                dragon_rotation=dragon_rotation,
                rotation_from=rotation_from,
                rotation_to=rotation_to,
                market_cycle=market_cycle,
                cycle_stage=cycle_stage,
                index_change=index_change,
                raw_data=sentiment_data
            )
            
            return snapshot
        except Exception as e:
            print(f"生成市场快照失败: {e}")
            return None
    
    def generate_and_save(self, sentiment_data: Dict) -> bool:
        """
        生成并保存市场快照
        
        Args:
            sentiment_data: 市场情绪数据
        
        Returns:
            bool: 是否成功
        """
        snapshot = self.generate_snapshot(sentiment_data)
        if snapshot:
            return self.engine.save_snapshot(snapshot)
        return False
