"""
登录页面组件 - Login Page Components
提供登录和注册界面
"""

import streamlit as st
from auth.auth import login_user, register_user, set_session_user


def show_login_page():
    """显示登录页面"""
    try:
        st.set_page_config(page_title="AI股票复盘系统 - 登录", page_icon="🔐", layout="centered")
    except Exception as e:
        print(f"st.set_page_config 异常: {type(e).__name__}: {e}")
        st.error(f"页面配置异常: {e}")

    with st.expander("🔍 调试信息", expanded=False):
        from database.db import is_streamlit_cloud, get_db, get_all_users, get_user_count
        st.write(f"**Streamlit Cloud 环境**: {is_streamlit_cloud()}")

        db = next(get_db())
        user_count = get_user_count(db)
        st.write(f"**数据库用户数**: {user_count}")

        if user_count > 0:
            all_users = get_all_users(db)
            st.write("**所有用户列表**:")
            for user in all_users:
                st.write(f"- {user.username} ({user.email}) - role={user.role} - active={user.is_active}")
        db.close()

    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])

    with tab1:
        st.header("🔐 用户登录")

        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")

            col1, col2 = st.columns([1, 1])
            with col1:
                remember_me = st.checkbox("记住我")
            with col2:
                st.write("")

            submitted = st.form_submit_button("登录", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("请填写用户名和密码")
                else:
                    with st.spinner("正在验证..."):
                        print(f"登录尝试: username={username}, password_length={len(password) if password else 0}")
                        result = login_user(username, password)
                        print(f"login_user 返回结果: {result}, len={len(result)}")
                        import base64
                        import json

                        if len(result) == 4:
                            success, message, user, token = result
                            print(f"解包4元素: success={success}, message={message}, user type={type(user)}, user={user is not None}, token={token}")
                            print(f"调用 set_session_user: user={user}")
                            if user is not None:
                                set_session_user(user, token)
                                print(f"set_session_user 后: session_state['user']={st.session_state.get('user')}")
                                session_data = base64.b64encode(json.dumps(user).encode('utf-8')).decode('utf-8')
                                st.query_params["s"] = session_data
                                st.session_state["show_login"] = False
                                st.success(message + " 正在跳转...")
                                st.rerun()
                            else:
                                st.error(f"登录失败: user is None")
                        else:
                            success, message, user = result
                            print(f"解包3元素: success={success}, message={message}, user={user}")
                            if success:
                                print(f"调用 set_session_user: user={user}")
                                set_session_user(user)
                                print(f"set_session_user 后: session_state['user']={st.session_state.get('user')}")
                                st.session_state["show_login"] = False
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(f"登录失败: {message}")

    with tab2:
        st.header("📝 用户注册")

        with st.form("register_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            email = st.text_input("邮箱", placeholder="请输入邮箱（可选）")
            name = st.text_input("姓名", placeholder="请输入姓名（可选）")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")

            submitted = st.form_submit_button("注册", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("请填写用户名和密码")
                elif password != confirm_password:
                    st.error("两次输入的密码不一致")
                else:
                    with st.spinner("正在注册..."):
                        success, message = register_user(username, password, email, name)

                        if success:
                            st.success(message)
                            st.info("注册成功，请返回登录页面登录")
                        else:
                            st.error(f"注册失败: {message}")


def show_user_info():
    """显示用户信息侧边栏"""
    # 调试信息
    with st.sidebar.expander("🔍 会话状态调试", expanded=False):
        st.write(f"session_state keys: {list(st.session_state.keys())}")
        st.write(f"user in session_state: {'user' in st.session_state}")
        st.write(f"user value: {st.session_state.get('user')}")
        st.write(f"show_login: {st.session_state.get('show_login')}")
    
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]

        st.sidebar.subheader("👤 用户信息")

        col1, col2 = st.sidebar.columns([1, 3])
        with col1:
            st.write("👤")
        with col2:
            st.write(f"**用户名**: {user.get('username', '')}")
            if user.get('name'):
                st.write(f"**姓名**: {user['name']}")

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

        st.sidebar.markdown(f"""
        **会员等级**: <span style='color: {membership_color.get(user.get('membership'), 'gray')}; font-weight: bold;'>
        {membership_label.get(user.get('membership'), user.get('membership', 'free'))}
        </span>
        """, unsafe_allow_html=True)

        if user.get('role') == 'admin':
            st.sidebar.markdown("**角色**: 🔧 管理员")

        if user.get('membership') == 'vip' or user.get('role') == 'admin':
            st.sidebar.info("🎉 无限分析次数")
        else:
            st.sidebar.write(f"**今日分析**: {user.get('today_used', 0)} / {user.get('daily_limit', 10)} 次")

        if user.get('last_login'):
            st.sidebar.write(f"**上次登录**: {user['last_login']}")

        if st.sidebar.button("🚪 退出登录", use_container_width=True):
            from auth.auth import logout_user
            logout_user()
            st.rerun()

        if user.get('role') == 'admin':
            if st.sidebar.button("🔧 管理员后台", use_container_width=True):
                st.session_state["show_admin"] = True
                st.rerun()
    else:
        st.sidebar.info("👤 未登录用户")
        if st.sidebar.button("🔐 登录 / 注册", use_container_width=True):
            st.session_state["show_login"] = True
            st.rerun()