"""
Analysis Pipeline - 统一分析总线

V9 架构：Pipeline 负责"算"，ReportService 负责"解释"

分析流程：
1. 数据加载 → 2. 因子计算 → 3. 信号生成 → 4. 龙头识别 → 5. 市场记忆 → 6. 综合评分

采用 Pipeline 驱动架构，而非 UI 驱动架构
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from core.csv_provider import CSVProvider
from factors.factor_engine import FactorEngine
from signals.signal_engine import SignalEngine
from leaders.leader_engine import LeaderEngine
from core.market_memory import MarketMemory


class AnalysisPipeline:
    """
    统一分析管线

    V9 架构下仅负责计算，不调用 Agent
    Agent 解释由 ReportService 负责
    """

    def __init__(self):
        """初始化管线"""
        logger.info("🔧 初始化分析管线...")

        self.data_provider = CSVProvider()
        self.factor_engine = FactorEngine()
        self.signal_engine = SignalEngine()
        self.leader_engine = LeaderEngine()
        self.market_memory = MarketMemory()

        logger.info("✅ 分析管线初始化完成")

    def load_data(self, stock_code: str, market: str = "cn") -> Optional[Any]:
        """
        步骤 1: 加载股票数据

        数据获取策略：
        1. 优先从本地 CSV 获取
        2. 如果本地没有，尝试从网络获取

        Args:
            stock_code: 股票代码
            market: 市场（cn/hk/us）

        Returns:
            DataFrame: 股票日线数据
        """
        logger.info(f"📊 加载股票数据：{stock_code} (市场：{market})")
        try:
            df = self.data_provider.get_stock_daily(stock_code, market)
            if df is not None and not df.empty:
                logger.info(f"✅ 从本地CSV加载 {len(df)} 条数据")
                return df

            logger.warning(f"⚠️ 本地没有 {stock_code} 的数据，尝试网络获取...")
            try:
                from modules.market_data import get_stock_data_fast
                stock_data = get_stock_data_fast(stock_code, market)
                if stock_data and stock_data.get('data'):
                    logger.info(f"✅ 从网络获取历史数据成功")
                    import pandas as pd
                    df = pd.DataFrame(stock_data['data'])
                    if not df.empty:
                        return df
            except Exception as e:
                logger.warning(f"⚠️ 网络获取历史数据失败: {e}")

            try:
                from modules.market_data import get_stock_data
                realtime_data = get_stock_data(stock_code, market)
                if realtime_data:
                    logger.info(f"✅ 获取到实时数据")
                    import pandas as pd
                    df = pd.DataFrame([{
                        'date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                        'open': realtime_data.get('open', 0),
                        'close': realtime_data.get('price', 0),
                        'high': realtime_data.get('high', 0),
                        'low': realtime_data.get('low', 0),
                        'volume': realtime_data.get('volume', 0),
                        'turnover': realtime_data.get('market_cap', 0)
                    }])
                    return df
            except Exception as e:
                logger.warning(f"⚠️ 获取实时数据也失败: {e}")

            logger.error(f"❌ 无法获取股票 {stock_code} 的数据")
            return None
        except Exception as e:
            logger.error(f"❌ 加载数据失败: {e}")
            return None

    def analyze(
        self,
        stock_code: str,
        market: str = "cn",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整的分析流程

        V9 架构：只做计算，不调用 Agent
        Agent 解释由 ReportService.generate_report() 负责

        Args:
            stock_code: 股票代码
            market: 市场（cn/hk/us）
            use_cache: 是否使用缓存

        Returns:
            Dict: 包含计算结果的字典（不含 Agent 报告）
        """
        start_time = datetime.now()
        logger.info(f"🚀 开始分析股票: {stock_code}")

        try:
            # 1. 数据加载
            df = self.load_data(stock_code, market)
            if df is None:
                return {
                    "success": False,
                    "error": "无法加载股票数据",
                    "stock_code": stock_code
                }

            # 2. 因子计算
            logger.info("🔢 运行因子引擎...")
            factors = self.factor_engine.calculate(df)
            logger.info(f"✅ 因子计算完成")

            # 3. 信号生成
            logger.info("📡 运行信号引擎...")
            signals = self.signal_engine.generate(df, factors)
            logger.info(f"✅ 信号生成完成")

            # 4. 龙头识别
            logger.info("🐉 运行龙头引擎...")
            leaders = self.leader_engine.analyze(df, factors, signals)
            logger.info(f"✅ 龙头识别完成")

            # 5. 市场记忆
            logger.info("🧠 获取市场记忆...")
            memory = self.market_memory.get_market_context(days=5)
            logger.info(f"✅ 市场记忆获取完成")

            # 6. 综合评分
            logger.info("📈 计算综合评分...")
            final_score = self.calculate_score(factors, signals, leaders)
            logger.info(f"✅ 综合评分: {final_score}")

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"🎉 分析完成，耗时: {elapsed:.2f}秒")

            return {
                "success": True,
                "stock_code": stock_code,
                "market": market,
                "factors": factors,
                "signals": signals,
                "leaders": leaders,
                "memory": memory,
                "score": final_score,
                "elapsed_time": elapsed,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.error(f"❌ 分析失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def calculate_score(self, factors: Dict, signals: Dict, leaders: Dict) -> float:
        """
        计算综合评分

        评分权重：
        - 因子评分: 40%
        - 信号评分: 30%
        - 龙头评分: 30%

        Args:
            factors: 因子结果
            signals: 信号结果
            leaders: 龙头结果

        Returns:
            float: 综合评分（0-100）
        """
        try:
            factor_score = factors.get('summary', {}).get('overall_score', 50)
            signal_summary = signals.get('summary', {})
            signal_score = signal_summary.get('overall_strength', 50)
            leader_score = leaders.get('leader_score', 50)

            final_score = (
                factor_score * 0.4 +
                signal_score * 0.3 +
                leader_score * 0.3
            )

            return round(final_score, 1)

        except Exception as e:
            logger.error(f"❌ 计算综合评分失败: {e}")
            return 50.0

    def quick_analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        快速分析（简化版）

        Args:
            stock_code: 股票代码

        Returns:
            Dict: 简化的分析结果
        """
        result = self.analyze(stock_code)

        if not result.get("success"):
            return result

        return {
            "success": True,
            "stock_code": stock_code,
            "score": result["score"],
            "risk_level": self._determine_risk_level(result),
            "signal": self._determine_signal(result),
            "is_leader": result["leaders"].get("is_leader", False),
            "summary": self._generate_summary(result)
        }

    def _determine_risk_level(self, result: Dict) -> str:
        """根据分析结果确定风险等级"""
        score = result.get("score", 50)

        if score >= 70:
            return "低"
        elif score >= 40:
            return "中"
        else:
            return "高"

    def _determine_signal(self, result: Dict) -> str:
        """根据分析结果确定买卖信号"""
        score = result.get("score", 50)

        if score >= 75:
            return "看多"
        elif score >= 60:
            return "谨慎看多"
        elif score >= 40:
            return "观望"
        elif score >= 25:
            return "谨慎看空"
        else:
            return "看空"

    def _generate_summary(self, result: Dict) -> str:
        """生成简短的分析摘要"""
        score = result.get("score", 50)
        signal = self._determine_signal(result)
        risk = self._determine_risk_level(result)
        is_leader = result["leaders"].get("is_leader", False)

        parts = [
            f"综合评分: {score}",
            f"信号: {signal}",
            f"风险: {risk}"
        ]

        if is_leader:
            parts.append("👑 龙头股")

        return " | ".join(parts)


_pipeline_instance = None

def get_pipeline() -> AnalysisPipeline:
    """获取分析管线单例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = AnalysisPipeline()
    return _pipeline_instance
