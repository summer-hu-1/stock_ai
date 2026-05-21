"""
admin_auth 数据访问层 - Repository Layer
提供数据库操作方法
"""

from sqlalchemy.orm import Session
from datetime import datetime

from admin_auth.db import AdminUser, AdminLog, AdminAnalysisRecord


class AdminRepository:
    """管理员数据访问类"""

    @staticmethod
    def create_user(db: Session, username: str, password_hash: str, email: str, name: str = None, role: str = "member") -> AdminUser:
        """创建用户（email 为必填）"""
        if not email:
            raise ValueError("邮箱不能为空")
        user = AdminUser(
            username=username or email,  # username 降级为兼容字段
            password_hash=password_hash,
            email=email,
            name=name or email.split('@')[0],
            role=role,
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

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> AdminUser:
        """根据用户名获取用户"""
        return db.query(AdminUser).filter(AdminUser.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> AdminUser:
        """根据邮箱获取用户"""
        return db.query(AdminUser).filter(AdminUser.email == email).first()

    @staticmethod
    def get_all_users(db: Session):
        """获取所有用户"""
        return db.query(AdminUser).order_by(AdminUser.created_at.desc()).all()

    @staticmethod
    def get_user_count(db: Session) -> int:
        """获取用户总数"""
        return db.query(AdminUser).count()

    @staticmethod
    def get_active_user_count(db: Session) -> int:
        """获取活跃用户数"""
        return db.query(AdminUser).filter(AdminUser.is_active == True).count()

    @staticmethod
    def toggle_user_active(db: Session, username: str):
        """切换用户激活状态"""
        user = AdminRepository.get_user_by_username(db, username)
        if user:
            user.is_active = not user.is_active
            db.commit()
            return True, user.is_active
        return False, False

    @staticmethod
    def update_user_membership(db: Session, username: str, membership: str, expire_date: datetime = None):
        """更新用户会员等级"""
        user = AdminRepository.get_user_by_username(db, username)
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

    @staticmethod
    def update_user_last_login(db: Session, username: str):
        """更新用户最后登录时间"""
        user = AdminRepository.get_user_by_username(db, username)
        if user:
            user.last_login = datetime.now()
            db.commit()

    @staticmethod
    def increment_user_usage(db: Session, username: str):
        """增加用户今日使用次数"""
        user = AdminRepository.get_user_by_username(db, username)
        if user:
            user.today_used += 1
            db.commit()
            return True
        return False

    @staticmethod
    def add_log(db: Session, username: str, action: str, stock_code: str = None, model_used: str = None, token_used: int = 0):
        """添加操作日志"""
        log = AdminLog(
            username=username,
            action=action,
            stock_code=stock_code,
            model_used=model_used,
            token_used=token_used,
            created_at=datetime.now()
        )
        db.add(log)
        db.commit()

    @staticmethod
    def get_all_logs(db: Session, limit: int = 50):
        """获取所有日志"""
        return db.query(AdminLog).order_by(AdminLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def add_analysis_record(db: Session, username: str, stock_code: str, stock_name: str,
                            analysis_type: str, model_name: str, token_used: int, result: str):
        """添加分析记录"""
        record = AdminAnalysisRecord(
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

    @staticmethod
    def get_all_analysis_records(db: Session, limit: int = 50):
        """获取所有分析记录"""
        return db.query(AdminAnalysisRecord).order_by(AdminAnalysisRecord.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_user_analysis_records(db: Session, username: str, limit: int = 20):
        """获取用户分析记录"""
        return db.query(AdminAnalysisRecord).filter(
            AdminAnalysisRecord.username == username
        ).order_by(AdminAnalysisRecord.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_today_analysis_count(db: Session) -> int:
        """获取今日分析次数"""
        today = datetime.now().date()
        return db.query(AdminAnalysisRecord).filter(
            AdminAnalysisRecord.created_at >= datetime(today.year, today.month, today.day)
        ).count()

    @staticmethod
    def get_total_analysis_count(db: Session) -> int:
        """获取总分析次数"""
        return db.query(AdminAnalysisRecord).count()