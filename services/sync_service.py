"""
Sync Service - 同步服务

V9 Service Layer 组件，提供数据同步相关的统一接口：
1. 股票数据同步
2. 市场情绪同步
3. 离线计算任务触发
4. 数据更新状态查询

核心原则：
- UI 不直接调用 DataSyncManager/OfflineCalculator，通过 Service Layer 访问
- 统一错误处理和日志记录
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SyncService:
    """
    同步服务
    
    提供数据同步相关的统一接口，隔离 UI 和底层同步引擎
    """
    
    def __init__(self):
        """初始化同步服务"""
        logger.info("🔧 初始化同步服务")
        
        # 延迟加载依赖
        self._sync_manager = None
        self._calculator = None
        self._task_scheduler = None
    
    @property
    def sync_manager(self):
        if self._sync_manager is None:
            from data_sync.data_sync_manager import DataSyncManager
            import os
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "cn", "daily")
            self._sync_manager = DataSyncManager(data_dir=data_dir)
        return self._sync_manager
    
    @property
    def calculator(self):
        if self._calculator is None:
            from core.offline_calculator import get_calculator
            self._calculator = get_calculator()
        return self._calculator
    
    @property
    def task_scheduler(self):
        if self._task_scheduler is None:
            from core.task_scheduler import get_scheduler, init_daily_tasks
            self._task_scheduler = get_scheduler()
            init_daily_tasks()
        return self._task_scheduler
    
    def sync_stock_data(self, stock_code: str, end_date: str = None) -> Dict:
        """
        同步单只股票的数据
        
        Args:
            stock_code: 股票代码
            end_date: 结束日期（默认今日）
        
        Returns:
            Dict: 同步结果
        """
        logger.info(f"📥 同步股票 {stock_code} 的数据")
        
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            success, message, count = self.sync_manager.update_stock_incremental(stock_code, end_date)
            
            return {
                "success": success,
                "message": message,
                "count": count,
                "stock_code": stock_code
            }
        
        except Exception as e:
            logger.error(f"❌ 同步股票数据失败: {e}")
            return {
                "success": False,
                "message": str(e),
                "stock_code": stock_code
            }
    
    def sync_all_stocks(self, progress_callback=None) -> Dict:
        """
        同步所有股票的数据
        
        Args:
            progress_callback: 进度回调函数
        
        Returns:
            Dict: 同步结果统计
        """
        logger.info("📥 同步所有股票的数据")
        
        try:
            result = self.sync_manager.sync_all_full(progress_callback=progress_callback)
            
            logger.info(f"✅ 全量同步完成！成功: {result['success']}, 失败: {result['failed']}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 同步所有股票数据失败: {e}")
            return {
                "success": 0,
                "failed": 0,
                "error": str(e)
            }
    
    def get_sync_status(self) -> Dict:
        """
        获取同步状态
        
        Returns:
            Dict: 同步状态信息
        """
        logger.debug(f"📊 获取同步状态")
        
        try:
            existing_count = self.sync_manager.get_existing_stocks_count()
            
            return {
                "existing_stocks": existing_count,
                "last_sync_time": self._get_last_sync_time(),
                "sync_running": False  # 可以扩展为实际检测
            }
        
        except Exception as e:
            logger.error(f"❌ 获取同步状态失败: {e}")
            return {}
    
    def run_factor_calculation(self, stock_codes: List[str] = None) -> Dict:
        """
        运行因子计算
        
        Args:
            stock_codes: 股票代码列表（不传则计算所有）
        
        Returns:
            Dict: 计算结果统计
        """
        logger.info("🔢 运行因子计算")
        
        try:
            from core.csv_provider import CSVProvider
            provider = CSVProvider()
            
            if stock_codes is None:
                stock_codes = provider.get_all_stock_codes()
            
            result = self.calculator.batch_process_stocks(stock_codes, provider)
            
            logger.info(f"✅ 因子计算完成！成功: {result['success']}, 失败: {result['failed']}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 运行因子计算失败: {e}")
            return {
                "success": 0,
                "failed": 0,
                "error": str(e)
            }
    
    def run_single_stock_calculation(self, stock_code: str) -> Dict:
        """
        计算单只股票的因子
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Dict: 计算结果
        """
        logger.info(f"🔢 计算股票 {stock_code} 的因子")
        
        try:
            from core.csv_provider import CSVProvider
            provider = CSVProvider()
            
            df = provider.get_stock_daily(stock_code)
            
            if df is None or df.empty:
                return {
                    "success": False,
                    "error": "无法获取股票数据",
                    "stock_code": stock_code
                }
            
            result = self.calculator.process_stock(stock_code, df)
            
            return {
                "success": True,
                "stock_code": stock_code,
                "overall_score": result.get("score", {}).get("overall_score", 0),
                "processed_at": result.get("processed_at")
            }
        
        except Exception as e:
            logger.error(f"❌ 计算股票因子失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code
            }
    
    def trigger_daily_tasks(self) -> Dict:
        """
        手动触发每日任务
        
        Returns:
            Dict: 任务执行结果
        """
        logger.info("🚀 手动触发每日任务")
        
        results = {}
        
        try:
            # 执行每日因子计算
            logger.info("📊 执行每日因子计算...")
            factor_result = self.task_scheduler.run_task_now("daily_factor_calculation")
            results["daily_factor_calculation"] = factor_result
            
            # 执行市场快照生成
            logger.info("📸 执行市场快照生成...")
            snapshot_result = self.task_scheduler.run_task_now("daily_market_snapshot")
            results["daily_market_snapshot"] = snapshot_result
            
            # 执行市场结构分析
            logger.info("🧠 执行市场结构分析...")
            structure_result = self.task_scheduler.run_task_now("daily_market_structure_analysis")
            results["daily_market_structure_analysis"] = structure_result
            
            logger.info("✅ 所有每日任务执行完成")
            
            return {
                "success": True,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"❌ 触发每日任务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": results
            }
    
    def start_scheduler(self, block: bool = False):
        """
        启动任务调度器
        
        Args:
            block: 是否阻塞主线程
        """
        logger.info("🚀 启动任务调度器")
        
        try:
            self.task_scheduler.start(block=block)
            return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ 启动调度器失败: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_scheduler(self):
        """停止任务调度器"""
        logger.info("🛑 停止任务调度器")
        
        try:
            self.task_scheduler.stop()
            return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ 停止调度器失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_scheduler_status(self) -> Dict:
        """
        获取调度器状态
        
        Returns:
            Dict: 调度器状态
        """
        try:
            tasks = self.task_scheduler.get_tasks()
            
            return {
                "is_running": self.task_scheduler._is_running,
                "task_count": len(tasks),
                "tasks": list(tasks.keys())
            }
        
        except Exception as e:
            logger.error(f"❌ 获取调度器状态失败: {e}")
            return {}
    
    def _get_last_sync_time(self) -> Optional[str]:
        """获取最后同步时间"""
        try:
            # 检查数据目录中最新的文件
            import os
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "cn", "daily")
            
            if not os.path.exists(data_dir):
                return None
            
            latest_time = None
            
            for market_dir in os.listdir(data_dir):
                market_path = os.path.join(data_dir, market_dir)
                if os.path.isdir(market_path):
                    for filename in os.listdir(market_path):
                        if filename.endswith('.csv'):
                            file_path = os.path.join(market_path, filename)
                            mtime = os.path.getmtime(file_path)
                            if latest_time is None or mtime > latest_time:
                                latest_time = mtime
            
            if latest_time:
                return datetime.fromtimestamp(latest_time).strftime("%Y-%m-%d %H:%M:%S")
            
            return None
        
        except Exception as e:
            logger.error(f"❌ 获取最后同步时间失败: {e}")
            return None


# 全局单例
_sync_service_instance = None

def get_sync_service() -> SyncService:
    """获取同步服务单例"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = SyncService()
    return _sync_service_instance
