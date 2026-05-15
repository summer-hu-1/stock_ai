"""
Quant Snapshot Engine - 量化快照引擎

核心职责：
1. 每天统一计算所有股票的因子
2. 生成信号快照
3. 生成市场状态
4. 计算股票综合评分
5. 识别龙头股票

运行方式：
- 每天收盘后（18:00-20:00）离线执行
- 所有计算结果写入 Feature Store
- 白天用户查询直接读取快照，无需重新计算

架构：
DataLake -> FactorEngine -> SignalEngine -> ScoreEngine -> Database
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_lake import get_data_lake
from database.market_db import SnapshotEngine, init_db
from quant.engine import get_quant_core
from quant.factor.engine import FactorEngine
from quant.signal.engine import SignalEngine
from quant.state.engine import MarketStateEngine

class QuantSnapshotEngine:
    """量化快照引擎"""
    
    def __init__(self):
        self.data_lake = get_data_lake()
        self.snapshot_engine = SnapshotEngine()
        self.quant_core = get_quant_core()
        self.factor_engine = FactorEngine()
        self.signal_engine = SignalEngine()
        self.state_engine = MarketStateEngine()
        
        # 确保数据库已初始化
        init_db()
    
    def generate_daily_snapshot(self, target_date: str = None):
        """
        生成每日快照（核心方法）
        
        Args:
            target_date: 目标日期 (YYYY-MM-DD)，默认昨天
        """
        if not target_date:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"🚀 开始生成 {target_date} 的量化快照...")
        
        # 1. 获取市场股票列表
        stocks = self.data_lake.list_stocks('cn')
        print(f"📊 待处理股票数量: {len(stocks)}")
        
        # 2. 遍历计算每个股票的因子和信号
        for i, code in enumerate(stocks):
            try:
                self._process_stock(code, target_date)
                if (i + 1) % 50 == 0:
                    print(f"⏳ 进度: {i + 1}/{len(stocks)}")
            except Exception as e:
                print(f"❌ 处理股票 {code} 失败: {str(e)}")
        
        # 3. 生成市场状态
        self._generate_market_state(target_date)
        
        # 4. 生成龙头快照
        self._generate_leaders(target_date)
        
        print(f"✅ {target_date} 量化快照生成完成！")
    
    def _process_stock(self, code: str, date: str):
        """处理单个股票"""
        # 加载K线数据
        df = self.data_lake.load_daily_data(code, 'cn')
        
        if df.empty:
            return
        
        # 计算因子
        factors = self.factor_engine.calculate_factors(df)
        
        # 计算信号
        signals = self.signal_engine.generate_signals(df, factors)
        
        # 计算评分
        score = self._calculate_score(factors, signals)
        
        # 保存快照
        self.snapshot_engine.save_factor_snapshot(code, date, factors)
        self.snapshot_engine.save_signal_snapshot(code, date, signals)
        self.snapshot_engine.save_stock_score(code, date, score)
    
    def _calculate_score(self, factors: Dict, signals: Dict) -> Dict:
        """计算股票综合评分"""
        # 因子得分（权重：60%）
        factor_score = sum([
            factors.get('trend_score', 0) * 0.25,
            factors.get('momentum_score', 0) * 0.25,
            factors.get('volume_score', 0) * 0.2,
            factors.get('volatility_score', 0) * 0.15,
            factors.get('strength_score', 0) * 0.15
        ])
        
        # 信号得分（权重：40%）
        signal_score = signals.get('signal_strength', 0)
        
        # 综合得分
        overall_score = factor_score * 0.6 + signal_score * 0.4
        
        # 确定风险等级
        risk_level = self._determine_risk_level(factors, signals)
        
        # 确定交易信号
        trading_signal = self._determine_trading_signal(overall_score, risk_level)
        
        return {
            'factor_score': round(factor_score, 2),
            'signal_score': round(signal_score, 2),
            'overall_score': round(overall_score, 2),
            'risk_score': self._calculate_risk_score(factors),
            'leader_bonus': 0,
            'risk_level': risk_level,
            'trading_signal': trading_signal
        }
    
    def _determine_risk_level(self, factors: Dict, signals: Dict) -> str:
        """确定风险等级"""
        volatility = factors.get('volatility_score', 50)
        
        if volatility > 70:
            return 'high'
        elif volatility < 30:
            return 'low'
        else:
            return 'medium'
    
    def _determine_trading_signal(self, score: float, risk_level: str) -> str:
        """确定交易信号"""
        if score >= 70 and risk_level != 'high':
            return 'buy'
        elif score >= 50:
            return 'hold'
        else:
            return 'sell'
    
    def _calculate_risk_score(self, factors: Dict) -> float:
        """计算风险评分"""
        return 100 - factors.get('volatility_score', 50)
    
    def _generate_market_state(self, date: str):
        """生成市场状态"""
        # 获取市场整体数据
        state = self.state_engine.analyze_market(date)
        
        # 保存到数据库
        self.snapshot_engine.save_market_state(date, state)
        print(f"📈 市场状态已保存: {state.get('market_cycle')}")
    
    def _generate_leaders(self, date: str):
        """生成龙头快照"""
        # 获取龙头数据
        leaders = self.state_engine.get_leaders(date)
        
        # 保存龙头
        from database.market_db import LeaderSnapshot, get_db
        
        db = next(get_db())
        for leader in leaders:
            snapshot = LeaderSnapshot(
                date=date,
                code=leader['code'],
                name=leader.get('name'),
                sector=leader.get('sector'),
                leader_score=leader.get('leader_score', 0),
                leader_type=leader.get('leader_type', 'main'),
                created_at=datetime.now()
            )
            db.merge(snapshot)
        
        db.commit()
        print(f"👑 龙头快照已保存: {len(leaders)} 只")
    
    def get_stock_snapshot(self, code: str, date: str = None) -> Dict:
        """获取单只股票的快照"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        return {
            'factors': self.snapshot_engine.get_latest_factor_snapshot(code),
            'signals': self._get_signal_snapshot(code, date),
            'market_state': self.snapshot_engine.get_latest_market_state()
        }
    
    def _get_signal_snapshot(self, code: str, date: str) -> Dict:
        """获取信号快照"""
        from database.market_db import SignalSnapshot, get_db
        
        db = next(get_db())
        snapshot = db.query(SignalSnapshot)\
            .filter(SignalSnapshot.code == code, SignalSnapshot.date == date)\
            .first()
        
        if snapshot:
            return {
                'code': snapshot.code,
                'date': snapshot.date,
                'breakout': snapshot.breakout,
                'reversal': snapshot.reversal,
                'main_rise': snapshot.main_rise,
                'signal_strength': snapshot.signal_strength,
                'signal_direction': snapshot.signal_direction
            }
        return {}
    
    def get_top_stocks(self, date: str = None, limit: int = 20) -> List[Dict]:
        """获取高分股票"""
        return self.snapshot_engine.get_top_stocks_by_score(date, limit)

# 全局实例
_snapshot_engine = None

def get_snapshot_engine() -> QuantSnapshotEngine:
    """获取全局快照引擎实例"""
    global _snapshot_engine
    if _snapshot_engine is None:
        _snapshot_engine = QuantSnapshotEngine()
    return _snapshot_engine

# 命令行运行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quant Snapshot Engine")
    parser.add_argument('--date', type=str, help='目标日期 (YYYY-MM-DD)')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    engine = get_snapshot_engine()
    
    if args.test:
        # 测试模式：只处理少量股票
        print("🧪 测试模式启动...")
        # 这里可以添加测试逻辑
    else:
        engine.generate_daily_snapshot(args.date)