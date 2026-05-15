"""
Analysis Service - 分析服务

V10 Service Layer 的核心组件，提供统一的分析接口：
1. Pipeline 计算（因子、信号、龙头、评分）
2. ReportService 报告生成（Agent 解释）

V10 架构原则：
- Pipeline 负责"算"
- ReportService 负责"解释"
- Service 统一封装，屏蔽复杂度
- 使用新的 QuantCore 量化引擎
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AnalysisService:
    """
    分析服务

    V10 架构下统一入口，使用新的 QuantCore 量化引擎
    """

    MODE_ONLINE = "online"
    MODE_REAL_TIME = "realtime"

    def __init__(self, mode: str = MODE_ONLINE):
        logger.info(f"🔧 初始化分析服务（模式: {mode}）")
        self.mode = mode
        self._factor_engine = None
        self._signal_engine = None
        self._state_engine = None
        self._score_engine = None
        self._report_service = None

    @property
    def factor_engine(self):
        """获取因子计算引擎"""
        if self._factor_engine is None:
            from quant.factor.engine import FactorEngine
            self._factor_engine = FactorEngine()
        return self._factor_engine

    @property
    def signal_engine(self):
        """获取信号生成引擎"""
        if self._signal_engine is None:
            from quant.signal.engine import SignalEngine
            self._signal_engine = SignalEngine()
        return self._signal_engine

    @property
    def state_engine(self):
        """获取市场状态引擎"""
        if self._state_engine is None:
            from quant.state.engine import StateEngine
            self._state_engine = StateEngine()
        return self._state_engine

    @property
    def score_engine(self):
        """获取评分引擎"""
        if self._score_engine is None:
            from quant.score.engine import ScoreEngine
            self._score_engine = ScoreEngine()
        return self._score_engine

    @property
    def report_service(self):
        """获取报告服务"""
        if self._report_service is None:
            from services.report_service import get_report_service
            self._report_service = get_report_service()
        return self._report_service

    def analyze_stock(self, stock_code: str, market: str = "cn", with_report: bool = False) -> Dict[str, Any]:
        """
        分析单只股票

        V10 架构：
        1. 使用 QuantCore 引擎进行计算
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
            # 获取股票K线数据
            df = self._get_stock_data(stock_code, market)
            if df is None or df.empty:
                logger.warning(f"⚠️ 股票 {stock_code} 数据获取失败")
                return {
                    "success": False,
                    "error": "无法获取股票数据",
                    "stock_code": stock_code
                }

            # 计算因子
            factors = self.factor_engine.calculate(df)

            # 生成信号
            signals = self.signal_engine.generate(df, factors)

            # 分析市场状态和龙头特征
            state_result = self.state_engine.analyze(df, factors, signals)

            # 计算综合评分
            score = self.score_engine.calculate(factors, signals, state_result)

            calc_result = {
                "success": True,
                "stock_code": stock_code,
                "market": market,
                "factors": factors,
                "signals": signals,
                "state": state_result,
                "score": score,
                "analysis_time": datetime.now().isoformat()
            }

            if with_report:
                logger.info("🤖 生成 Agent 报告...")
                report_result = self.report_service.generate_report(
                    stock_code,
                    factors,
                    signals,
                    state_result,
                    score
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
            df = self._get_stock_data(stock_code, "cn")
            if df is None or df.empty:
                return {
                    "success": False,
                    "error": "无法获取股票数据",
                    "stock_code": stock_code
                }

            factors = self.factor_engine.calculate(df)
            signals = self.signal_engine.generate(df, factors)
            state_result = self.state_engine.analyze(df, factors, signals)
            score = self.score_engine.calculate(factors, signals, state_result)

            return {
                "success": True,
                "stock_code": stock_code,
                "factors": factors.get("summary", {}),
                "signals": signals.get("summary", {}),
                "is_leader": state_result.get("is_leader", False),
                "leader_score": state_result.get("leader_score", 0),
                "score": score,
                "analysis_time": datetime.now().isoformat()
            }

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
            result = self.quick_analyze(stock_code)
            if result.get("success"):
                return {"score": result["score"]}
            return None

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
        try:
            df = self._get_stock_data(stock_code, "cn")
            if df is None or df.empty:
                return []
            factors = self.factor_engine.calculate(df)
            return factors
        except Exception as e:
            logger.error(f"❌ 获取股票因子异常: {e}")
            return []

    def get_stock_signals(self, stock_code: str, date: str = None) -> List[Dict]:
        """获取股票信号生成结果"""
        logger.debug(f"📡 获取股票信号: {stock_code}")
        try:
            df = self._get_stock_data(stock_code, "cn")
            if df is None or df.empty:
                return []
            factors = self.factor_engine.calculate(df)
            signals = self.signal_engine.generate(df, factors)
            return signals
        except Exception as e:
            logger.error(f"❌ 获取股票信号异常: {e}")
            return []

    def get_stock_leader_info(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """获取股票龙头识别结果"""
        logger.debug(f"🐉 获取股票龙头信息: {stock_code}")
        try:
            df = self._get_stock_data(stock_code, "cn")
            if df is None or df.empty:
                return None
            factors = self.factor_engine.calculate(df)
            signals = self.signal_engine.generate(df, factors)
            state_result = self.state_engine.analyze(df, factors, signals)
            return {
                "is_leader": state_result.get("is_leader", False),
                "leader_score": state_result.get("leader_score", 0),
                "leader_type": state_result.get("leader_type", "普通"),
                "leader_reasons": state_result.get("leader_reasons", []),
                "limit_up_info": state_result.get("limit_up_info", {})
            }
        except Exception as e:
            logger.error(f"❌ 获取股票龙头信息异常: {e}")
            return None

    def get_stock_analysis(self, stock_code: str, date: str = None) -> Dict:
        """获取股票完整分析数据"""
        logger.debug(f"📋 获取股票完整分析: {stock_code}")
        return self.analyze_stock(stock_code, "cn", with_report=False)

    def get_market_summary(self, date: str = None) -> Dict:
        """获取市场整体摘要"""
        logger.debug(f"📊 获取市场摘要")
        return {}

    def rank_stocks(self, stock_data_list: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
        """
        对股票进行龙头排名

        Args:
            stock_data_list: 股票数据列表，包含 code, name, df
            top_n: 返回前N名

        Returns:
            Dict: 排名结果
        """
        logger.debug(f"🏆 股票排名: {len(stock_data_list)} 只股票")
        return self.state_engine.rank_stocks(stock_data_list, top_n)

    def set_mode(self, mode: str):
        """设置运行模式"""
        if mode in [self.MODE_ONLINE, self.MODE_REAL_TIME]:
            self.mode = mode
            self._factor_engine = None
            self._signal_engine = None
            self._state_engine = None
            self._score_engine = None
            logger.info(f"🔄 切换分析模式: {mode}")
        else:
            logger.warning(f"⚠️ 无效的模式: {mode}")

    def _get_stock_data(self, stock_code: str, market: str) -> Optional[Any]:
        """获取股票K线数据"""
        try:
            from modules.market_data import get_stock_data
            df = get_stock_data(stock_code)
            return df
        except Exception as e:
            logger.error(f"❌ 获取股票数据失败: {e}")
            return None


_analysis_service_instance = None


def get_analysis_service(mode: str = AnalysisService.MODE_ONLINE) -> AnalysisService:
    """获取分析服务单例"""
    global _analysis_service_instance
    if _analysis_service_instance is None:
        _analysis_service_instance = AnalysisService(mode)
    return _analysis_service_instance
