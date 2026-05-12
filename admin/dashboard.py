"""
管理员后台模块 - Admin Dashboard Module
提供管理员专属功能
"""

import streamlit as st
from database.db import (
    get_db, get_all_users, get_all_logs, get_all_analysis_records,
    toggle_user_active, update_user_membership, get_user_count,
    get_active_user_count, get_today_analysis_count, get_total_analysis_count
)
from datetime import datetime


def show_admin_dashboard():
    """显示管理员后台"""
    st.set_page_config(page_title="管理员后台", page_icon="🔧", layout="wide")
    
    # 检查是否为管理员
    if "user" not in st.session_state or st.session_state["user"].get("role") != "admin":
        st.error("❌ 权限不足：您不是管理员")
        return
    
    # 侧边栏导航
    with st.sidebar:
        st.subheader("🔧 管理员导航")
        menu = ["仪表盘", "用户管理", "分析记录", "操作日志"]
        selected_menu = st.selectbox("选择功能", menu)
    
    # 主内容区
    if selected_menu == "仪表盘":
        show_dashboard()
    elif selected_menu == "用户管理":
        show_user_management()
    elif selected_menu == "分析记录":
        show_analysis_records()
    elif selected_menu == "操作日志":
        show_operation_logs()


def show_dashboard():
    """显示仪表盘"""
    st.header("📊 系统仪表盘")
    
    db = next(get_db())
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 总用户数", get_user_count(db))
    
    with col2:
        st.metric("✅ 活跃用户", get_active_user_count(db))
    
    with col3:
        st.metric("📈 今日分析", get_today_analysis_count(db))
    
    with col4:
        st.metric("📊 总分析次数", get_total_analysis_count(db))
    
    # 最近用户列表
    st.subheader("👥 最近注册用户")
    users = get_all_users(db)[:10]
    if users:
        data = []
        for u in users:
            data.append({
                "用户名": u.username,
                "邮箱": u.email or "-",
                "角色": u.role,
                "会员": u.membership,
                "状态": "✅ 活跃" if u.is_active else "❌ 封禁",
                "注册时间": u.created_at.strftime("%Y-%m-%d %H:%M")
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("暂无用户")


def show_user_management():
    """显示用户管理"""
    st.header("👥 用户管理")
    
    db = next(get_db())
    users = get_all_users(db)
    
    if not users:
        st.info("暂无用户")
        return
    
    # 用户筛选
    col1, col2 = st.columns([1, 3])
    with col1:
        role_filter = st.selectbox("按角色筛选", ["全部", "admin", "member"])
    with col2:
        status_filter = st.selectbox("按状态筛选", ["全部", "活跃", "封禁"])
    
    # 筛选用户
    filtered_users = users
    if role_filter != "全部":
        filtered_users = [u for u in filtered_users if u.role == role_filter]
    if status_filter == "活跃":
        filtered_users = [u for u in filtered_users if u.is_active]
    elif status_filter == "封禁":
        filtered_users = [u for u in filtered_users if not u.is_active]
    
    # 用户列表
    for user in filtered_users:
        with st.expander(f"👤 {user.username} ({user.name or '-'})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**邮箱**: {user.email or '-'}")
                st.write(f"**角色**: {user.role}")
                st.write(f"**会员**: {user.membership}")
            
            with col2:
                st.write(f"**注册时间**: {user.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**上次登录**: {user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '-'}")
                st.write(f"**今日分析**: {user.today_used} / {user.daily_limit} 次")
            
            with col3:
                # 会员等级调整
                new_membership = st.selectbox(
                    "会员等级",
                    ["free", "pro", "vip"],
                    index=["free", "pro", "vip"].index(user.membership),
                    key=f"membership_{user.id}"
                )
                
                if st.button("更新会员等级", key=f"update_{user.id}"):
                    if update_user_membership(db, user.username, new_membership):
                        st.success(f"已将 {user.username} 会员等级更新为 {new_membership}")
                        st.rerun()
                    else:
                        st.error("更新失败")
                
                # 封禁/解封按钮
                if user.is_active:
                    if st.button(f"🔒 封禁用户", key=f"ban_{user.id}"):
                        success, new_status = toggle_user_active(db, user.username)
                        if success:
                            st.success(f"用户 {user.username} 已被封禁")
                            st.rerun()
                else:
                    if st.button(f"🔓 解封用户", key=f"unban_{user.id}"):
                        success, new_status = toggle_user_active(db, user.username)
                        if success:
                            st.success(f"用户 {user.username} 已被解封")
                            st.rerun()


def show_analysis_records():
    """显示分析记录"""
    st.header("📊 分析记录")
    
    db = next(get_db())
    records = get_all_analysis_records(db)
    
    if not records:
        st.info("暂无分析记录")
        return
    
    # 搜索框
    search_code = st.text_input("搜索股票代码", placeholder="输入股票代码")
    
    # 筛选记录
    filtered_records = records
    if search_code:
        filtered_records = [r for r in filtered_records if search_code.lower() in r.stock_code.lower()]
    
    # 显示记录
    data = []
    for record in filtered_records:
        data.append({
            "用户": record.username,
            "股票代码": record.stock_code,
            "股票名称": record.stock_name,
            "分析类型": record.analysis_type,
            "模型": record.model_name,
            "Token消耗": record.token_used,
            "时间": record.created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    st.dataframe(data, use_container_width=True)


def show_operation_logs():
    """显示操作日志"""
    st.header("📝 操作日志")
    
    db = next(get_db())
    logs = get_all_logs(db)
    
    if not logs:
        st.info("暂无操作日志")
        return
    
    # 搜索框
    search_user = st.text_input("搜索用户名", placeholder="输入用户名")
    
    # 筛选日志
    filtered_logs = logs
    if search_user:
        filtered_logs = [l for l in filtered_logs if search_user.lower() in l.username.lower()]
    
    # 显示日志
    data = []
    for log in filtered_logs:
        data.append({
            "用户名": log.username,
            "操作": log.action,
            "股票代码": log.stock_code or "-",
            "模型": log.model_used or "-",
            "Token消耗": log.token_used,
            "时间": log.created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    st.dataframe(data, use_container_width=True)


def go_back():
    """返回主应用"""
    if "show_admin" in st.session_state:
        del st.session_state["show_admin"]
        st.rerun()