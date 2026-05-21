"""
登录页面组件 - Login Page Components
提供登录和注册界面（邮箱为核心身份标识）
"""

import streamlit as st
from auth.auth import login_user, register_user, set_session_user, is_valid_email


def show_login_page():
    """显示登录页面"""
    st.set_page_config(page_title="AI股票复盘系统 - 登录", page_icon="🔐", layout="centered")
    
    # 调试信息
    with st.expander("🔍 调试信息", expanded=False):
        from admin_auth.db import is_streamlit_cloud
        from admin_auth.service import AdminService

        st.write(f"**Streamlit Cloud 环境**: {is_streamlit_cloud()}")

        users = AdminService.get_all_users()
        user_count = len(users)
        st.write(f"**数据库用户数**: {user_count}")

        if user_count > 0:
            st.write("**所有用户列表**:")
            for user in users:
                st.write(f"- {user.username} ({user.email}) - role={user.role} - active={user.is_active}")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])
    
    with tab1:
        st.header("🔐 用户登录")
        
        with st.form("login_form"):
            email = st.text_input("邮箱", placeholder="请输入邮箱地址")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                remember_me = st.checkbox("记住我")
            with col2:
                st.write("")
            
            submitted = st.form_submit_button("登录", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("请填写邮箱和密码")
                elif not is_valid_email(email):
                    st.error("请输入有效的邮箱地址")
                else:
                    with st.spinner("正在验证..."):
                        success, message, user = login_user(email, password)
                        
                        if success:
                            set_session_user(user)
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(f"登录失败: {message}")
    
    with tab2:
        st.header("📝 用户注册")
        
        with st.form("register_form"):
            email = st.text_input("邮箱 *", placeholder="请输入邮箱地址")
            name = st.text_input("昵称", placeholder="请输入昵称（可选）")
            password = st.text_input("密码", type="password", placeholder="至少6个字符")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
            
            submitted = st.form_submit_button("注册", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("请填写邮箱和密码")
                elif not is_valid_email(email):
                    st.error("请输入有效的邮箱地址")
                elif len(password) < 6:
                    st.error("密码至少需要6个字符")
                elif password != confirm_password:
                    st.error("两次输入的密码不一致")
                else:
                    with st.spinner("正在注册..."):
                        success, message = register_user(email, password, name)
                        
                        if success:
                            st.success(message)
                            st.info("注册成功，请返回登录页面登录")
                        else:
                            st.error(f"注册失败: {message}")


def show_user_info():
    """显示用户信息侧边栏"""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        
        with st.sidebar:
            st.subheader("👤 用户信息")
            
            # 用户头像和基本信息
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("👤")
            with col2:
                st.write(f"**邮箱**: {user.get('email', user['username'])}")
                if user.get('name'):
                    st.write(f"**昵称**: {user['name']}")
            
            # 会员等级标签
            membership_color = {
                "free": "gray",
                "pro": "blue",
                "vip": "gold"
            }
            membership_label = {
                "free": "免费用户",
                "pro": "Pro会员",
                "vip": "VIP会员"
            }
            
            st.markdown(f"""
            **会员等级**: <span style='color: {membership_color.get(user['membership'], 'gray')}; font-weight: bold;'>
            {membership_label.get(user['membership'], user['membership'])}
            </span>
            """, unsafe_allow_html=True)
            
            # 角色
            if user['role'] == 'admin':
                st.markdown("**角色**: 🔧 管理员")
            
            # 配额信息
            if user['membership'] == 'vip' or user['role'] == 'admin':
                st.info("🎉 无限分析次数")
            else:
                st.write(f"**今日分析**: {user['today_used']} / {user['daily_limit']} 次")
            
            # 登录时间
            if user.get('last_login'):
                st.write(f"**上次登录**: {user['last_login']}")
            
            # 退出按钮
            if st.button("🚪 退出登录", use_container_width=True):
                from auth.auth import logout_user
                logout_user()
                st.rerun()
            
            # 管理员入口
            if user['role'] == 'admin':
                if st.button("🔧 管理员后台", use_container_width=True):
                    st.session_state["show_admin"] = True
                    st.rerun()
