"""
统一分析结果数据模型 - AnalysisResult
供所有分析模块复用，统一数据入口和输出格式
"""

from typing import Dict, List, Optional


class AnalysisResult:
    def __init__(self):
        self.stock = {}               # 股票基本信息 {code, name, price, change_pct, ...}
        self.factors = {}             # 多因子得分
        self.signals = []             # 交易信号列表 [{name, value, direction}, ...]
        self.leader = {}              # 龙头/跟风判断
        self.short_term_state = {}    # 短线状态引擎输出
        self.market_memory = {}       # 市场记忆/情绪
        self.ai_summary = ""          # 最终给用户的自然语言分析（一段完成）

    def to_dict(self) -> Dict:
        return {
            "stock": self.stock,
            "factors": self.factors,
            "signals": self.signals,
            "leader": self.leader,
            "short_term_state": self.short_term_state,
            "market_memory": self.market_memory,
            "ai_summary": self.ai_summary,
        }