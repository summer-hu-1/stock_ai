"""
登录弹窗组件 - Login Modal Component
参考 Raphael AI 的登录界面设计：邮箱是核心用户身份标识
"""

import streamlit as st
from datetime import datetime, timedelta
from auth.auth import login_user, register_user, set_session_user, logout_user, get_user_by_email, is_valid_email
import extra_streamlit_components as argx


def inject_login_dialog_css():
    """登录弹窗专属样式，避免受全局输入框样式影响"""
    st.markdown(
        """
        <style>
        [data-testid="stDialog"] {
            background: linear-gradient(180deg, rgba(6, 10, 20, 0.98), rgba(6, 11, 22, 0.96)) !important;
            border: 1px solid rgba(91, 130, 255, 0.18) !important;
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.38) !important;
        }

        [data-testid="stDialog"] > div {
            border-radius: 26px !important;
        }

        [data-testid="stDialog"] .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        [data-testid="stDialog"] .stTabs [data-baseweb="tab"] {
            border-radius: 14px 14px 0 0 !important;
            padding: 0.7rem 1rem !important;
        }

        [data-testid="stDialog"] .stTextInput label,
        [data-testid="stDialog"] .stCheckbox label {
            color: #c8d5f2 !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] > div {
            min-height: 58px !important;
            border-radius: 18px !important;
            background: linear-gradient(145deg, rgba(15, 22, 42, 0.96), rgba(11, 17, 31, 0.92)) !important;
            border: 1px solid rgba(77, 111, 196, 0.18) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.04),
                0 10px 24px rgba(0, 0, 0, 0.18) !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] > div:hover {
            border-color: rgba(84, 168, 255, 0.28) !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.04),
                0 12px 28px rgba(0, 0, 0, 0.22) !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] > div:focus-within {
            border-color: rgba(84, 168, 255, 0.52) !important;
            box-shadow:
                0 0 0 1px rgba(84, 168, 255, 0.16),
                0 0 24px rgba(84, 168, 255, 0.16),
                inset 0 1px 0 rgba(255,255,255,0.04) !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] input {
            color: #f4f7ff !important;
            font-size: 16px !important;
            padding-left: 2px !important;
            caret-color: #53b8ff !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] input::placeholder {
            color: rgba(182, 194, 220, 0.58) !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            min-height: auto !important;
            padding-right: 8px !important;
        }

        [data-testid="stDialog"] div[data-baseweb="input"] svg {
            color: #d9e4ff !important;
            opacity: 0.9;
        }

        [data-testid="stDialog"] input:-webkit-autofill,
        [data-testid="stDialog"] input:-webkit-autofill:hover,
        [data-testid="stDialog"] input:-webkit-autofill:focus,
        [data-testid="stDialog"] input:-webkit-autofill:active {
            -webkit-text-fill-color: #f4f7ff !important;
            caret-color: #53b8ff !important;
            transition: background-color 99999s ease-in-out 0s;
            box-shadow: 0 0 0 1000px rgba(14, 21, 40, 0.98) inset !important;
            border-radius: 14px !important;
        }

        [data-testid="stDialog"] .stCheckbox > label {
            gap: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# 初始化 Cookie 管理器
def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state["cookie_manager"] = argx.CookieManager()
    return st.session_state["cookie_manager"]

@st.dialog("登录 / 注册", width="small")
def login_dialog():
    """使用 st.dialog 实现的登录弹窗，邮箱为核心凭据"""
    cookie_manager = get_cookie_manager()
    inject_login_dialog_css()
    
    # 标签页切换
    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])
    
    with tab1:
        st.markdown("#### 👋 欢迎回来")
        email = st.text_input(
            "邮箱",
            placeholder="请输入邮箱地址",
            key="login_email_dialog",
            autocomplete="email",
        )
        password = st.text_input(
            "密码",
            type="password",
            placeholder="请输入密码",
            key="login_password_dialog",
            autocomplete="current-password",
        )
        
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
                        # 标记待设置 cookie（由主页面 check_auto_login 完成，
                        # 因为 dialog 内的 CookieManager 在 rerun 后可能已被销毁）
                        if remember_me:
                            st.session_state["_pending_cookie_email"] = email
                        
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(f"登录失败: {message}")
        
    with tab2:
        st.markdown("#### ✨ 创建新账号")
        reg_email = st.text_input(
            "邮箱 *",
            placeholder="请输入邮箱地址",
            key="reg_email_dialog",
            help="邮箱是您的唯一身份标识，用于登录",
            autocomplete="email",
        )
        reg_name = st.text_input(
            "昵称",
            placeholder="请输入昵称（可选）",
            key="reg_name_dialog",
            autocomplete="name",
        )
        reg_password = st.text_input(
            "密码",
            type="password",
            placeholder="至少6个字符",
            key="reg_password_dialog",
            autocomplete="new-password",
        )
        reg_confirm = st.text_input(
            "确认密码",
            type="password",
            placeholder="请再次输入密码",
            key="reg_confirm_dialog",
            autocomplete="new-password",
        )
        
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

    双保险策略：
    1. CookieManager（浏览器 cookie）— 主要持久化方式
    2. st.cache_resource（服务端缓存）— CookieManager 异步失败时的回退

    流程：
    - 首次运行 → 尝试读 cookie → 未加载则等待 CookieManager 触发 rerun
    - 有 cookie → 直接登录
    - 无 cookie → 3 次 retry 后放弃（防止无限等待）
    """
    if "user" in st.session_state and st.session_state["user"]:
        # 用户已登录：处理待写入的 cookie（来自 dialog 登录）
        pending_email = st.session_state.pop("_pending_cookie_email", None)
        if pending_email:
            try:
                cookie_manager = get_cookie_manager()
                cookie_manager.set("saved_email", pending_email, expires_at=datetime.now() + timedelta(days=30))
            except Exception:
                pass
        return True

    @st.cache_resource(ttl=86400)
    def _cached_user_lookup(email: str):
        """服务端缓存用户查询（24h），作为 CookieManager 失败时的回退"""
        return get_user_by_email(email)

    # 处理待写入的 cookie（首次登录后从 dialog 转交）
    pending_email = st.session_state.pop("_pending_cookie_email", None)
    if pending_email:
        try:
            cookie_manager = get_cookie_manager()
            cookie_manager.set("saved_email", pending_email, expires_at=datetime.now() + timedelta(days=30))
        except Exception:
            pass

    phase = st.session_state.get("_auto_login_phase", None)
    attempt = st.session_state.get("_auto_login_attempt", 0)

    # 安全阀：超过 3 次尝试仍未拿到 cookie，放弃自动登录
    if phase == "done" or attempt >= 3:
        st.session_state["_auto_login_phase"] = "done"
        return False

    cookie_manager = get_cookie_manager()
    saved_email = cookie_manager.get("saved_email")

    # --- 有 cookie 值 → 尝试登录 ---
    if saved_email and isinstance(saved_email, str) and '@' in saved_email:
        user = _cached_user_lookup(saved_email)
        if user:
            set_session_user(user)
            st.session_state["_auto_login_phase"] = "done"
            st.session_state["_auto_login_attempt"] = 0
            return True
        else:
            cookie_manager.delete("saved_email")
            st.session_state["_auto_login_phase"] = "done"
            return False

    # --- 首次运行，cookie 尚未加载 ---
    if phase is None:
        st.session_state["_auto_login_phase"] = "waiting"
        st.session_state["_auto_login_attempt"] = 1
        return False

    # --- 仍在等待 CookieManager 响应 ---
    st.session_state["_auto_login_attempt"] = attempt + 1
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
