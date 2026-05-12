"""
分析结果模型

定义完整分析流程的结构化输出
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
from core.models.factor_result import FactorResult
from core.models.signal_result import SignalResult
from core.models.leader_result import LeaderResult


@dataclass
class MarketMemory:
    """市场记忆数据"""
    has_context: bool = False
    recent_snapshots: List[Dict] = field(default_factory=list)
    market_mood: str = ""
    volatility: float = 0.0
    hot_sectors: List[str] = field(default_factory=list)


@dataclass
class AgentAnalysis:
    """Agent分析结果"""
    success: bool = False
    summary: str = ""
    detailed_analysis: str = ""
    investment_suggestion: str = ""
    risk_warning: str = ""
    raw_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    完整分析结果
    
    这是整个分析管线的最终输出，整合所有子模块的结果
    """
    success: bool
    stock_code: str
    market: str = "cn"
    
    # 各模块结果
    factors: Optional[FactorResult] = None
    signals: Optional[SignalResult] = None
    leaders: Optional[LeaderResult] = None
    memory: Optional[MarketMemory] = None
    agent: Optional[AgentAnalysis] = None
    
    # 综合评分
    score: float = 50.0
    risk_level: str = "中"  # '低', '中', '高'
    signal: str = "观望"  # '看多', '谨慎看多', '观望', '谨慎看空', '看空'
    
    # 元数据
    elapsed_time: float = 0.0
    analysis_time: datetime = field(default_factory=datetime.now)
    
    # 错误信息
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于JSON序列化）"""
        return {
            "success": self.success,
            "stock_code": self.stock_code,
            "market": self.market,
            "score": self.score,
            "risk_level": self.risk_level,
            "signal": self.signal,
            "elapsed_time": self.elapsed_time,
            "analysis_time": self.analysis_time.isoformat(),
            "error": self.error
        }
    
    def get_summary(self) -> str:
        """生成简短的分析摘要"""
        parts = [
            f"股票: {self.stock_code}",
            f"综合评分: {self.score}",
            f"信号: {self.signal}",
            f"风险: {self.risk_level}"
        ]
        
        if self.leaders and self.leaders.is_leader:
            parts.append("👑 龙头股")
        
        return " | ".join(parts)
