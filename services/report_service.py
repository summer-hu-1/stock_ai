"""
Report Service - 报告生成服务

V9 架构：Service 层专门处理报告生成，调用 Agent 进行解释

职责：
- 接收 Pipeline 计算的结果
- 调用 Agent 进行市场结构解释
- 生成最终分析报告

原则：
- Agent 不做计算，只做解释
- ReportService 聚合 Pipeline + Agent
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReportService:
    """
    报告生成服务

    专门处理 AI 报告生成，调用 Agent 进行市场结构解释
    """

    def __init__(self):
        logger.info("🔧 初始化报告服务...")

    def generate_report(
        self,
        stock_code: str,
        factors: Dict,
        signals: Dict,
        leaders: Dict,
        memory: Dict
    ) -> Dict[str, Any]:
        """
        生成分析报告

        Args:
            stock_code: 股票代码
            factors: 因子结果（从 Pipeline 获取）
            signals: 信号结果（从 Pipeline 获取）
            leaders: 龙头结果（从 Pipeline 获取）
            memory: 市场记忆（从 Pipeline 获取）

        Returns:
            Dict: Agent 生成的报告结果
        """
        logger.info(f"🤖 为股票 {stock_code} 生成报告...")

        try:
            from agents.controller_agent import multi_agent_review

            # 调用 Agent 生成报告
            result = multi_agent_review(stock_code)

            logger.info(f"✅ 报告生成成功")
            return {
                "success": True,
                "data": result,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code
            }

    def generate_quick_report(self, stock_code: str) -> Dict[str, Any]:
        """
        快速生成报告（不经过 Pipeline，直接调用 Agent）

        用于简单分析场景

        Args:
            stock_code: 股票代码

        Returns:
            Dict: 报告结果
        """
        logger.info(f"⚡ 快速生成报告: {stock_code}")

        try:
            from agents.controller_agent import multi_agent_review
            result = multi_agent_review(stock_code)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"❌ 快速报告生成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局单例
_report_service_instance = None

def get_report_service() -> ReportService:
    """获取报告服务单例"""
    global _report_service_instance
    if _report_service_instance is None:
        _report_service_instance = ReportService()
    return _report_service_instance
