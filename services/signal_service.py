"""
Signal Service - 信号服务

V9 Service Layer 组件，提供信号相关的统一接口：
1. 信号查询
2. 信号验证
3. 信号统计
4. 信号可视化数据

核心原则：
- UI 不直接调用 SignalEngine，通过 Service Layer 访问
- 统一错误处理和日志记录
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SignalService:
    """
    信号服务
    
    提供信号相关的统一接口，隔离 UI 和底层 SignalEngine
    """
    
    def __init__(self):
        """初始化信号服务"""
        logger.info("🔧 初始化信号服务")
        
        # 延迟加载依赖
        self._data_service = None
        self._signal_engine = None
    
    @property
    def data_service(self):
        if self._data_service is None:
            from core.online_data_service import get_data_service
            self._data_service = get_data_service()
        return self._data_service
    
    @property
    def signal_engine(self):
        if self._signal_engine is None:
            from signals.signal_engine import SignalEngine
            self._signal_engine = SignalEngine()
        return self._signal_engine
    
    def get_stock_signals(self, stock_code: str, date: str = None) -> List[Dict]:
        """
        获取股票信号
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            List: 信号列表
        """
        logger.debug(f"📡 获取股票 {stock_code} 的信号")
        
        try:
            signals = self.data_service.get_signal_results(stock_code, date)
            return signals
        
        except Exception as e:
            logger.error(f"❌ 获取股票信号失败: {e}")
            return []
    
    def get_all_signals(self, date: str = None) -> Dict[str, List[Dict]]:
        """
        获取所有股票的信号
        
        Args:
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 股票代码到信号列表的映射
        """
        logger.debug(f"📡 获取所有股票的信号")
        
        try:
            # 获取所有有评分的股票
            from core.csv_provider import CSVProvider
            provider = CSVProvider()
            stock_codes = provider.get_all_stock_codes()
            
            result = {}
            for stock_code in stock_codes:
                signals = self.get_stock_signals(stock_code, date)
                if signals:
                    result[stock_code] = signals
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取所有信号失败: {e}")
            return {}
    
    def get_signal_summary(self, stock_code: str, date: str = None) -> Dict:
        """
        获取股票信号摘要
        
        Args:
            stock_code: 股票代码
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 信号摘要
        """
        signals = self.get_stock_signals(stock_code, date)
        
        if not signals:
            return {
                "stock_code": stock_code,
                "signal_count": 0,
                "strong_signals": [],
                "weak_signals": [],
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "overall_strength": 0
            }
        
        # 统计信号
        strong_signals = [s for s in signals if s.get("strength", 0) >= 70]
        weak_signals = [s for s in signals if s.get("strength", 0) < 50]
        
        bullish_count = len([s for s in signals if s.get("direction") == "bullish"])
        bearish_count = len([s for s in signals if s.get("direction") == "bearish"])
        neutral_count = len([s for s in signals if s.get("direction") == "neutral"])
        
        avg_strength = sum(s.get("strength", 0) for s in signals) / len(signals) if signals else 0
        
        return {
            "stock_code": stock_code,
            "signal_count": len(signals),
            "strong_signals": strong_signals,
            "weak_signals": weak_signals,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "overall_strength": round(avg_strength, 1)
        }
    
    def get_signals_by_type(self, signal_type: str, date: str = None) -> List[Dict]:
        """
        按信号类型获取所有股票的信号
        
        Args:
            signal_type: 信号类型（breakout/reversal/trend/volume）
            date: 查询日期（默认今日）
        
        Returns:
            List: 符合条件的信号列表
        """
        logger.debug(f"📡 获取类型为 {signal_type} 的信号")
        
        try:
            all_signals = self.get_all_signals(date)
            
            result = []
            for stock_code, signals in all_signals.items():
                for signal in signals:
                    if signal.get("signal_type") == signal_type:
                        signal["stock_code"] = stock_code
                        result.append(signal)
            
            # 按强度排序
            result.sort(key=lambda x: x.get("strength", 0), reverse=True)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 按类型获取信号失败: {e}")
            return []
    
    def get_strong_signals(self, min_strength: int = 70, date: str = None) -> List[Dict]:
        """
        获取强信号（强度>=阈值）
        
        Args:
            min_strength: 最小强度阈值（默认70）
            date: 查询日期（默认今日）
        
        Returns:
            List: 强信号列表
        """
        logger.debug(f"📡 获取强度 >= {min_strength} 的强信号")
        
        try:
            all_signals = self.get_all_signals(date)
            
            result = []
            for stock_code, signals in all_signals.items():
                for signal in signals:
                    if signal.get("strength", 0) >= min_strength:
                        signal["stock_code"] = stock_code
                        result.append(signal)
            
            # 按强度排序
            result.sort(key=lambda x: x.get("strength", 0), reverse=True)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 获取强信号失败: {e}")
            return []
    
    def validate_signal(self, stock_code: str, signal_type: str, date: str = None) -> Dict:
        """
        验证信号有效性
        
        Args:
            stock_code: 股票代码
            signal_type: 信号类型
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 验证结果
        """
        logger.debug(f"🔍 验证股票 {stock_code} 的 {signal_type} 信号")
        
        try:
            signals = self.get_stock_signals(stock_code, date)
            
            for signal in signals:
                if signal.get("signal_type") == signal_type:
                    return {
                        "stock_code": stock_code,
                        "signal_type": signal_type,
                        "valid": True,
                        "strength": signal.get("strength", 0),
                        "direction": signal.get("direction", "neutral"),
                        "description": signal.get("description", "")
                    }
            
            return {
                "stock_code": stock_code,
                "signal_type": signal_type,
                "valid": False,
                "reason": "未找到该类型信号"
            }
        
        except Exception as e:
            logger.error(f"❌ 验证信号失败: {e}")
            return {
                "stock_code": stock_code,
                "signal_type": signal_type,
                "valid": False,
                "reason": str(e)
            }
    
    def get_signal_statistics(self, date: str = None) -> Dict:
        """
        获取信号统计信息
        
        Args:
            date: 查询日期（默认今日）
        
        Returns:
            Dict: 信号统计
        """
        logger.debug(f"📊 获取信号统计")
        
        try:
            all_signals = self.get_all_signals(date)
            
            total_signals = 0
            total_stocks = len(all_signals)
            strong_count = 0
            bullish_count = 0
            bearish_count = 0
            
            signal_type_dist = {}
            
            for stock_code, signals in all_signals.items():
                total_signals += len(signals)
                
                for signal in signals:
                    # 统计信号类型分布
                    sig_type = signal.get("signal_type", "unknown")
                    signal_type_dist[sig_type] = signal_type_dist.get(sig_type, 0) + 1
                    
                    # 统计强度
                    if signal.get("strength", 0) >= 70:
                        strong_count += 1
                    
                    # 统计方向
                    direction = signal.get("direction", "neutral")
                    if direction == "bullish":
                        bullish_count += 1
                    elif direction == "bearish":
                        bearish_count += 1
            
            return {
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "total_stocks": total_stocks,
                "total_signals": total_signals,
                "avg_signals_per_stock": round(total_signals / total_stocks, 2) if total_stocks > 0 else 0,
                "strong_signals": strong_count,
                "bullish_signals": bullish_count,
                "bearish_signals": bearish_count,
                "signal_type_distribution": signal_type_dist,
                "bullish_ratio": round(bullish_count / total_signals * 100, 1) if total_signals > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"❌ 获取信号统计失败: {e}")
            return {}
    
    def get_today_breakouts(self, min_strength: int = 70, date: str = None) -> List[Dict]:
        """
        获取今日突破信号
        
        Args:
            min_strength: 最小强度阈值（默认70）
            date: 查询日期（默认今日）
        
        Returns:
            List: 突破信号列表
        """
        logger.debug(f"📈 获取今日突破信号")
        
        try:
            breakout_signals = self.get_signals_by_type("breakout", date)
            
            strong_breakouts = [
                s for s in breakout_signals 
                if s.get("strength", 0) >= min_strength
            ]
            
            return strong_breakouts
        
        except Exception as e:
            logger.error(f"❌ 获取今日突破信号失败: {e}")
            return []
    
    def get_watchlist(self, min_score: int = 70, limit: int = 20) -> List[Dict]:
        """
        获取关注列表（高分且有强信号的股票）
        
        Args:
            min_score: 最小综合评分
            limit: 返回数量限制
        
        Returns:
            List: 关注列表
        """
        logger.debug(f"📋 获取关注列表")
        
        try:
            from core.online_data_service import get_data_service
            data_service = get_data_service()
            top_stocks = data_service.get_top_stocks(limit=100)
            
            watchlist = []
            for stock in top_stocks:
                if stock.get("overall_score", 0) >= min_score:
                    stock_code = stock.get("stock_code")
                    
                    signals = self.get_stock_signals(stock_code)
                    has_strong_signal = any(s.get("strength", 0) >= 70 for s in signals)
                    
                    watchlist.append({
                        "stock_code": stock_code,
                        "overall_score": stock.get("overall_score"),
                        "has_strong_signal": has_strong_signal,
                        "signal_count": len(signals),
                        "risk_level": stock.get("risk_level")
                    })
                    
                    if len(watchlist) >= limit:
                        break
            
            watchlist.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
            
            return watchlist
        
        except Exception as e:
            logger.error(f"❌ 获取关注列表失败: {e}")
            return []


_signal_service_instance = None

def get_signal_service() -> SignalService:
    """获取信号服务单例"""
    global _signal_service_instance
    if _signal_service_instance is None:
        _signal_service_instance = SignalService()
    return _signal_service_instance
