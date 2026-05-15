"""
调度器模块 - Scheduler

负责：
1. 每天收盘后更新市场数据
2. 执行量化因子计算
3. 生成信号快照
4. 更新市场状态

运行时间：
- 18:00: 更新行情数据
- 18:30: 计算因子
- 19:00: 生成信号
- 20:00: 生成市场状态

使用 APScheduler 实现定时任务
"""

import os
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_lake import get_data_lake
from quant.snapshot_engine import get_snapshot_engine
from data.hub import get_datahub

class QuantScheduler:
    """量化调度器"""
    
    def __init__(self):
        self.scheduler = BlockingScheduler(timezone='Asia/Shanghai')
        self.data_lake = get_data_lake()
        self.snapshot_engine = get_snapshot_engine()
        self.datahub = get_datahub()
        
        # 注册任务
        self._register_jobs()
    
    def _register_jobs(self):
        """注册定时任务"""
        # 每天 18:00 更新行情数据
        self.scheduler.add_job(
            self.update_market_data,
            'cron',
            hour=18,
            minute=0,
            id='update_market_data',
            name='更新市场行情数据'
        )
        
        # 每天 18:30 计算因子
        self.scheduler.add_job(
            self.calculate_factors,
            'cron',
            hour=18,
            minute=30,
            id='calculate_factors',
            name='计算全市场因子'
        )
        
        # 每天 19:00 生成信号
        self.scheduler.add_job(
            self.generate_signals,
            'cron',
            hour=19,
            minute=0,
            id='generate_signals',
            name='生成全市场信号'
        )
        
        # 每天 20:00 生成市场状态
        self.scheduler.add_job(
            self.generate_market_state,
            'cron',
            hour=20,
            minute=0,
            id='generate_market_state',
            name='生成市场状态'
        )
        
        # 每天 20:30 生成完整快照
        self.scheduler.add_job(
            self.generate_complete_snapshot,
            'cron',
            hour=20,
            minute=30,
            id='generate_complete_snapshot',
            name='生成完整量化快照'
        )
        
        # 每天 00:00 重置用户配额
        self.scheduler.add_job(
            self.reset_daily_quota,
            'cron',
            hour=0,
            minute=0,
            id='reset_daily_quota',
            name='重置每日配额'
        )
    
    def update_market_data(self):
        """更新市场行情数据"""
        print(f"⏰ {datetime.now()} - 开始更新市场行情数据...")
        
        try:
            # 获取需要更新的股票列表
            stocks = self.datahub.get_stock_list('cn')
            
            for code in stocks:
                try:
                    # 获取最新K线数据
                    df = self.datahub.get_ohlcv_dataframe(code, 'cn')
                    
                    # 保存到数据湖
                    self.data_lake.save_daily_data(code, 'cn', df)
                    
                except Exception as e:
                    print(f"❌ 更新股票 {code} 失败: {str(e)}")
            
            print(f"✅ {datetime.now()} - 市场行情数据更新完成")
        
        except Exception as e:
            print(f"❌ 更新市场数据失败: {str(e)}")
    
    def calculate_factors(self):
        """计算全市场因子"""
        print(f"⏰ {datetime.now()} - 开始计算全市场因子...")
        
        try:
            # 获取股票列表
            stocks = self.data_lake.list_stocks('cn')
            target_date = datetime.now().strftime('%Y-%m-%d')
            
            for code in stocks:
                try:
                    df = self.data_lake.load_daily_data(code, 'cn')
                    if df.empty:
                        continue
                    
                    # 计算因子并保存
                    factors = self.snapshot_engine.factor_engine.calculate_factors(df)
                    self.snapshot_engine.save_factor_snapshot(code, target_date, factors)
                    
                except Exception as e:
                    print(f"❌ 计算股票 {code} 因子失败: {str(e)}")
            
            print(f"✅ {datetime.now()} - 全市场因子计算完成")
        
        except Exception as e:
            print(f"❌ 计算因子失败: {str(e)}")
    
    def generate_signals(self):
        """生成全市场信号"""
        print(f"⏰ {datetime.now()} - 开始生成全市场信号...")
        
        try:
            stocks = self.data_lake.list_stocks('cn')
            target_date = datetime.now().strftime('%Y-%m-%d')
            
            for code in stocks:
                try:
                    df = self.data_lake.load_daily_data(code, 'cn')
                    if df.empty:
                        continue
                    
                    factors = self.snapshot_engine.factor_engine.calculate_factors(df)
                    signals = self.snapshot_engine.signal_engine.generate_signals(df, factors)
                    
                    self.snapshot_engine.save_signal_snapshot(code, target_date, signals)
                    
                except Exception as e:
                    print(f"❌ 生成股票 {code} 信号失败: {str(e)}")
            
            print(f"✅ {datetime.now()} - 全市场信号生成完成")
        
        except Exception as e:
            print(f"❌ 生成信号失败: {str(e)}")
    
    def generate_market_state(self):
        """生成市场状态"""
        print(f"⏰ {datetime.now()} - 开始生成市场状态...")
        
        try:
            target_date = datetime.now().strftime('%Y-%m-%d')
            self.snapshot_engine._generate_market_state(target_date)
            print(f"✅ {datetime.now()} - 市场状态生成完成")
        
        except Exception as e:
            print(f"❌ 生成市场状态失败: {str(e)}")
    
    def generate_complete_snapshot(self):
        """生成完整量化快照"""
        print(f"⏰ {datetime.now()} - 开始生成完整量化快照...")
        
        try:
            target_date = datetime.now().strftime('%Y-%m-%d')
            self.snapshot_engine.generate_daily_snapshot(target_date)
            print(f"✅ {datetime.now()} - 完整量化快照生成完成")
        
        except Exception as e:
            print(f"❌ 生成快照失败: {str(e)}")
    
    def reset_daily_quota(self):
        """重置每日配额"""
        print(f"⏰ {datetime.now()} - 开始重置每日配额...")
        
        try:
            from database.db import get_db, reset_user_daily_usage, get_all_users
            
            db = next(get_db())
            users = get_all_users(db)
            
            for user in users:
                reset_user_daily_usage(db, user.username)
            
            print(f"✅ {datetime.now()} - 每日配额重置完成")
        
        except Exception as e:
            print(f"❌ 重置配额失败: {str(e)}")
    
    def run(self):
        """启动调度器"""
        print("🚀 Quant Scheduler 启动中...")
        print("📅 定时任务列表:")
        
        for job in self.scheduler.get_jobs():
            print(f"  - {job.name}: {job.trigger}")
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("🛑 Quant Scheduler 已停止")
    
    def run_once(self):
        """手动运行一次所有任务（用于测试）"""
        print("🔄 手动运行一次所有任务...")
        
        self.update_market_data()
        self.calculate_factors()
        self.generate_signals()
        self.generate_market_state()
        self.generate_complete_snapshot()
        
        print("✅ 所有任务执行完成")

# 全局实例
_scheduler = None

def get_scheduler() -> QuantScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = QuantScheduler()
    return _scheduler

# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quant Scheduler")
    parser.add_argument('--run-once', action='store_true', help='运行一次所有任务')
    parser.add_argument('--start', action='store_true', help='启动定时调度')
    
    args = parser.parse_args()
    
    scheduler = get_scheduler()
    
    if args.run_once:
        scheduler.run_once()
    elif args.start:
        scheduler.run()
    else:
        print("请指定 --run-once 或 --start")