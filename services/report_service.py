"""
Report Service - 报告生成服务

V10 架构：使用 AgentOS 统一处理 AI 认知层

职责：
- 统一使用 AgentOS 进行分析
- 保持向后兼容旧接口
- 聚合 QuantCore + AgentOS

原则：
- 所有计算由 QuantCore 完成
- 所有解释由 AgentOS 完成
- ReportService 只做粘合
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReportService:
    """
    报告生成服务

    V10 架构：使用 AgentOS 统一处理 AI 认知层
    """

    def __init__(self):
        logger.info("🔧 初始化报告服务（AgentOS）...")
        from core.agent_os import get_agent_os
        self.agent_os = get_agent_os()

    def generate_report(
        self,
        stock_code: str,
        factors: Dict = None,
        signals: Dict = None,
        leaders: Dict = None,
        memory: Dict = None
    ) -> Dict[str, Any]:
        """
        生成分析报告（保持向后兼容）

        新代码建议直接使用 agent_os.analyze_stock()
        """
        logger.info(f"🤖 为股票 {stock_code} 生成报告...")

        try:
            # 使用 AgentOS 统一处理
            result = self.agent_os.analyze_stock(stock_code)

            if not result.get("success"):
                return result

            logger.info(f"✅ 报告生成成功")
            return {
                "success": True,
                "data": {
                    "agent_results": {},
                    "final_report": result.get("agent_report", ""),
                    "summary": result.get("summary", {}),
                    "quant_result": result.get("quant_result")
                },
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
        快速生成报告（保持向后兼容）

        新代码建议直接使用 agent_os.analyze_stock()
        """
        logger.info(f"⚡ 快速生成报告: {stock_code}")

        try:
            result = self.agent_os.analyze_stock(stock_code)

            if not result.get("success"):
                return result

            return {
                "success": True,
                "data": {
                    "final_report": result.get("agent_report", ""),
                    "summary": result.get("summary", {})
                }
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
