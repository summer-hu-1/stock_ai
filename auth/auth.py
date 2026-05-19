"""
认证模块 - Authentication Module
处理用户登录、注册、会话管理等功能
"""

import streamlit as st
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime, timedelta

from admin_auth.db import get_session
from admin_auth.repository import AdminRepository


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def register_user(username: str, password: str, email: str = None, name: str = None) -> tuple:
    """
    注册用户

    Returns:
        (success: bool, message: str)
    """
    db = get_session()

    if AdminRepository.get_user_by_username(db, username):
        return False, "用户名已存在"

    if email and AdminRepository.get_user_by_email(db, email):
        return False, "邮箱已被注册"

    password_hash = hash_password(password)
    try:
        AdminRepository.create_user(db, username, password_hash, email, name)
        AdminRepository.add_log(db, username, "register")
        return True, "注册成功"
    except Exception as e:
        return False, f"注册失败: {str(e)}"
    finally:
        db.close()


def login_user(username: str, password: str) -> tuple:
    """
    登录用户

    Returns:
        (success: bool, message: str, user_dict: dict or None)
    """
    db = get_session()

    user = AdminRepository.get_user_by_username(db, username)

    if not user:
        return False, "用户名不存在", None

    if not user.is_active:
        return False, "用户已被封禁", None

    if not verify_password(password, user.password_hash):
        return False, "密码错误", None

    AdminRepository.update_user_last_login(db, username)

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

    AdminRepository.add_log(db, username, "login")
    db.close()

    return True, "登录成功", user_dict


def logout_user():
    """退出登录"""
    if "user" in st.session_state:
        username = st.session_state["user"]["username"]
        db = get_session()
        AdminRepository.add_log(db, username, "logout")
        db.close()
    
    # 清除 Cookie
    if "cookie_manager" in st.session_state:
        st.session_state["cookie_manager"].delete("saved_username")
    
    # 清除会话状态
    keys_to_remove = ["user", "username", "role", "membership"]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def set_session_user(user_dict: dict):
    """设置会话用户"""
    st.session_state["user"] = user_dict
    st.session_state["username"] = user_dict["username"]
    st.session_state["role"] = user_dict["role"]
    st.session_state["membership"] = user_dict["membership"]


def is_logged_in() -> bool:
    """检查是否已登录"""
    return "user" in st.session_state and st.session_state["user"] is not None


def is_admin() -> bool:
    """检查是否为管理员"""
    if not is_logged_in():
        return False
    return st.session_state["user"].get("role") == "admin"


def can_analyze() -> tuple:
    """
    检查是否可以进行分析（检查每日限额）
    
    Returns:
        (can_do: bool, message: str)
    """
    # 游客模式逻辑
    if not is_logged_in():
        # 游客默认限制，可以根据需要调整
        # 这里允许游客分析，但不记录到特定用户
        return True, "游客模式（可以分析）"
    
    user = st.session_state["user"]
    
    # 管理员和VIP用户不受限制
    if user["role"] == "admin" or user["membership"] == "vip":
        return True, "可以分析"
    
    # 检查每日限额
    today_used = user["today_used"]
    daily_limit = user["daily_limit"]
    
    if today_used >= daily_limit:
        return False, f"今日分析次数已用完（{today_used}/{daily_limit}次），请明日再试或升级会员"
    
    return True, f"可以分析（今日剩余 {daily_limit - today_used} 次）"


def record_analysis_usage():
    """记录分析使用次数"""
    if is_logged_in():
        username = st.session_state["user"]["username"]
        db = get_session()
        AdminRepository.increment_user_usage(db, username)
        db.close()

        st.session_state["user"]["today_used"] += 1
    else:
        # 游客模式下，可以使用 session_state 简单记录本次会话的使用次数
        if "guest_used" not in st.session_state:
            st.session_state["guest_used"] = 0
        st.session_state["guest_used"] += 1


def get_user_by_username(username: str) -> dict:
    """通过用户名获取用户信息（用于自动登录）"""
    db = get_session()
    user = AdminRepository.get_user_by_username(db, username)
    db.close()
    
    if not user or not user.is_active:
        return None
        
    return {
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


def get_user_info() -> dict:
    """获取当前用户信息"""
    if is_logged_in():
        return st.session_state["user"]
    return None


def get_user_quota_info() -> dict:
    """获取用户配额信息"""
    if not is_logged_in():
        return {"used": 0, "limit": 0, "remaining": 0}
    
    user = st.session_state["user"]
    used = user["today_used"]
    limit = user["daily_limit"]
    
    return {
        "used": used,
        "limit": limit,
        "remaining": limit - used if limit > 0 else 999,
        "unlimited": limit == 999
    }