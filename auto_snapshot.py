#!/usr/bin/env python3
"""
市场快照定时任务服务

功能：
1. 每天下午3:30（A股收盘后）自动生成市场快照
2. 支持手动触发
3. 记录执行日志
4. 支持后台运行

使用方法：
1. 手动执行一次：python auto_snapshot.py --run-now
2. 启动定时服务：python auto_snapshot.py --start-service
3. 查看日志：python auto_snapshot.py --show-log
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
from argparse import ArgumentParser

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from core.market_memory import MarketMemory
from modules.market_sentiment import get_market_sentiment


class AutoSnapshotService:
    """
    自动快照服务
    """
    
    def __init__(self):
        self.memory = MarketMemory()
        self.logger = self._init_logger()
        self.running = False
        
    def _init_logger(self):
        """初始化日志记录器"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger('auto_snapshot')
        logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'auto_snapshot.log'),
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def generate_snapshot(self):
        """生成市场快照"""
        try:
            self.logger.info("📸 开始生成市场快照...")
            
            # 获取市场情绪数据
            self.logger.info("🔄 获取市场情绪数据...")
            sentiment_data = get_market_sentiment(use_cache=False)
            
            if not sentiment_data:
                self.logger.error("❌ 无法获取市场情绪数据")
                return False
            
            # 生成并保存快照
            self.logger.info("💾 保存市场快照...")
            success = self.memory.save_snapshot(sentiment_data)
            
            if success:
                self.logger.info(f"✅ 市场快照生成成功")
                self.logger.info(f"   日期: {datetime.now().strftime('%Y-%m-%d')}")
                self.logger.info(f"   涨停家数: {sentiment_data.get('limit_up_count', 0)}")
                self.logger.info(f"   市场情绪: {sentiment_data.get('market_mood', '未知')}")
                return True
            else:
                self.logger.error("❌ 市场快照保存失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 生成市场快照失败: {str(e)}")
            return False
    
    def run_scheduled_task(self):
        """执行定时任务"""
        self.logger.info("⏰ 定时任务触发")
        self.generate_snapshot()
    
    def start_service(self):
        """启动定时服务"""
        self.logger.info("🚀 启动市场快照定时服务...")
        self.logger.info("📅 定时任务设置: 每天下午 15:30")
        
        # 设置定时任务（下午3:30）
        schedule.every().day.at("15:30").do(self.run_scheduled_task)
        
        self.running = True
        self.logger.info("✅ 服务已启动，按 Ctrl+C 停止")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("⏹️ 服务已停止")
            self.running = False
    
    def show_log(self, lines: int = 50):
        """显示日志"""
        log_file = os.path.join(os.path.dirname(__file__), 'logs', 'auto_snapshot.log')
        
        if not os.path.exists(log_file):
            print("📄 日志文件不存在")
            return
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.readlines()
            
        print(f"📄 最近 {min(lines, len(content))} 条日志:")
        print("-" * 80)
        for line in content[-lines:]:
            print(line.strip())


def main():
    parser = ArgumentParser(description='市场快照定时任务服务')
    parser.add_argument('--run-now', action='store_true', help='立即执行一次快照生成')
    parser.add_argument('--start-service', action='store_true', help='启动定时服务')
    parser.add_argument('--show-log', action='store_true', help='显示最近的日志')
    parser.add_argument('--log-lines', type=int, default=50, help='显示的日志行数')
    
    args = parser.parse_args()
    
    service = AutoSnapshotService()
    
    if args.run_now:
        print("🔄 立即执行快照生成...")
        success = service.generate_snapshot()
        sys.exit(0 if success else 1)
    
    elif args.start_service:
        service.start_service()
    
    elif args.show_log:
        service.show_log(args.log_lines)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
