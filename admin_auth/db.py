"""
admin_auth 数据库模块 - Database Module
独立的管理员数据存储
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

Base = declarative_base()


class AdminUser(Base):
    """用户表"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String, default="member")
    membership = Column(String, default="free")
    vip_expire = Column(DateTime)
    token_balance = Column(Integer, default=0)
    daily_limit = Column(Integer, default=3)
    today_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)


class AdminLog(Base):
    """操作日志表"""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    action = Column(String)
    stock_code = Column(String)
    model_used = Column(String)
    token_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class AdminAnalysisRecord(Base):
    """分析记录表"""
    __tablename__ = "admin_analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    stock_code = Column(String)
    stock_name = Column(String)
    analysis_type = Column(String)
    model_name = Column(String)
    token_used = Column(Integer)
    result = Column(String)
    created_at = Column(DateTime, default=datetime.now)


def is_streamlit_cloud():
    """检测是否运行在 Streamlit Cloud 上"""
    if os.environ.get('STREAMLIT_CLOUD', '').lower() == 'true':
        return True
    if os.environ.get('IS_STREAMLIT_CLOUD', '').lower() == 'true':
        return True
    return False


def get_engine():
    """获取数据库引擎"""
    if is_streamlit_cloud():
        return create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    else:
        db_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(db_dir, 'admin_auth.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """获取数据库会话（直接返回，非生成器）"""
    return SessionLocal()