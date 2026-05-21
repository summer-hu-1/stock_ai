"""
登录弹窗组件 - Login Modal Component
参考 Raphael AI 的登录界面设计：邮箱是核心用户身份标识
"""

import streamlit as st
from datetime import datetime, timedelta
from auth.auth import login_user, register_user, set_session_user, logout_user, get_user_by_email, is_valid_email
import extra_streamlit_components as argx

# 初始化 Cookie 管理器
def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state["cookie_manager"] = argx.CookieManager()
    return st.session_state["cookie_manager"]

@st.dialog("登录 / 注册", width="small")
def login_dialog():
    """使用 st.dialog 实现的登录弹窗，邮箱为核心凭据"""
    cookie_manager = get_cookie_manager()
    
    # 标签页切换
    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])
    
    with tab1:
        st.markdown("#### 👋 欢迎回来")
        email = st.text_input("邮箱", placeholder="请输入邮箱地址", key="login_email_dialog")
        password = st.text_input("密码", type="password", placeholder="请输入密码", key="login_password_dialog")
        
        remember_me = st.checkbox("记住我（30天内保持登录状态）", value=True, key="remember_me_dialog")
        
        st.markdown("")
        
        if st.button("立即登录", use_container_width=True, type="primary", key="login_btn_dialog"):
            if not email or not password:
                st.error("请填写邮箱和密码")
            elif not is_valid_email(email):
                st.error("请输入有效的邮箱地址")
            else:
                with st.spinner("正在验证..."):
                    success, message, user = login_user(email, password)
                    
                    if success:
                        set_session_user(user)
                        # 如果勾选了记住我，保存邮箱到 Cookie（30天）
                        if remember_me:
                            cookie_manager.set("saved_email", email, expires_at=datetime.now() + timedelta(days=30))
                        
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(f"登录失败: {message}")
        
    with tab2:
        st.markdown("#### ✨ 创建新账号")
        reg_email = st.text_input("邮箱 *", placeholder="请输入邮箱地址", key="reg_email_dialog",
                                   help="邮箱是您的唯一身份标识，用于登录")
        reg_name = st.text_input("昵称", placeholder="请输入昵称（可选）", key="reg_name_dialog")
        reg_password = st.text_input("密码", type="password", placeholder="至少6个字符", key="reg_password_dialog")
        reg_confirm = st.text_input("确认密码", type="password", placeholder="请再次输入密码", key="reg_confirm_dialog")
        
        if st.button("创建账号", use_container_width=True, type="primary", key="reg_btn_dialog"):
            if not reg_email or not reg_password:
                st.error("请填写邮箱和密码")
            elif not is_valid_email(reg_email):
                st.error("请输入有效的邮箱地址")
            elif len(reg_password) < 6:
                st.error("密码至少需要6个字符")
            elif reg_password != reg_confirm:
                st.error("两次输入的密码不一致")
            else:
                with st.spinner("正在注册..."):
                    success, message = register_user(reg_email, reg_password, reg_name)
                    if success:
                        st.success(message)
                        st.info("注册成功！请切换到登录页进行登录")
                    else:
                        st.error(f"注册失败: {message}")


def check_auto_login():
    """
    检查 Cookie 并尝试自动登录。
    
    由于 extra_streamlit_components.CookieManager 是异步的，
    第一个脚本运行可能返回 None，CookieManager 会在获取到 cookie 值后触发 rerun。
    使用 _auto_login_phase 状态标记来管理工作流程：
    - 未设置 → 第一次尝试（等待 CookieManager 响应）
    - "waiting" → CookieManager 已请求，等待 rerun
    - "done" → 已尝试完成（有或无 cookie）
    """
    if "user" in st.session_state and st.session_state["user"]:
        return True
    
    phase = st.session_state.get("_auto_login_phase", None)
    
    # 已完成尝试，不再重复
    if phase == "done":
        return False
    
    cookie_manager = get_cookie_manager()
    saved_email = cookie_manager.get("saved_email")
    
    if saved_email:
        # Cookie 值已加载，尝试自动登录
        user = get_user_by_email(saved_email)
        if user:
            set_session_user(user)
            st.session_state["_auto_login_phase"] = "done"
            return True
        else:
            # Cookie 中的邮箱无效，清除 cookie 和状态
            cookie_manager.delete("saved_email")
            st.session_state["_auto_login_phase"] = "done"
            return False
    
    # Cookie 值尚未加载（首次运行）
    if phase is None:
        st.session_state["_auto_login_phase"] = "waiting"
        # CookieManager 会在获取到 cookie 后自动触发 streamlit rerun
        return False
    
    # phase == "waiting": CookieManager 已经查询过，但没有 cookie（无 cookie 时不触发 rerun）
    st.session_state["_auto_login_phase"] = "done"
    return False


def show_login_modal():
    """
    显示登录/注册弹窗的触发器
    """
    if st.session_state.get("show_login_modal", False):
        st.session_state["show_login_modal"] = False
        login_dialog()


def show_user_info_updated():
    """显示用户信息侧边栏（包含模型选择）"""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        
        with st.sidebar:
            st.subheader("👤 用户信息")
            
            # 用户信息
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
            if user.get('last_login'):
                st.write(f"**上次登录**: {user['last_login']}")
            
            # 模型选择
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