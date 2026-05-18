"""
登录弹窗组件 - Login Modal Component
参考 Raphael AI 的登录界面设计
"""

import streamlit as st
from auth.auth import login_user, register_user, set_session_user, logout_user

def show_login_modal():
    """显示登录/注册弹窗（使用Streamlit原生组件）"""
    if "show_login_modal" not in st.session_state:
        st.session_state["show_login_modal"] = False
    
    if st.session_state["show_login_modal"]:
        # 清空主页面内容，只显示登录弹窗
        st.empty()
        
        # 使用Streamlit原生布局创建居中的登录表单
        st.markdown(
            """
            <style>
            .login-container {
                max-width: 420px;
                margin: 0 auto;
                padding: 40px;
                background: linear-gradient(145deg, #2d2d2d, #1f1f1f);
                border-radius: 20px;
                box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # 创建三列布局，中间列显示登录表单
        col1, col_main, col2 = st.columns([1, 2, 1])
        
        with col_main:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            # 弹窗头部
            header_col1, header_col2 = st.columns([4, 1])
            with header_col1:
                st.subheader("欢迎回来")
            with header_col2:
                close_button = st.button("✕", key="close_login_modal", help="关闭")
                if close_button:
                    st.session_state["show_login_modal"] = False
                    st.rerun()
            
            # 标签页切换
            tab1, tab2 = st.tabs(["登录", "注册"])
            
            with tab1:
                st.markdown("---")
                
                username = st.text_input("用户名", placeholder="请输入用户名", key="login_username")
                password = st.text_input("密码", type="password", placeholder="请输入密码", key="login_password")
                
                col_remember, _ = st.columns([1, 3])
                with col_remember:
                    remember_me = st.checkbox("记住我")
                
                st.markdown("")
                
                if st.button("登录", use_container_width=True, type="primary", key="login_btn"):
                    if not username or not password:
                        st.error("请填写用户名和密码")
                    else:
                        with st.spinner("正在验证..."):
                            success, message, user = login_user(username, password)
                            
                            if success:
                                set_session_user(user)
                                st.session_state["show_login_modal"] = False
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(f"登录失败: {message}")
                
                st.markdown("---")
                st.caption("忘记密码？联系管理员重置")
            
            with tab2:
                st.markdown("---")
                
                username = st.text_input("用户名", placeholder="请输入用户名", key="reg_username")
                email = st.text_input("邮箱", placeholder="请输入邮箱", key="reg_email")
                name = st.text_input("姓名", placeholder="请输入姓名（可选）", key="reg_name")
                password = st.text_input("密码", type="password", placeholder="请输入密码", key="reg_password")
                confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码", key="reg_confirm_password")
                
                st.markdown("")
                
                if st.button("注册", use_container_width=True, type="primary", key="reg_btn"):
                    if not username or not password:
                        st.error("请填写用户名和密码")
                    elif password != confirm_password:
                        st.error("两次输入的密码不一致")
                    else:
                        with st.spinner("正在注册..."):
                            success, message = register_user(username, password, email, name)
                            
                            if success:
                                st.success(message)
                                st.info("注册成功，请返回登录")
                            else:
                                st.error(f"注册失败: {message}")
            
            st.markdown('</div>', unsafe_allow_html=True)


def show_user_info_updated():
    """显示用户信息侧边栏（包含模型选择）"""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        
        with st.sidebar:
            st.subheader("👤 用户信息")
            
            # 用户头像和基本信息
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("👤")
            with col2:
                st.write(f"**用户名**: {user['username']}")
                if user['name']:
                    st.write(f"**姓名**: {user['name']}")
            
            # 会员等级标签
            membership_color = {
                "free": "gray",
                "pro": "#4a9eff",
                "vip": "#ffd700"
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
            if user['last_login']:
                st.write(f"**上次登录**: {user['last_login']}")
            
            # 模型选择（移到这里）
            st.markdown("---")
            st.subheader("🤖 AI模型")
            from core.model_config import (
                get_all_models, 
                get_current_model, 
                set_current_model, 
                format_price_info
            )
            
            models = get_all_models()
            current_model = get_current_model()
            
            model_options = {f"{m['display_name']} - {m['description']}": m["name"] for m in models}
            
            selected_model_display = next(k for k, v in model_options.items() if v == current_model)
            
            selected_model = st.selectbox(
                "选择模型",
                options=list(model_options.keys()),
                index=list(model_options.values()).index(current_model),
                key="model_selector_sidebar"
            )
            
            selected_model_name = model_options[selected_model]
            selected_model_config = next(m for m in models if m["name"] == selected_model_name)
            
            if selected_model_name != current_model:
                if set_current_model(selected_model_name):
                    st.success(f"✅ 已切换到 {selected_model_config['display_name']}")
                    st.rerun()
            
            st.caption(f"{format_price_info(selected_model_config)} | Max Tokens: {selected_model_config['max_tokens']}")
            
            # 退出按钮
            st.markdown("---")
            if st.button("🚪 退出登录", use_container_width=True):
                logout_user()
                st.rerun()
            
            # 管理员入口
            if user['role'] == 'admin':
                if st.button("🔧 管理员后台", use_container_width=True):
                    st.session_state["show_admin"] = True
                    st.rerun()
        return True
    return False
