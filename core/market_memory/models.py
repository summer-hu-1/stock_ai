from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional
import json


@dataclass
class MarketSnapshot:
    """
    市场快照数据模型
    每天收盘后生成，保存完整的市场状态
    """
    date: str
    timestamp: str
    
    # 市场情绪
    market_sentiment: str  # 冰点/修复/高潮/分歧/退潮
    emotion_score: float  # 情绪得分 0-100
    
    # 涨跌停统计
    limit_up_count: int
    limit_down_count: int
    highest_board: int  # 最高连板高度
    
    # 市场广度
    rising_count: int
    falling_count: int
    flat_count: int
    rise_ratio: float
    
    # 成交量
    total_volume: float  # 万亿
    volume_trend: str  # 放量/缩量/平量
    
    # 北向资金
    north_money: float  # 亿
    north_money_trend: str  # 流入/流出/持平
    
    # 风险指标
    bomb_rate: float  # 炸板率
    risk_level: str  # 低/中/高
    
    # 热点板块
    top_sectors: List[str]  # 前三大热点板块
    hot_theme: str  # 最热主题
    
    # 龙头股
    leaders: List[str]  # 前三大龙头股（名称+代码）
    
    # 板块轮动
    dragon_rotation: bool  # 是否发生龙头切换
    rotation_from: Optional[str]  # 从哪个板块切换
    rotation_to: Optional[str]  # 切换到哪个板块
    
    # 市场周期
    market_cycle: str  # 冰点期/修复期/主升期/分歧期/退潮期
    cycle_stage: str  # 早期/中期/晚期
    
    # 指数表现
    index_change: Dict[str, float]  # 各大指数涨跌幅
    
    # 原始数据（用于调试）
    raw_data: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketSnapshot':
        """从字典创建实例"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MarketSnapshot':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class MarketTrend:
    """
    市场趋势分析结果
    """
    emotion_trend: List[float]  # 近N天情绪得分变化
    emotion_direction: str  # 上升/下降/震荡
    
    limit_up_trend: List[int]  # 近N天涨停家数变化
    limit_up_direction: str  # 上升/下降/震荡
    
    volume_trend: List[float]  # 近N天成交量变化
    volume_direction: str  # 放量/缩量/平量
    
    sector_rotation: Dict[str, List[str]]  # 板块轮动历史
    leader_rotation: List[Dict[str, str]]  # 龙头股切换历史
    
    market_cycle_history: List[str]  # 市场周期变化历史
    
    conclusion: str  # 综合结论
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class MarketInsight:
    """
    市场洞察（AI生成的分析结论）
    """
    date: str
    timestamp: str
    
    # 市场状态
    current_state: str
    state_description: str
    
    # 趋势分析
    trend_analysis: str
    
    # 风险提示
    risk_alert: str
    
    # 机会提示
    opportunity: str
    
    # 操作建议
    action_suggestion: str
    
    # 关键变化
    key_changes: List[str]
    
    # 置信度
    confidence: float
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
