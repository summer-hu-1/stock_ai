"""
Market Service - 市场服务

V9 Service Layer 组件，提供市场相关的统一接口：
1. 市场情绪查询
2. 市场快照管理
3. 市场结构分析
4. 市场洞察生成
5. 龙头股票管理

核心原则：
- UI 不直接调用 MarketMemory/MarketStateEngine，通过 Service Layer 访问
- 统一错误处理和日志记录
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MarketService:
    """
    市场服务
    
    提供市场相关的统一接口，隔离 UI 和底层市场引擎
    """
    
    def __init__(self):
        """初始化市场服务"""
        logger.info("🔧 初始化市场服务")
        
        # 延迟加载依赖
        self._market_memory = None
        self._structure_engine = None
        self._data_service = None
    
    @property
    def market_memory(self):
        if self._market_memory is None:
            from core.market_memory import MarketMemory
            self._market_memory = MarketMemory()
        return self._market_memory
    
    @property
    def structure_engine(self):
        if self._structure_engine is None:
            from core.market_structure_engine import get_market_structure_engine
            self._structure_engine = get_market_structure_engine()
        return self._structure_engine
    
    @property
    def data_service(self):
        if self._data_service is None:
            from core.online_data_service import get_data_service
            self._data_service = get_data_service()
        return self._data_service
    
    def get_market_context(self, days: int = 5) -> Dict:
        """
        获取市场上下文
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场上下文
        """
        logger.debug(f"🧠 获取市场上下文（最近{days}天）")
        
        try:
            context = self.market_memory.get_market_context(days)
            return context
        
        except Exception as e:
            logger.error(f"❌ 获取市场上下文失败: {e}")
            return {"has_context": False, "message": str(e)}
    
    def get_market_snapshot(self, date: str = None) -> Optional[Dict]:
        """
        获取市场快照
        
        Args:
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 市场快照数据
        """
        logger.debug(f"📸 获取市场快照")
        
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            snapshot = self.market_memory.get_snapshot_by_date(date)
            
            if snapshot:
                return snapshot.to_dict()
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取市场快照失败: {e}")
            return None
    
    def get_recent_snapshots(self, days: int = 30) -> List[Dict]:
        """
        获取最近N天的市场快照
        
        Args:
            days: 天数
        
        Returns:
            List: 市场快照列表
        """
        logger.debug(f"📸 获取最近{days}天的市场快照")
        
        try:
            snapshots = self.market_memory.get_recent_snapshots(days)
            return [s.to_dict() for s in snapshots]
        
        except Exception as e:
            logger.error(f"❌ 获取最近快照失败: {e}")
            return []
    
    def save_market_snapshot(self, sentiment: Dict) -> bool:
        """
        保存市场快照
        
        Args:
            sentiment: 市场情绪数据
        
        Returns:
            bool: 是否成功
        """
        logger.info("📸 保存市场快照")
        
        try:
            success = self.market_memory.save_snapshot(sentiment)
            
            if success:
                logger.info("✅ 市场快照保存成功")
            else:
                logger.warning("⚠️ 市场快照保存失败")
            
            return success
        
        except Exception as e:
            logger.error(f"❌ 保存市场快照失败: {e}")
            return False
    
    def fetch_historical_snapshots(self, start_date: str, end_date: str) -> Dict:
        """
        拉取历史快照
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            Dict: 拉取结果统计
        """
        logger.info(f"📥 拉取历史快照: {start_date} 至 {end_date}")
        
        try:
            result = self.market_memory.fetch_date_range(start_date, end_date)
            return result
        
        except Exception as e:
            logger.error(f"❌ 拉取历史快照失败: {e}")
            return {"success": 0, "failed": 0, "skipped": 0}
    
    def update_missing_snapshots(self, days: int = 30) -> Dict:
        """
        增量更新缺失的快照
        
        Args:
            days: 最近N天
        
        Returns:
            Dict: 更新结果统计
        """
        logger.info(f"🔄 增量更新最近{days}天的快照")
        
        try:
            result = self.market_memory.update_missing_snapshots(days)
            return result
        
        except Exception as e:
            logger.error(f"❌ 增量更新快照失败: {e}")
            return {"total_missing": 0, "success": 0, "failed": 0}
    
    def analyze_market_structure(self, days: int = 5) -> Dict:
        """
        分析市场结构
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场结构分析结果
        """
        logger.info(f"🧠 分析市场结构（最近{days}天）")
        
        try:
            structure = self.structure_engine.analyze_market_structure(days)
            return structure
        
        except Exception as e:
            logger.error(f"❌ 分析市场结构失败: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_market_insight(self, days: int = 5) -> Dict:
        """
        生成市场洞察
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场洞察结果
        """
        logger.info(f"🤖 生成市场洞察（最近{days}天）")
        
        try:
            insight = self.market_memory.generate_market_insight(days)
            
            if insight:
                # 保存洞察
                self.market_memory.save_insight(insight)
                
                return {
                    "success": True,
                    "insight": {
                        "date": insight.date,
                        "current_state": insight.current_state,
                        "state_description": insight.state_description,
                        "trend_analysis": insight.trend_analysis,
                        "risk_alert": insight.risk_alert,
                        "opportunity": insight.opportunity,
                        "action_suggestion": insight.action_suggestion,
                        "confidence": insight.confidence
                    }
                }
            
            return {"success": False, "error": "未能生成洞察"}
        
        except Exception as e:
            logger.error(f"❌ 生成市场洞察失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_latest_insight(self) -> Optional[Dict]:
        """
        获取最新的市场洞察
        
        Returns:
            Dict: 最新市场洞察
        """
        logger.debug(f"📊 获取最新市场洞察")
        
        try:
            insight = self.market_memory.get_latest_insight()
            
            if insight:
                return {
                    "date": insight.date,
                    "current_state": insight.current_state,
                    "state_description": insight.state_description,
                    "trend_analysis": insight.trend_analysis,
                    "risk_alert": insight.risk_alert,
                    "opportunity": insight.opportunity,
                    "action_suggestion": insight.action_suggestion,
                    "confidence": insight.confidence,
                    "key_changes": insight.key_changes
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取最新洞察失败: {e}")
            return None
    
    def get_recent_insights(self, days: int = 30) -> List[Dict]:
        """
        获取最近N天的市场洞察
        
        Args:
            days: 天数
        
        Returns:
            List: 市场洞察列表
        """
        logger.debug(f"📊 获取最近{days}天的市场洞察")
        
        try:
            insights = self.market_memory.get_recent_insights(days)
            
            result = []
            for insight in insights:
                result.append({
                    "date": insight.date,
                    "current_state": insight.current_state,
                    "state_description": insight.state_description,
                    "risk_alert": insight.risk_alert,
                    "action_suggestion": insight.action_suggestion,
                    "confidence": insight.confidence
                })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取最近洞察失败: {e}")
            return []
    
    def get_all_leaders(self, date: str = None) -> List[Dict]:
        """
        获取所有龙头股票
        
        Args:
            date: 查询日期（默认今日）
        
        Returns:
            List: 龙头股票列表
        """
        logger.debug(f"🐉 获取所有龙头股票")
        
        try:
            leaders = self.data_service.get_all_leaders(date)
            return leaders
        
        except Exception as e:
            logger.error(f"❌ 获取龙头股票失败: {e}")
            return []
    
    def get_market_summary(self, date: str = None) -> Dict:
        """
        获取市场摘要
        
        Args:
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 市场摘要数据
        """
        logger.debug(f"📊 获取市场摘要")
        
        try:
            summary = self.data_service.get_market_summary(date)
            
            # 补充市场记忆数据
            snapshot = self.get_market_snapshot(date)
            if snapshot:
                summary.update({
                    "market_sentiment": snapshot.get("market_sentiment"),
                    "emotion_score": snapshot.get("emotion_score"),
                    "limit_up_count": snapshot.get("limit_up_count"),
                    "limit_down_count": snapshot.get("limit_down_count")
                })
            
            return summary
        
        except Exception as e:
            logger.error(f"❌ 获取市场摘要失败: {e}")
            return {}
    
    def get_market_cycle(self, days: int = 5) -> Dict:
        """
        获取市场周期信息
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场周期信息
        """
        logger.debug(f"🔄 获取市场周期")
        
        try:
            context = self.market_memory.get_market_context(days)
            
            if not context.get("has_context"):
                return {
                    "cycle": "未知",
                    "stage": "未知",
                    "description": "数据不足"
                }
            
            market_cycle = context.get("market_cycle", {})
            
            return {
                "cycle": market_cycle.get("cycle", "未知"),
                "stage": market_cycle.get("stage", "未知"),
                "description": market_cycle.get("description", ""),
                "limit_up": market_cycle.get("limit_up", 0),
                "emotion_score": market_cycle.get("emotion_score", 0),
                "bomb_rate": market_cycle.get("bomb_rate", 0)
            }
        
        except Exception as e:
            logger.error(f"❌ 获取市场周期失败: {e}")
            return {"cycle": "未知", "stage": "未知", "description": str(e)}
    
    def get_sector_rotation(self, days: int = 7) -> Dict:
        """
        获取板块轮动信息
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 板块轮动信息
        """
        logger.debug(f"🔄 获取板块轮动")
        
        try:
            context = self.market_memory.get_market_context(days)
            
            if not context.get("has_context"):
                return {
                    "has_rotation": False,
                    "description": "数据不足"
                }
            
            sector_rotation = context.get("sector_rotation", {})
            
            return {
                "has_rotation": sector_rotation.get("has_rotation", False),
                "rotation_from": sector_rotation.get("rotation_from"),
                "rotation_to": sector_rotation.get("rotation_to"),
                "description": sector_rotation.get("description", ""),
                "rotation_history": sector_rotation.get("rotation_history", {})
            }
        
        except Exception as e:
            logger.error(f"❌ 获取板块轮动失败: {e}")
            return {"has_rotation": False, "description": str(e)}
    
    def get_leader_rotation(self, days: int = 5) -> Dict:
        """
        获取龙头切换信息
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 龙头切换信息
        """
        logger.debug(f"🐉 获取龙头切换")
        
        try:
            context = self.market_memory.get_market_context(days)
            
            if not context.get("has_context"):
                return {
                    "has_rotation": False,
                    "description": "数据不足"
                }
            
            leader_rotation = context.get("leader_rotation", {})
            
            return {
                "has_rotation": leader_rotation.get("has_rotation", False),
                "description": leader_rotation.get("description", ""),
                "rotation_history": leader_rotation.get("rotation_history", [])
            }
        
        except Exception as e:
            logger.error(f"❌ 获取龙头切换失败: {e}")
            return {"has_rotation": False, "description": str(e)}
    
    def get_emotion_trend(self, days: int = 5) -> Dict:
        """
        获取情绪趋势信息
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 情绪趋势信息
        """
        logger.debug(f"😊 获取情绪趋势")
        
        try:
            context = self.market_memory.get_market_context(days)
            
            if not context.get("has_context"):
                return {
                    "direction": "未知",
                    "description": "数据不足"
                }
            
            emotion_trend = context.get("emotion_trend", {})
            
            return {
                "direction": emotion_trend.get("direction", "未知"),
                "description": emotion_trend.get("description", ""),
                "trend": emotion_trend.get("trend", []),
                "change_rate": emotion_trend.get("change_rate", 0)
            }
        
        except Exception as e:
            logger.error(f"❌ 获取情绪趋势失败: {e}")
            return {"direction": "未知", "description": str(e)}

_market_service_instance = None

def get_market_service() -> MarketService:
    """获取市场服务单例"""
    global _market_service_instance
    if _market_service_instance is None:
        _market_service_instance = MarketService()
    return _market_service_instance
