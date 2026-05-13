"""
Analysis Service - 分析服务

V9 Service Layer 的核心组件，提供统一的分析接口：
1. 股票分析（在线/实时模式）
2. 因子计算
3. 信号生成
4. 龙头识别
5. 综合评分

核心原则：
- UI 不直接调用 Engine，通过 Service Layer 访问
- 统一错误处理和日志记录
- 支持在线/实时两种模式
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AnalysisService:
    """
    分析服务
    
    提供统一的分析接口，隔离 UI 和底层 Engine
    """
    
    MODE_ONLINE = "online"
    MODE_REAL_TIME = "realtime"
    
    def __init__(self, mode: str = MODE_ONLINE):
        """
        初始化分析服务
        
        Args:
            mode: 运行模式（online/realtime）
        """
        logger.info(f"🔧 初始化分析服务（模式: {mode}）")
        self.mode = mode
        
        # 延迟加载依赖，避免循环导入
        self._pipeline = None
        self._data_service = None
    
    @property
    def pipeline(self):
        if self._pipeline is None:
            from core.analysis_pipeline import get_pipeline
            self._pipeline = get_pipeline()
        return self._pipeline
    
    @property
    def data_service(self):
        if self._data_service is None:
            from core.online_data_service import get_data_service
            self._data_service = get_data_service()
        return self._data_service
    
    def analyze_stock(self, stock_code: str, market: str = "cn") -> Dict[str, Any]:
        """
        分析单只股票
        
        Args:
            stock_code: 股票代码
            market: 市场（cn/hk/us）
        
        Returns:
            Dict: 分析结果
        """
        logger.info(f"🚀 分析股票: {stock_code}")
        
        try:
            result = self.pipeline.analyze(stock_code, market)
            
            if result.get("success"):
                logger.info(f"✅ 股票 {stock_code} 分析成功")
            else:
                logger.warning(f"⚠️ 股票 {stock_code} 分析失败: {result.get('error')}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 分析股票 {stock_code} 异常: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code
            }
    
    def quick_analyze(self, stock_code: str) -> Dict[str, Any]:
        """
        快速分析（简化版）
        
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
    
    def analyze_market_structure(self, days: int = 5) -> Dict[str, Any]:
        """
        分析市场结构
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场结构分析结果
        """
        logger.info(f"🧠 分析市场结构（最近{days}天）")
        
        try:
            result = self.pipeline.analyze_market_structure(days)
            return result
        
        except Exception as e:
            logger.error(f"❌ 分析市场结构异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_market_insight(self, days: int = 5) -> Dict[str, Any]:
        """
        生成市场洞察
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场洞察结果
        """
        logger.info(f"🤖 生成市场洞察（最近{days}天）")
        
        try:
            result = self.pipeline.generate_market_insight(days)
            return result
        
        except Exception as e:
            logger.error(f"❌ 生成市场洞察异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stock_score(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """
        获取股票综合评分
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 综合评分数据
        """
        logger.debug(f"📊 获取股票评分: {stock_code}")
        
        try:
            result = self.data_service.get_stock_score(stock_code, date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取股票评分异常: {e}")
            return None
    
    def get_top_stocks(self, limit: int = 10) -> List[Dict]:
        """
        获取评分最高的股票列表
        
        Args:
            limit: 返回数量限制
        
        Returns:
            List: 股票评分列表
        """
        logger.debug(f"📈 获取 Top {limit} 股票")
        
        try:
            result = self.data_service.get_top_stocks(limit=limit)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取Top股票异常: {e}")
            return []
    
    def get_stock_factors(self, stock_code: str, date: str = None) -> List[Dict]:
        """
        获取股票因子计算结果
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            List: 因子结果列表
        """
        logger.debug(f"🔢 获取股票因子: {stock_code}")
        
        try:
            result = self.data_service.get_factor_results(stock_code, date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取股票因子异常: {e}")
            return []
    
    def get_stock_signals(self, stock_code: str, date: str = None) -> List[Dict]:
        """
        获取股票信号生成结果
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            List: 信号结果列表
        """
        logger.debug(f"📡 获取股票信号: {stock_code}")
        
        try:
            result = self.data_service.get_signal_results(stock_code, date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取股票信号异常: {e}")
            return []
    
    def get_stock_leader_info(self, stock_code: str, date: str = None) -> Optional[Dict]:
        """
        获取股票龙头识别结果
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 龙头识别结果
        """
        logger.debug(f"🐉 获取股票龙头信息: {stock_code}")
        
        try:
            result = self.data_service.get_leader_results(stock_code, date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取股票龙头信息异常: {e}")
            return None
    
    def get_stock_analysis(self, stock_code: str, date: str = None) -> Dict:
        """
        获取股票完整分析数据
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 完整分析数据
        """
        logger.debug(f"📋 获取股票完整分析: {stock_code}")
        
        try:
            result = self.data_service.get_stock_analysis(stock_code, date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取股票完整分析异常: {e}")
            return {}
    
    def get_market_summary(self, date: str = None) -> Dict:
        """
        获取市场整体摘要
        
        Args:
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 市场摘要数据
        """
        logger.debug(f"📊 获取市场摘要")
        
        try:
            result = self.data_service.get_market_summary(date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取市场摘要异常: {e}")
            return {}
    
    def set_mode(self, mode: str):
        """
        设置运行模式
        
        Args:
            mode: 运行模式（online/realtime）
        """
        if mode in [self.MODE_ONLINE, self.MODE_REAL_TIME]:
            self.mode = mode
            # 重置 pipeline 实例
            self._pipeline = None
            logger.info(f"🔄 切换分析模式: {mode}")
        else:
            logger.warning(f"⚠️ 无效的模式: {mode}")


# 全局单例
_analysis_service_instance = None

def get_analysis_service(mode: str = AnalysisService.MODE_ONLINE) -> AnalysisService:
    """获取分析服务单例"""
    global _analysis_service_instance
    if _analysis_service_instance is None:
        _analysis_service_instance = AnalysisService(mode)
    return _analysis_service_instance
