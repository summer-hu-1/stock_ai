from .engine import MarketStateEngine
from .snapshot_generator import MarketSnapshotGenerator
from .models import MarketSnapshot, MarketTrend, MarketInsight
from .insight_engine import MarketInsightEngine
from .historical_fetcher import HistoricalSnapshotFetcher
from typing import Dict, Optional, List


class MarketMemory:
    """
    市场记忆 - 统一API
    
    提供便捷的接口来访问市场历史数据和趋势分析
    """
    
    def __init__(self, db_path: str = None, llm_client=None):
        self.engine = MarketStateEngine(db_path)
        self.generator = MarketSnapshotGenerator(self.engine)
        self.insight_engine = MarketInsightEngine(db_path, llm_client)
        self.historical_fetcher = HistoricalSnapshotFetcher(db_path)
    
    def create_snapshot(self, sentiment_data: Dict) -> Optional[MarketSnapshot]:
        """
        创建市场快照
        
        Args:
            sentiment_data: 市场情绪数据（从get_market_sentiment获取）
        
        Returns:
            MarketSnapshot: 市场快照对象
        """
        return self.generator.generate_snapshot(sentiment_data)
    
    def save_snapshot(self, sentiment_data: Dict) -> bool:
        """
        创建并保存市场快照
        
        Args:
            sentiment_data: 市场情绪数据
        
        Returns:
            bool: 是否成功
        """
        return self.generator.generate_and_save(sentiment_data)
    
    def get_recent_snapshots(self, days: int = 30) -> List[MarketSnapshot]:
        """
        获取最近N天的市场快照
        
        Args:
            days: 天数
        
        Returns:
            List[MarketSnapshot]: 市场快照列表
        """
        return self.engine.get_recent_snapshots(days)
    
    def get_latest_snapshot(self) -> Optional[MarketSnapshot]:
        """
        获取最新的市场快照
        
        Returns:
            MarketSnapshot: 最新的市场快照
        """
        snapshots = self.get_recent_snapshots(1)
        return snapshots[0] if snapshots else None
    
    def analyze_market_cycle(self, days: int = 7) -> Dict:
        """
        分析市场周期
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场周期分析结果
        """
        snapshots = self.get_recent_snapshots(days)
        return self.engine.analyze_market_cycle(snapshots)
    
    def analyze_emotion_trend(self, days: int = 5) -> Dict:
        """
        分析情绪趋势
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 情绪趋势分析结果
        """
        snapshots = self.get_recent_snapshots(days)
        return self.engine.analyze_emotion_trend(snapshots, days)
    
    def analyze_sector_rotation(self, days: int = 7) -> Dict:
        """
        分析板块轮动
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 板块轮动分析结果
        """
        snapshots = self.get_recent_snapshots(days)
        return self.engine.analyze_sector_rotation(snapshots, days)
    
    def analyze_leader_rotation(self, days: int = 5) -> Dict:
        """
        分析龙头切换
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 龙头切换分析结果
        """
        snapshots = self.get_recent_snapshots(days)
        return self.engine.analyze_leader_rotation(snapshots, days)
    
    def analyze_risk_change(self, days: int = 5) -> Dict:
        """
        分析风险变化
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 风险变化分析结果
        """
        snapshots = self.get_recent_snapshots(days)
        return self.engine.analyze_risk_change(snapshots, days)
    
    def generate_market_trend(self, days: int = 7) -> MarketTrend:
        """
        生成市场趋势分析
        
        Args:
            days: 分析天数
        
        Returns:
            MarketTrend: 市场趋势对象
        """
        return self.engine.generate_market_trend(days)
    
    def get_market_context(self, days: int = 5) -> Dict:
        """
        获取市场上下文（用于Agent分析）
        
        返回最近N天的市场状态，包括：
        - 市场周期
        - 情绪趋势
        - 板块轮动
        - 龙头切换
        - 风险变化
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场上下文
        """
        snapshots = self.get_recent_snapshots(days)
        
        if not snapshots:
            return {
                "has_context": False,
                "message": "暂无历史数据"
            }
        
        market_cycle = self.engine.analyze_market_cycle(snapshots)
        emotion_trend = self.engine.analyze_emotion_trend(snapshots, days)
        sector_rotation = self.engine.analyze_sector_rotation(snapshots, days)
        leader_rotation = self.engine.analyze_leader_rotation(snapshots, days)
        risk_change = self.engine.analyze_risk_change(snapshots, days)
        
        return {
            "has_context": True,
            "days": days,
            "latest_date": snapshots[0].date,
            "market_cycle": market_cycle,
            "emotion_trend": emotion_trend,
            "sector_rotation": sector_rotation,
            "leader_rotation": leader_rotation,
            "risk_change": risk_change,
            "latest_snapshot": snapshots[0].to_dict() if snapshots else None
        }
    
    def format_market_context(self, days: int = 5) -> str:
        """
        格式化市场上下文为易读字符串
        
        Args:
            days: 分析天数
        
        Returns:
            str: 格式化的市场上下文
        """
        context = self.get_market_context(days)
        
        if not context.get("has_context"):
            return "暂无历史市场数据"
        
        lines = [
            f"【市场上下文（最近{days}天）】",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"📊 市场周期：{context['market_cycle']['cycle']}（{context['market_cycle']['stage']}）",
            f"   {context['market_cycle']['description']}",
            f"",
            f"😊 情绪趋势：{context['emotion_trend']['direction']}",
            f"   {context['emotion_trend']['description']}",
            f"",
            f"🔄 板块轮动：{context['sector_rotation']['description']}",
            f"",
            f"🐉 龙头切换：{context['leader_rotation']['description']}",
            f"",
            f"⚠️  风险变化：{context['risk_change']['description']}",
            f"",
            f"━━━━━━━━━━━━━━━━━━━━",
        ]
        
        return "\n".join(lines)
    
    def load_history_context(self, days: int = 5) -> Dict:
        """
        加载历史上下文（用于AI洞察生成）
        
        Args:
            days: 加载天数
        
        Returns:
            Dict: 历史上下文
        """
        return self.insight_engine.load_history_context(days)
    
    def build_market_story(self, days: int = 5) -> str:
        """
        构建市场故事
        
        Args:
            days: 分析天数
        
        Returns:
            str: 市场故事
        """
        return self.insight_engine.build_market_story(days)
    
    def build_llm_prompt(self, days: int = 5) -> str:
        """
        构建LLM提示词
        
        Args:
            days: 分析天数
        
        Returns:
            str: LLM提示词
        """
        return self.insight_engine.build_llm_prompt(days)
    
    def generate_market_insight(self, days: int = 5) -> MarketInsight:
        """
        生成市场洞察
        
        Args:
            days: 分析天数
        
        Returns:
            MarketInsight: 市场洞察对象
        """
        return self.insight_engine.generate_market_insight(days)
    
    def save_insight(self, insight: MarketInsight) -> bool:
        """
        保存市场洞察
        
        Args:
            insight: 市场洞察对象
        
        Returns:
            bool: 是否成功
        """
        return self.insight_engine.save_insight(insight)
    
    def get_latest_insight(self) -> Optional[MarketInsight]:
        """
        获取最新的市场洞察
        
        Returns:
            MarketInsight: 最新的市场洞察
        """
        return self.insight_engine.get_latest_insight()
    
    def get_recent_insights(self, days: int = 30) -> List[MarketInsight]:
        """
        获取最近N天的市场洞察
        
        Args:
            days: 天数
        
        Returns:
            List[MarketInsight]: 市场洞察列表
        """
        return self.insight_engine.get_recent_insights(days)
    
    # ========== 历史快照拉取 API ==========
    
    def fetch_historical_snapshot(self, date: str) -> bool:
        """
        拉取指定日期的历史市场快照
        
        Args:
            date: 日期（YYYY-MM-DD格式）
        
        Returns:
            bool: 是否成功
        """
        return self.historical_fetcher.fetch_and_save_snapshot(date)
    
    def fetch_date_range(self, start_date: str, end_date: str) -> Dict:
        """
        拉取指定日期范围的市场快照
        
        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
        
        Returns:
            Dict: 拉取结果统计
        """
        return self.historical_fetcher.fetch_date_range(start_date, end_date)
    
    def get_missing_dates(self, start_date: str, end_date: str) -> List[str]:
        """
        获取指定日期范围内缺失的日期
        
        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
        
        Returns:
            List[str]: 缺失的日期列表
        """
        return self.historical_fetcher.get_missing_dates(start_date, end_date)
    
    def update_missing_snapshots(self, days: int = 30) -> Dict:
        """
        增量更新最近N天缺失的快照
        
        Args:
            days: 天数（默认30天）
        
        Returns:
            Dict: 更新结果统计
        """
        return self.historical_fetcher.update_missing_snapshots(days)
