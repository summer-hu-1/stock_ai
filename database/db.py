"""
数据库模块 - Database Module
使用 SQLite + SQLAlchemy 实现轻量级用户管理
支持本地开发和 Streamlit Cloud 部署
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

def is_streamlit_cloud():
    """检测是否运行在 Streamlit Cloud 上"""
    if os.environ.get('STREAMLIT_CLOUD', '').lower() == 'true':
        return True
    if os.environ.get('IS_STREAMLIT_CLOUD', '').lower() == 'true':
        return True
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            try:
                if st.secrets.get('DEEPSEEK_API_KEY', '').startswith('sk-'):
                    return True
            except:
                pass
    except:
        pass
    return False

if is_streamlit_cloud():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'auth.db')
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

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


class Log(Base):
    """操作日志表"""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    action = Column(String)
    stock_code = Column(String)
    model_used = Column(String)
    token_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class AnalysisRecord(Base):
    """分析记录表"""
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    stock_code = Column(String)
    stock_name = Column(String)
    analysis_type = Column(String)
    model_name = Column(String)
    token_used = Column(Integer)
    result = Column(String)
    created_at = Column(DateTime, default=datetime.now)


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


def create_user(db: Session, username: str, password_hash: str, email: str = None, name: str = None):
    """创建用户"""
    user = User(
        username=username,
        password_hash=password_hash,
        email=email,
        name=name,
        role="member",
        membership="free",
        daily_limit=3,
        today_used=0,
        is_active=True,
        created_at=datetime.now()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str):
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def update_user_last_login(db: Session, username: str):
    """更新用户最后登录时间"""
    user = get_user_by_username(db, username)
    if user:
        user.last_login = datetime.now()
        db.commit()


def update_user_membership(db: Session, username: str, membership: str, expire_date: datetime = None):
    """更新用户会员等级"""
    user = get_user_by_username(db, username)
    if user:
        user.membership = membership
        user.vip_expire = expire_date
        if membership == "vip":
            user.daily_limit = 999
        elif membership == "pro":
            user.daily_limit = 10
        else:
            user.daily_limit = 3
        db.commit()
        return True
    return False


def toggle_user_active(db: Session, username: str):
    """切换用户激活状态（封禁/解封）"""
    user = get_user_by_username(db, username)
    if user:
        user.is_active = not user.is_active
        db.commit()
        return True, user.is_active
    return False, False


def reset_user_daily_usage(db: Session, username: str):
    """重置用户今日使用次数"""
    user = get_user_by_username(db, username)
    if user:
        user.today_used = 0
        db.commit()
        return True
    return False


def increment_user_usage(db: Session, username: str):
    """增加用户今日使用次数"""
    user = get_user_by_username(db, username)
    if user:
        user.today_used += 1
        db.commit()
        return True
    return False


def add_log(db: Session, username: str, action: str, stock_code: str = None, model_used: str = None, token_used: int = 0):
    """添加操作日志"""
    log = Log(
        username=username,
        action=action,
        stock_code=stock_code,
        model_used=model_used,
        token_used=token_used,
        created_at=datetime.now()
    )
    db.add(log)
    db.commit()


def add_analysis_record(db: Session, username: str, stock_code: str, stock_name: str,
                        analysis_type: str, model_name: str, token_used: int, result: str):
    """添加分析记录"""
    record = AnalysisRecord(
        username=username,
        stock_code=stock_code,
        stock_name=stock_name,
        analysis_type=analysis_type,
        model_name=model_name,
        token_used=token_used,
        result=result,
        created_at=datetime.now()
    )
    db.add(record)
    db.commit()


def get_user_analysis_records(db: Session, username: str, limit: int = 20):
    """获取用户分析记录"""
    return db.query(AnalysisRecord).filter(
        AnalysisRecord.username == username
    ).order_by(AnalysisRecord.created_at.desc()).limit(limit).all()


def get_all_users(db: Session):
    """获取所有用户"""
    return db.query(User).order_by(User.created_at.desc()).all()


def get_all_logs(db: Session, limit: int = 50):
    """获取所有日志"""
    return db.query(Log).order_by(Log.created_at.desc()).limit(limit).all()


def get_all_analysis_records(db: Session, limit: int = 50):
    """获取所有分析记录"""
    return db.query(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()).limit(limit).all()


def get_user_count(db: Session):
    """获取用户总数"""
    return db.query(User).count()


def get_active_user_count(db: Session):
    """获取活跃用户数"""
    return db.query(User).filter(User.is_active == True).count()


def get_today_analysis_count(db: Session):
    """获取今日分析次数"""
    today = datetime.now().date()
    return db.query(AnalysisRecord).filter(
        AnalysisRecord.created_at >= datetime(today.year, today.month, today.day)
    ).count()


def get_total_analysis_count(db: Session):
    """获取总分析次数"""
    return db.query(AnalysisRecord).count()
