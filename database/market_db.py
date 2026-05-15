"""
统一数据库模块 - Market Database

V10.2 核心升级：从零散数据库升级为统一数据中台

架构分层：
1. Market Data（市场原始数据）- 事实层
2. Feature Store（特征层）- 计算层
3. Strategy Layer（策略层）- 行为层

使用 SQLite + Parquet 方案：
- SQLite: 结构化查询（signals, scores, state, positions）
- Parquet: 海量K线存储（data_lake）
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def get_db_path():
    """获取数据库路径"""
    DB_PATH = os.path.join(os.path.dirname(__file__), 'market.db')
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH

def get_data_lake_path(market: str = "cn", freq: str = "daily"):
    """获取 data_lake 路径"""
    path = os.path.join(os.path.dirname(__file__), '..', 'data_lake', market, freq)
    os.makedirs(path, exist_ok=True)
    return path

# 创建引擎
engine = create_engine(f'sqlite:///{get_db_path()}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== 1. Market Data（事实层）====================

class DailyBar(Base):
    """每日K线 - 核心原始数据"""
    __tablename__ = "daily_bars"
    
    code = Column(String, primary_key=True)
    market = Column(String, nullable=False)
    date = Column(String, primary_key=True)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    
    price_change = Column(Float)
    price_change_pct = Column(Float)
    turnover_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)

class IndexBar(Base):
    """指数K线"""
    __tablename__ = "index_bars"
    
    code = Column(String, primary_key=True)
    market = Column(String, nullable=False)
    date = Column(String, primary_key=True)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)

class SectorBar(Base):
    """板块K线"""
    __tablename__ = "sector_bars"
    
    sector = Column(String, primary_key=True)
    date = Column(String, primary_key=True)
    
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
    rise_count = Column(Integer)
    fall_count = Column(Integer)
    avg_change = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)

# ==================== 2. Feature Store（计算层）====================

class FactorSnapshot(Base):
    """因子快照 - 核心量化特征"""
    __tablename__ = "factor_snapshot"
    
    code = Column(String, primary_key=True)
    date = Column(String, primary_key=True)
    
    # 核心因子得分
    trend_score = Column(Float)
    momentum_score = Column(Float)
    volume_score = Column(Float)
    volatility_score = Column(Float)
    strength_score = Column(Float)
    
    # 辅助因子
    ma_score = Column(Float)
    macd_score = Column(Float)
    rsi_score = Column(Float)
    boll_score = Column(Float)
    
    # 综合得分
    total_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)

class SignalSnapshot(Base):
    """信号快照"""
    __tablename__ = "signal_snapshot"
    
    code = Column(String, primary_key=True)
    date = Column(String, primary_key=True)
    
    # 信号类型（0-100 强度）
    breakout = Column(Integer)
    reversal = Column(Integer)
    main_rise = Column(Integer)
    volume_surge = Column(Integer)
    
    # 综合信号强度
    signal_strength = Column(Float)
    signal_direction = Column(String)  # up/down/neutral
    
    created_at = Column(DateTime, default=datetime.now)

class MarketState(Base):
    """市场状态 - AI大脑核心"""
    __tablename__ = "market_state"
    
    date = Column(String, primary_key=True)
    
    # 核心状态
    market_cycle = Column(String)       # bull/bear/sideways
    cycle_stage = Column(String)        # early/middle/late
    
    # 情绪指标
    sentiment_score = Column(Float)     # 0-100
    sentiment_trend = Column(String)    # up/down/flat
    
    # 市场统计
    limit_up_count = Column(Integer)
    limit_down_count = Column(Integer)
    rise_ratio = Column(Float)
    total_volume = Column(Float)        # 万亿
    north_money = Column(Float)         # 亿
    
    # 风险等级
    risk_level = Column(String)         # low/medium/high
    
    # 热门板块
    hot_sector = Column(String)
    top_sectors = Column(TEXT)          # JSON array
    
    created_at = Column(DateTime, default=datetime.now)

class SectorStrength(Base):
    """板块强度"""
    __tablename__ = "sector_strength"
    
    sector = Column(String, primary_key=True)
    date = Column(String, primary_key=True)
    
    strength_score = Column(Float)
    trend = Column(String)              # up/down/sideways
    change_pct = Column(Float)
    turnover_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)

class LeaderSnapshot(Base):
    """龙头快照"""
    __tablename__ = "leader_snapshot"
    
    date = Column(String, primary_key=True)
    code = Column(String, primary_key=True)
    
    name = Column(String)
    sector = Column(String)
    leader_score = Column(Float)        # 0-100
    leader_type = Column(String)        # main/branch/theme
    
    created_at = Column(DateTime, default=datetime.now)

class StockScore(Base):
    """股票综合评分"""
    __tablename__ = "stock_score"
    
    code = Column(String, primary_key=True)
    date = Column(String, primary_key=True)
    
    name = Column(String)
    overall_score = Column(Float)       # 0-100
    factor_score = Column(Float)
    signal_score = Column(Float)
    risk_score = Column(Float)
    leader_bonus = Column(Float)
    
    risk_level = Column(String)         # low/medium/high
    trading_signal = Column(String)     # buy/hold/sell
    
    created_at = Column(DateTime, default=datetime.now)

# ==================== 3. Strategy Layer（行为层）====================

class Position(Base):
    """持仓记录"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, index=True)
    code = Column(String, index=True)
    name = Column(String)
    
    quantity = Column(Integer)
    avg_cost = Column(Float)
    current_price = Column(Float)
    
    market_value = Column(Float)
    profit_loss = Column(Float)
    profit_loss_pct = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

class Order(Base):
    """订单记录"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, index=True)
    order_id = Column(String, unique=True)
    
    code = Column(String)
    name = Column(String)
    side = Column(String)               # buy/sell
    order_type = Column(String)         # market/limit
    
    price = Column(Float)
    quantity = Column(Integer)
    filled_quantity = Column(Integer)
    
    status = Column(String)             # pending/filled/canceled
    commission = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)
    filled_at = Column(DateTime)

class Trade(Base):
    """交易记录"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, index=True)
    trade_id = Column(String, unique=True)
    
    code = Column(String)
    name = Column(String)
    side = Column(String)
    
    price = Column(Float)
    quantity = Column(Integer)
    amount = Column(Float)
    commission = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)

class Watchlist(Base):
    """自选股"""
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, index=True)
    code = Column(String)
    name = Column(String)
    reason = Column(String)
    priority = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.now)

class StrategySnapshot(Base):
    """策略快照"""
    __tablename__ = "strategy_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String, index=True)
    date = Column(String)
    
    params = Column(TEXT)               # JSON
    performance = Column(TEXT)          # JSON
    positions = Column(TEXT)            # JSON
    
    created_at = Column(DateTime, default=datetime.now)

# ==================== 数据库操作 ====================

def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表初始化完成")

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== Data Lake 操作（Parquet）====================

def save_daily_bar_to_lake(code: str, market: str, df: pd.DataFrame):
    """保存每日K线到 data_lake（Parquet格式）"""
    path = get_data_lake_path(market, "daily")
    file_path = os.path.join(path, f"{code}.parquet")
    
    # 确保日期列格式正确
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # 写入 Parquet
    table = pa.Table.from_pandas(df)
    pq.write_to_dataset(
        table,
        root_path=path,
        partition_cols=['date'],
        filename=f"{code}.parquet"
    )

def load_daily_bar_from_lake(code: str, market: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """从 data_lake 加载K线数据"""
    path = get_data_lake_path(market, "daily")
    file_path = os.path.join(path, f"{code}.parquet")
    
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pq.read_table(file_path).to_pandas()
    
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
    
    return df.sort_values('date')

# ==================== 快照引擎接口 ====================

class SnapshotEngine:
    """快照引擎 - 每日生成量化快照"""
    
    def __init__(self):
        self.db = next(get_db())
    
    def save_factor_snapshot(self, code: str, date: str, factors: dict):
        """保存因子快照"""
        snapshot = FactorSnapshot(
            code=code,
            date=date,
            trend_score=factors.get('trend_score'),
            momentum_score=factors.get('momentum_score'),
            volume_score=factors.get('volume_score'),
            volatility_score=factors.get('volatility_score'),
            strength_score=factors.get('strength_score'),
            ma_score=factors.get('ma_score'),
            macd_score=factors.get('macd_score'),
            rsi_score=factors.get('rsi_score'),
            boll_score=factors.get('boll_score'),
            total_score=factors.get('total_score'),
            created_at=datetime.now()
        )
        
        # 更新或插入
        self.db.merge(snapshot)
        self.db.commit()
    
    def save_signal_snapshot(self, code: str, date: str, signals: dict):
        """保存信号快照"""
        snapshot = SignalSnapshot(
            code=code,
            date=date,
            breakout=signals.get('breakout', 0),
            reversal=signals.get('reversal', 0),
            main_rise=signals.get('main_rise', 0),
            volume_surge=signals.get('volume_surge', 0),
            signal_strength=signals.get('signal_strength', 0),
            signal_direction=signals.get('signal_direction', 'neutral'),
            created_at=datetime.now()
        )
        self.db.merge(snapshot)
        self.db.commit()
    
    def save_market_state(self, date: str, state: dict):
        """保存市场状态"""
        market_state = MarketState(
            date=date,
            market_cycle=state.get('market_cycle'),
            cycle_stage=state.get('cycle_stage'),
            sentiment_score=state.get('sentiment_score'),
            sentiment_trend=state.get('sentiment_trend'),
            limit_up_count=state.get('limit_up_count'),
            limit_down_count=state.get('limit_down_count'),
            rise_ratio=state.get('rise_ratio'),
            total_volume=state.get('total_volume'),
            north_money=state.get('north_money'),
            risk_level=state.get('risk_level'),
            hot_sector=state.get('hot_sector'),
            top_sectors=state.get('top_sectors', '[]'),
            created_at=datetime.now()
        )
        self.db.merge(market_state)
        self.db.commit()
    
    def save_stock_score(self, code: str, date: str, score: dict):
        """保存股票评分"""
        stock_score = StockScore(
            code=code,
            date=date,
            name=score.get('name'),
            overall_score=score.get('overall_score'),
            factor_score=score.get('factor_score'),
            signal_score=score.get('signal_score'),
            risk_score=score.get('risk_score'),
            leader_bonus=score.get('leader_bonus'),
            risk_level=score.get('risk_level'),
            trading_signal=score.get('trading_signal'),
            created_at=datetime.now()
        )
        self.db.merge(stock_score)
        self.db.commit()
    
    def get_latest_factor_snapshot(self, code: str) -> dict:
        """获取最新因子快照"""
        snapshot = self.db.query(FactorSnapshot)\
            .filter(FactorSnapshot.code == code)\
            .order_by(FactorSnapshot.date.desc())\
            .first()
        if snapshot:
            return {
                'code': snapshot.code,
                'date': snapshot.date,
                'trend_score': snapshot.trend_score,
                'momentum_score': snapshot.momentum_score,
                'volume_score': snapshot.volume_score,
                'volatility_score': snapshot.volatility_score,
                'total_score': snapshot.total_score
            }
        return {}
    
    def get_latest_market_state(self) -> dict:
        """获取最新市场状态"""
        state = self.db.query(MarketState)\
            .order_by(MarketState.date.desc())\
            .first()
        if state:
            return {
                'date': state.date,
                'market_cycle': state.market_cycle,
                'sentiment_score': state.sentiment_score,
                'risk_level': state.risk_level,
                'hot_sector': state.hot_sector
            }
        return {}
    
    def get_top_stocks_by_score(self, date: str = None, limit: int = 20) -> list:
        """获取高分股票"""
        query = self.db.query(StockScore)
        if date:
            query = query.filter(StockScore.date == date)
        query = query.order_by(StockScore.overall_score.desc()).limit(limit)
        
        return [{
            'code': s.code,
            'name': s.name,
            'overall_score': s.overall_score,
            'trading_signal': s.trading_signal,
            'risk_level': s.risk_level
        } for s in query.all()]

# 初始化数据库
if __name__ == "__main__":
    init_db()