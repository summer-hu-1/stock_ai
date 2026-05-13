"""
Analysis Pipeline - 统一分析总线

这是整个系统的核心，负责将所有分析模块串联起来：
1. 数据加载 → 2. 因子计算 → 3. 信号生成 → 4. 龙头识别 → 5. 市场记忆 → 6. Agent分析 → 7. 综合评分

采用 Pipeline 驱动架构，而非 UI 驱动架构
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 导入核心模块
from core.csv_provider import CSVProvider
from factors.factor_engine import FactorEngine
from signals.signal_engine import SignalEngine
from leaders.leader_engine import LeaderEngine
from core.market_memory import MarketMemory
from agents.controller_agent import multi_agent_review


class AnalysisPipeline:
    """
    统一分析管线
    
    将所有分析模块串联成一个完整的分析流程
    """
    
    def __init__(self):
        """初始化管线"""
        logger.info("🔧 初始化分析管线...")
        
        # 初始化各子模块
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
            # 策略 1: 优先从本地 CSV 获取
            df = self.data_provider.get_stock_daily(stock_code, market)
            if df is not None and not df.empty:
                logger.info(f"✅ 从本地CSV加载 {len(df)} 条数据")
                return df
            
            # 策略 2: 本地没有，尝试从网络获取历史数据
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
            
            # 策略 3: 如果历史数据获取失败，尝试获取实时数据作为备选
            try:
                from modules.market_data import get_stock_data
                realtime_data = get_stock_data(stock_code, market)
                if realtime_data:
                    logger.info(f"✅ 获取到实时数据（但可能不足以进行完整分析）")
                    # 创建包含实时数据的简单DataFrame
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
        
        Args:
            stock_code: 股票代码
            market: 市场（cn/hk/us）
            use_cache: 是否使用缓存
        
        Returns:
            Dict: 包含所有分析结果的字典
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
            logger.info(f"✅ 因子计算完成，综合评分: {factors.get('summary', {}).get('overall_score', 0)}")
            
            # 3. 信号生成
            logger.info("📡 运行信号引擎...")
            signals = self.signal_engine.generate(df, factors)
            signal_count = len([s for s in signals.get('summary', {}).get('signals', []) if s.get('strength', 0) > 50])
            logger.info(f"✅ 信号生成完成，有效信号: {signal_count}")
            
            # 4. 龙头识别
            logger.info("🐉 运行龙头引擎...")
            leaders = self.leader_engine.analyze(df, factors, signals)
            logger.info(f"✅ 龙头识别完成，是否龙头: {leaders.get('is_leader', False)}")
            
            # 5. 市场记忆
            logger.info("🧠 获取市场记忆...")
            memory = self.market_memory.get_market_context(days=5)
            has_context = memory.get("has_context", False)
            logger.info(f"✅ 市场记忆获取完成，有历史数据: {has_context}")
            
            # 6. Agent分析
            logger.info("🤖 运行Agent分析...")
            agent_result = self._run_agent_analysis(stock_code, factors, signals, leaders, memory)
            logger.info(f"✅ Agent分析完成")
            
            # 7. 综合评分
            logger.info("📈 计算综合评分...")
            final_score = self.calculate_score(factors, signals, leaders)
            logger.info(f"✅ 综合评分: {final_score}")
            
            # 计算耗时
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
                "agent": agent_result,
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
    
    def _run_agent_analysis(self, stock_code: str, factors: Dict, signals: Dict, leaders: Dict, memory: Dict) -> Dict:
        """
        运行Agent分析（封装，便于后续扩展）
        
        Args:
            stock_code: 股票代码
            factors: 因子结果
            signals: 信号结果
            leaders: 龙头结果
            memory: 市场记忆
        
        Returns:
            Dict: Agent分析结果
        """
        try:
            # 获取市场上下文文本
            market_context = self.market_memory.format_market_context(days=5)
            
            # 准备输入数据
            analysis_input = {
                "stock_code": stock_code,
                "factors": factors,
                "signals": signals,
                "leaders": leaders,
                "market_context": market_context
            }
            
            # 调用多Agent分析
            result = multi_agent_review(stock_code)
            
            return {
                "success": True,
                "data": result,
                "market_context": market_context
            }
        
        except Exception as e:
            logger.warning(f"⚠️ Agent分析失败（非致命）: {e}")
            return {
                "success": False,
                "error": str(e),
                "market_context": memory
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
            # 因子评分（0-100）
            factor_score = factors.get('summary', {}).get('overall_score', 50)
            
            # 信号评分（0-100）
            signal_summary = signals.get('summary', {})
            signal_score = signal_summary.get('overall_strength', 50)
            
            # 龙头评分（0-100）
            leader_score = leaders.get('leader_score', 50)
            
            # 综合评分
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
        快速分析（简化版，只返回关键结果）
        
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


# 全局单例
_pipeline_instance = None

def get_pipeline() -> AnalysisPipeline:
    """获取分析管线单例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = AnalysisPipeline()
    return _pipeline_instance
