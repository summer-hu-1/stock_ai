"""
Analysis Pipeline - 统一分析总线（QuantCore 包装器）

V10 架构：Pipeline 是 QuantCore 的便捷包装层，保持向后兼容

分析流程由 QuantCore 统一负责
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from core.quant_core import get_quant_core
from core.quant_core.models import QuantResult


class AnalysisPipeline:
    """
    统一分析管线（QuantCore 包装器）

    保持向后兼容，内部实际调用 QuantCore
    """

    def __init__(self):
        """初始化管线"""
        logger.info("🔧 初始化分析管线（QuantCore 包装器）...")
        self.quant_core = get_quant_core()
        logger.info("✅ 分析管线初始化完成")

    def analyze(
        self,
        stock_code: str,
        market: str = "cn",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整的分析流程（保持向后兼容）

        内部调用 QuantCore，返回兼容的旧格式
        """
        start_time = datetime.now()
        logger.info(f"🚀 开始分析股票: {stock_code}")

        try:
            # 调用 QuantCore 执行核心计算
            quant_result = self.quant_core.analyze(stock_code, market)

            # 转换为旧格式（保持向后兼容）
            old_format = self._convert_to_old_format(quant_result)

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"🎉 分析完成，耗时: {elapsed:.2f}秒")

            return old_format

        except Exception as e:
            logger.error(f"❌ 分析失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def _convert_to_old_format(self, quant_result: QuantResult) -> Dict[str, Any]:
        """
        将 QuantResult 转换为旧格式，保持向后兼容
        """
        return {
            "success": True,
            "stock_code": quant_result.code,
            "market": "cn",
            "factors": quant_result.factors.raw_data or {},
            "signals": quant_result.signals.raw_data or {},
            "leaders": quant_result.leaders.raw_data or {},
            "memory": quant_result.state.raw_data or {},
            "score": quant_result.score.final_score,
            "elapsed_time": quant_result.elapsed_ms / 1000.0,
            "analysis_time": quant_result.date.strftime("%Y-%m-%d %H:%M:%S"),
            "quant_result": quant_result  # 同时保留新格式
        }

    def load_data(self, stock_code: str, market: str = "cn") -> Optional[Any]:
        """
        加载股票数据（保持向后兼容）
        """
        return self.quant_core.datahub.get_ohlcv_dataframe(stock_code, market)

    def calculate_score(self, factors: Dict, signals: Dict, leaders: Dict) -> float:
        """
        计算综合评分（保持向后兼容，但不推荐使用）
        新代码应使用 QuantCore 直接计算
        """
        logger.warning("⚠️ 使用已弃用的 calculate_score 方法，建议使用 QuantCore")
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
