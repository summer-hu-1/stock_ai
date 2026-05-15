"""
AgentOS - Agent认知层

V10 架构核心：只做解释，不做计算

职责：
1. 理解量化结果
2. 生成分析报告
3. 认知推理
4. 总结生成

⚠️ 核心原则：
- AgentOS 只负责解释，不负责计算
- 所有计算必须由 QuantCore 完成
- AgentOS 接收 QuantResult，输出 AnalysisReport
"""

from .interpreter import AgentOS, get_agent_os
from .models import AnalysisReport, TradingInsight

__all__ = [
    "AgentOS",
    "get_agent_os",
    "AnalysisReport",
    "TradingInsight",
]
