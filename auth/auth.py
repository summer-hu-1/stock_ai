"""
认证模块 - Authentication Module
处理用户登录、注册、会话管理等功能
邮箱作为核心用户身份标识
"""

import re
import streamlit as st
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime, timedelta

from admin_auth.db import get_session
from admin_auth.repository import AdminRepository


def is_valid_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def register_user(email: str, password: str, name: str = None) -> tuple:
    """
    注册用户（邮箱为核心身份标识）

    Returns:
        (success: bool, message: str)
    """
    if not is_valid_email(email):
        return False, "请输入有效的邮箱地址"
    
    if len(password) < 6:
        return False, "密码至少需要6个字符"

    db = get_session()

    if AdminRepository.get_user_by_email(db, email):
        return False, "该邮箱已被注册"

    password_hash = hash_password(password)
    username = name or email.split('@')[0]
    try:
        AdminRepository.create_user(db, username, password_hash, email, name)
        AdminRepository.add_log(db, username, "register")
        return True, "注册成功"
    except Exception as e:
        return False, f"注册失败: {str(e)}"
    finally:
        db.close()


def login_user(email: str, password: str) -> tuple:
    """
    登录用户（使用邮箱）

    Returns:
        (success: bool, message: str, user_dict: dict or None)
    """
    if not is_valid_email(email):
        return False, "请输入有效的邮箱地址", None

    db = get_session()

    user = AdminRepository.get_user_by_email(db, email)

    if not user:
        return False, "邮箱未注册", None

    if not user.is_active:
        return False, "账户已被封禁", None

    if not verify_password(password, user.password_hash):
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


def logout_user():
    """退出登录"""
    if "user" in st.session_state:
        username = st.session_state["user"]["username"]
        db = get_session()
        AdminRepository.add_log(db, username, "logout")
        db.close()
    
    # 清除 Cookie
    if "cookie_manager" in st.session_state:
        st.session_state["cookie_manager"].delete("saved_email")
    
    # 清除会话状态
    keys_to_remove = ["user", "username", "role", "membership", 
                      "_auto_login_phase", "_auto_login_attempt", "_pending_cookie_email"]
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
    # 游客模式逻辑：限制5次
    if not is_logged_in():
        guest_used = st.session_state.get("guest_used", 0)
        if guest_used >= 5:
            return False, "游客模式最多使用5次，请登录后继续使用"
        return True, f"游客模式（剩余 {5 - guest_used} 次）"
    
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


def get_user_by_email(email: str) -> dict:
    """通过邮箱获取用户信息（用于自动登录）"""
    db = get_session()
    user = AdminRepository.get_user_by_email(db, email)
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


def get_user_by_username(username: str) -> dict:
    """通过用户名获取用户信息（兼容旧逻辑）"""
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