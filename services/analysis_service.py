"""
Analysis Service - 分析服务

V9 Service Layer 的核心组件，提供统一的分析接口：
1. Pipeline 计算（因子、信号、龙头、评分）
2. ReportService 报告生成（Agent 解释）

V9 架构原则：
- Pipeline 负责"算"
- ReportService 负责"解释"
- Service 统一封装，屏蔽复杂度
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AnalysisService:
    """
    分析服务

    V9 架构下统一入口，同时调用 Pipeline 计算和 ReportService 报告生成
    """

    MODE_ONLINE = "online"
    MODE_REAL_TIME = "realtime"

    def __init__(self, mode: str = MODE_ONLINE):
        logger.info(f"🔧 初始化分析服务（模式: {mode}）")
        self.mode = mode
        self._pipeline = None
        self._report_service = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            from core.analysis_pipeline import get_pipeline
            self._pipeline = get_pipeline()
        return self._pipeline

    @property
    def report_service(self):
        if self._report_service is None:
            from services.report_service import get_report_service
            self._report_service = get_report_service()
        return self._report_service

    def analyze_stock(self, stock_code: str, market: str = "cn", with_report: bool = False) -> Dict[str, Any]:
        """
        分析单只股票

        V9 架构：
        1. 调用 Pipeline 进行计算
        2. 可选调用 ReportService 生成报告

        Args:
            stock_code: 股票代码
            market: 市场（cn/hk/us）
            with_report: 是否生成 Agent 报告

        Returns:
            Dict: 分析结果
        """
        logger.info(f"🚀 分析股票: {stock_code} (with_report={with_report})")

        try:
            calc_result = self.pipeline.analyze(stock_code, market)

            if not calc_result.get("success"):
                logger.warning(f"⚠️ 股票 {stock_code} 计算失败: {calc_result.get('error')}")
                return calc_result

            if with_report:
                logger.info("🤖 生成 Agent 报告...")
                report_result = self.report_service.generate_report(
                    stock_code,
                    calc_result["factors"],
                    calc_result["signals"],
                    calc_result["leaders"],
                    calc_result["memory"]
                )
                calc_result["report"] = report_result
                logger.info("✅ Agent 报告生成完成")

            logger.info(f"✅ 股票 {stock_code} 分析成功")
            return calc_result

        except Exception as e:
            logger.error(f"❌ 分析股票 {stock_code} 异常: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code
            }

    def quick_analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        快速分析（仅计算，不生成报告）

        Args:
            stock_code: 股票代码

        Returns:
            Dict: 简化的分析结果
        """
        logger.info(f"⚡ 快速分析股票: {stock_code}")

        try:
            result = self.pipeline.quick_analyze(stock_code)
            return result

        except Exception as e:
            logger.error(f"❌ 快速分析股票 {stock_code} 异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code
            }

    def get_stock_score(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """获取股票综合评分"""
        logger.debug(f"📊 获取股票评分: {stock_code}")

        try:
            result = self.pipeline.calculate_score(
                {"summary": {"overall_score": 50}},
                {"summary": {"overall_strength": 50}},
                {"leader_score": 50}
            )
            return {"score": result}

        except Exception as e:
            logger.error(f"❌ 获取股票评分异常: {e}")
            return None

    def get_top_stocks(self, limit: int = 10) -> List[Dict]:
        """获取评分最高的股票列表"""
        logger.debug(f"📈 获取 Top {limit} 股票")
        return []

    def get_stock_factors(self, stock_code: str, date: str = None) -> List[Dict]:
        """获取股票因子计算结果"""
        logger.debug(f"🔢 获取股票因子: {stock_code}")
        return []

    def get_stock_signals(self, stock_code: str, date: str = None) -> List[Dict]:
        """获取股票信号生成结果"""
        logger.debug(f"📡 获取股票信号: {stock_code}")
        return []

    def get_stock_leader_info(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """获取股票龙头识别结果"""
        logger.debug(f"🐉 获取股票龙头信息: {stock_code}")
        return None

    def get_stock_analysis(self, stock_code: str, date: str = None) -> Dict:
        """获取股票完整分析数据"""
        logger.debug(f"📋 获取股票完整分析: {stock_code}")
        return {}

    def get_market_summary(self, date: str = None) -> Dict:
        """获取市场整体摘要"""
        logger.debug(f"📊 获取市场摘要")
        return {}

    def set_mode(self, mode: str):
        """设置运行模式"""
        if mode in [self.MODE_ONLINE, self.MODE_REAL_TIME]:
            self.mode = mode
            self._pipeline = None
            logger.info(f"🔄 切换分析模式: {mode}")
        else:
            logger.warning(f"⚠️ 无效的模式: {mode}")


_analysis_service_instance = None

def get_analysis_service(mode: str = AnalysisService.MODE_ONLINE) -> AnalysisService:
    """获取分析服务单例"""
    global _analysis_service_instance
    if _analysis_service_instance is None:
        _analysis_service_instance = AnalysisService(mode)
    return _analysis_service_instance
