"""
admin_auth 业务逻辑层 - Service Layer
提供业务逻辑处理
"""

from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime, timedelta

from admin_auth.db import get_session
from admin_auth.repository import AdminRepository
from admin_auth.models import AdminStats


class AdminService:
    """管理员业务逻辑类"""

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        return checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def register_user(email: str, password: str, name: str = None) -> tuple:
        """
        注册用户（邮箱为核心身份标识）

        Returns:
            (success: bool, message: str)
        """
        db = get_session()
        
        # 验证邮箱格式
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            return False, "请输入有效的邮箱地址"

        if AdminRepository.get_user_by_email(db, email):
            return False, "该邮箱已被注册"

        password_hash = AdminService.hash_password(password)
        username = name or email.split('@')[0]
        try:
            AdminRepository.create_user(db, username, password_hash, email, name)
            AdminRepository.add_log(db, username, "register")
            return True, "注册成功"
        except Exception as e:
            return False, f"注册失败: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def login_user(email: str, password: str) -> tuple:
        """
        登录用户（使用邮箱）

        Returns:
            (success: bool, message: str, user_dict: dict or None)
        """
        db = get_session()

        user = AdminRepository.get_user_by_email(db, email)

        if not user:
            return False, "邮箱未注册", None

        if not user.is_active:
            return False, "账户已被封禁", None

        if not AdminService.verify_password(password, user.password_hash):
            return False, "密码错误", None

        AdminRepository.update_user_last_login(db, user.username)

        user_dict = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "membership": user.membership,
            "vip_expire": user.vip_expire.strftime("%Y-%m-%d") if user.vip_expire else None,
            "token_balance": user.token_balance,
            "daily_limit": user.daily_limit,
            "today_used": user.today_used,
            "is_active": user.is_active,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else None,
            "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else None
        }

        AdminRepository.add_log(db, user.username, "login")
        db.close()

        return True, "登录成功", user_dict

    @staticmethod
    def logout_user(username: str):
        """退出登录"""
        db = get_session()
        AdminRepository.add_log(db, username, "logout")
        db.close()

    @staticmethod
    def get_stats() -> AdminStats:
        """获取管理员统计信息"""
        db = get_session()
        try:
            return AdminStats(
                total_users=AdminRepository.get_user_count(db),
                active_users=AdminRepository.get_active_user_count(db),
                today_analysis=AdminRepository.get_today_analysis_count(db),
                total_analysis=AdminRepository.get_total_analysis_count(db)
            )
        finally:
            db.close()

    @staticmethod
    def get_all_users():
        """获取所有用户"""
        db = get_session()
        try:
            return AdminRepository.get_all_users(db)
        finally:
            db.close()

    @staticmethod
    def get_all_logs(limit: int = 50):
        """获取所有日志"""
        db = get_session()
        try:
            return AdminRepository.get_all_logs(db, limit)
        finally:
            db.close()

    @staticmethod
    def get_all_analysis_records(limit: int = 50):
        """获取所有分析记录"""
        db = get_session()
        try:
            return AdminRepository.get_all_analysis_records(db, limit)
        finally:
            db.close()

    @staticmethod
    def toggle_user_active(username: str):
        """切换用户激活状态"""
        db = get_session()
        try:
            return AdminRepository.toggle_user_active(db, username)
        finally:
            db.close()

    @staticmethod
    def update_user_membership(username: str, membership: str, expire_date: datetime = None):
        """更新用户会员等级"""
        db = get_session()
        try:
            return AdminRepository.update_user_membership(db, username, membership, expire_date)
        finally:
            db.close()

    @staticmethod
    def init_default_admin():
        """初始化默认管理员"""
        db = get_session()
        try:
            user_count = AdminRepository.get_user_count(db)
            if user_count == 0:
                import os
                try:
                    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
                    admin_password = os.environ.get('ADMIN_PASSWORD', '123456')
                except:
                    admin_username = 'admin'
                    admin_password = '123456'
                password_hash = AdminService.hash_password(admin_password)
                AdminRepository.create_user(db, admin_username, password_hash, 'admin@stockai.com', '管理员', role="admin")
                return True, admin_username
            return False, None
        finally:
            db.close()