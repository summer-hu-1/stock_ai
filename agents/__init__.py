"""
agents package
多Agent市场情绪分析系统

核心架构：
- MarketContext: 统一数据层
- DataProvider: 统一数据提供者
- 各Agent从MarketContext读取数据，不直接访问AkShare
"""
from .controller_agent import run_all_agents, generate_report, multi_agent_review
from .market_agent import MarketAgent
from .sentiment_agent import SentimentAgent
from .sector_agent import SectorAgent
from .flow_agent import FlowAgent
from .risk_agent import RiskAgent

__all__ = [
    'multi_agent_review',
    'run_all_agents',
    'generate_report',
    'MarketAgent',
    'SentimentAgent',
    'SectorAgent',
    'FlowAgent',
    'RiskAgent',
]
