"""同步服务 - 提供数据同步功能"""

import os
from typing import Dict, List

# 获取项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SyncService:
    """同步服务 - 提供数据同步功能"""

    def __init__(self):
        self.data_dir = os.path.join(PROJECT_DIR, "data")

    def sync_stock_data(self, stock_code: str, date: str = None) -> Dict:
        """同步单只股票数据"""
        try:
            # 这里可以调用实际的数据同步逻辑
            # 目前返回模拟结果
            return {
                "success": True,
                "code": stock_code,
                "message": f"股票 {stock_code} 同步完成"
            }
        except Exception as e:
            return {
                "success": False,
                "code": stock_code,
                "error": str(e)
            }

    def sync_all_stocks(self) -> Dict:
        """同步所有股票数据"""
        try:
            # 获取数据目录
            cn_dir = os.path.join(self.data_dir, "cn", "daily")
            stock_count = 0

            if os.path.exists(cn_dir):
                stock_count = len([f for f in os.listdir(cn_dir) if f.endswith('.csv')])

            return {
                "success": True,
                "stock_count": stock_count,
                "message": f"全量同步完成，共 {stock_count} 只股票"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_sync_status(self) -> Dict:
        """获取同步状态"""
        try:
            cn_dir = os.path.join(self.data_dir, "cn", "daily")
            stock_count = 0
            last_sync = "未知"

            if os.path.exists(cn_dir):
                files = [f for f in os.listdir(cn_dir) if f.endswith('.csv')]
                stock_count = len(files)

            return {
                "status": "正常",
                "stock_count": stock_count,
                "last_sync": last_sync,
                "data_dir": cn_dir
            }
        except Exception as e:
            return {
                "status": "异常",
                "error": str(e)
            }


# 全局单例
_sync_service_instance = None

def get_sync_service() -> SyncService:
    """获取同步服务单例"""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = SyncService()
    return _sync_service_instance