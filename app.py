import streamlit as st
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from admin_auth.db import init_db as init_admin_db
from admin_auth.service import AdminService

init_admin_db()

created, admin_username = AdminService.init_default_admin()
if created:
    st.sidebar.success(f"✅ 已创建默认管理员: {admin_username}")

# 先检查登录状态
from auth.auth import is_logged_in, get_user_quota_info

# 导入业务模块（所有人都能进入主页面，游客模式也可以使用）
from modules.storage import init_db, save_analysis, save_market_sentiment, get_all_companies, save_company_info, get_company_by_code, get_all_stocks, get_stock_history, get_market_sentiment_history, get_cached_market_sentiment
from deepseek import stock_review, check_balance
from modules.market_data import get_stock_data, get_stock_data_fast
from modules.market_sentiment import get_market_sentiment, get_hot_sectors, analyze_sentiment

init_db()

def get_current_username():
    """获取当前用户名，未登录则返回 'guest'"""
    if "user" in st.session_state and st.session_state["user"]:
        return st.session_state["user"]["username"]
    return "guest"

def load_company_data():
    """从 akshare 加载全量公司信息到数据库"""
    import akshare as ak
    try:
        with st.spinner("📊 正在加载公司数据..."):
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                companies = []
                for _, row in df.iterrows():
                    companies.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "industry": str(row.get("行业", "")) if "行业" in row else ""
                    })
                save_company_info(companies)
                st.success(f"✅ 已加载 {len(companies)} 条公司信息")
                return True
    except Exception as e:
        st.error(f"加载公司数据失败: {e}")
    return False


def get_company_list():
    """获取公司列表，用于下拉选择"""
    companies = get_all_companies()
    if not companies:
        return None
    return companies


def _render_short_term_card(stock_code, stock_data):
    """
    渲染短线状态卡片：
    1. 从本地 CSV 日线数据加载最近5日走势
    2. 调用 ShortTermStateEngine 分析
    3. 以 HTML 卡片展示状态、得分、剧本
    """
    import os
    import pandas as pd

    # 查找本地 CSV 日线文件
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'cn', 'daily')
    if not os.path.exists(data_dir):
        st.warning("📭 暂无本地日线数据，无法生成短线状态卡片。请先在「行情数据」Tab下载。")
        return

    # 按市场目录查找
    csv_path = None
    for market_dir in os.listdir(data_dir):
        market_path = os.path.join(data_dir, market_dir)
        if not os.path.isdir(market_path):
            continue
        candidate = os.path.join(market_path, f"{stock_code}.csv")
        if os.path.exists(candidate):
            csv_path = candidate
            break

    if not csv_path:
        st.info("📭 该股票暂无本地日线数据，无法生成短线状态卡片。")
        return

    try:
        df = pd.read_csv(csv_path)
        if df.empty or len(df) < 3:
            st.info("📭 日线数据不足（需至少3天），无法生成短线状态卡片。")
            return

        from engines.structure_engine.short_term_state import get_short_term_state, daily_from_dataframe

        daily_5 = daily_from_dataframe(df, n=5)
        state = get_short_term_state(daily_5)

        if state["state_key"] == "insufficient_data":
            st.info(f"📭 {state['narrative']}")
            return

        # ---- 渲染 HTML 卡片 ----
        risk_color_map = {"low": "#4ecdc4", "medium": "#f5a623", "high": "#e74c3c"}
        state_color = risk_color_map.get(state["risk"], "#888")
        sc = state["score_components"]

        card_html = f"""
<div style="background:#0f0f1a; border-radius:16px; padding:20px; border-left:6px solid {state_color}; margin:12px 0;">
    <!-- 头部 -->
    <div style="display:flex; align-items:baseline; justify-content:space-between;">
        <div>
            <span style="font-size:12px; color:#888; letter-spacing:1px;">📊 短线状态</span>
            <div style="font-size:28px; font-weight:700; color:{state_color}; margin-top:4px;">
                {state['state_cn']}
            </div>
        </div>
        <div style="background:#1e1e2e; padding:4px 16px; border-radius:40px; font-size:14px; color:#ddd;">
            强度 <b style="color:{state_color}">{state['strength']}</b>
        </div>
    </div>

    <!-- 叙事 -->
    <div style="background:#1a1a24; border-radius:12px; padding:12px; margin-top:16px;">
        <div style="color:#aaa; font-size:11px;">市场行为</div>
        <div style="color:#eee; font-size:14px; margin-top:4px; line-height:1.6;">
            {state['narrative']}
        </div>
    </div>

    <!-- 得分 -->
    <div style="display:flex; gap:16px; margin-top:14px; font-size:11px; color:#777;">
        <span>趋势 {sc['trend_score']}</span> |
        <span>量能 {sc['volume_score']}</span> |
        <span>动量 {sc['momentum_score']}</span> |
        <span>风险 {sc['risk_score']}</span>
    </div>

    <!-- 剧本 -->
    <div style="margin-top:16px; border-top:1px solid #262636; padding-top:12px;">
        <div style="font-size:13px; font-weight:600; color:#ddd;">🎯 短线剧本</div>
        <div style="margin-top:8px;">
            <div style="background:#1a2a1a; color:#aaffaa; padding:8px 12px; border-radius:8px; font-size:13px;">
                ✅ {state['scenario_bullish']}
            </div>
            <div style="background:#2a1a1a; color:#ffaaaa; padding:8px 12px; border-radius:8px; font-size:13px; margin-top:8px;">
                ⚠️ {state['scenario_bearish']}
            </div>
        </div>
    </div>

    <!-- 风险 -->
    <div style="margin-top:12px; font-size:12px; color:#ffaa66; background:#2a1f1a; padding:6px 12px; border-radius:8px;">
        ⚠️ {state['risk_note']}
    </div>

    <!-- 标签 -->
    <div style="margin-top:10px; display:flex; gap:6px;">
"""
        for tag in state["tags"]:
            tag_color = "#4ecdc4" if state["risk"] == "low" else "#f5a623" if state["risk"] == "medium" else "#e74c3c"
            card_html += f'<span style="background:#1e1e2e; color:{tag_color}; padding:2px 10px; border-radius:20px; font-size:11px;">{tag}</span>'

        card_html += """
    </div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)

        # 联动：如果状态是恐慌/退潮，额外警示
        if state["state_key"] in ("panic_distribution", "decay"):
            st.error("🚨 该股当前处于高风险状态，请谨慎操作！")

    except Exception as e:
        st.caption(f"短线状态卡片生成失败: {e}")


NAV_ITEMS = [
    {
        "key": "market_state",
        "label": "市场状态",
        "icon": "◉",
        "hint": "全市场扫描",
        "index": "01",
        "title": "Market State",
        "subtitle": "先看情绪周期、主线方向和风险级别，像交易终端一样判断市场温度。 ",
        "signal": "SCAN / RISK / FLOW",
    },
    {
        "key": "stock_state",
        "label": "个股状态",
        "icon": "◎",
        "hint": "单股驾驶舱",
        "index": "02",
        "title": "Stock State",
        "subtitle": "保留现有个股快评逻辑，只升级成更像 AI 驾驶舱的导航入口。",
        "signal": "STOCK / AI / EXECUTE",
    },
    {
        "key": "attack_board",
        "label": "今日进攻",
        "icon": "▲",
        "hint": "进攻目标池",
        "index": "03",
        "title": "Attack Board",
        "subtitle": "综合趋势、量能、龙头、情绪多因子扫描全市场，输出今日最值得进攻的 TOP5 目标池。",
        "signal": "ATTACK / RANK / EXECUTE",
    },
    {
        "key": "market_timeline",
        "label": "市场时间线",
        "icon": "◌",
        "hint": "历史回放",
        "index": "04",
        "title": "Market Timeline",
        "subtitle": "把历史记录和情绪快照做成连续观察面板，弱化后台感，增强终端感。",
        "signal": "MEMORY / LOG / REVIEW",
    },
    {
        "key": "data_center",
        "label": "数据中心",
        "icon": "▣",
        "hint": "本地日线中心",
        "index": "05",
        "title": "Data Center",
        "subtitle": "维持现有行情数据页能力，用更统一的终端外观承载同步和浏览操作。",
        "signal": "DATA / SYNC / STORAGE",
    },
]

NAV_META = {item["key"]: item for item in NAV_ITEMS}


def inject_terminal_nav_css():
    """顶部导航与页面驾驶舱风格"""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(46, 118, 255, 0.14), transparent 28%),
                radial-gradient(circle at top right, rgba(255, 128, 62, 0.08), transparent 24%),
                linear-gradient(180deg, #060914 0%, #090d1a 32%, #070b16 100%);
            color: #edf3ff;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent;
        }

        [data-testid="stHeader"] {
            background: rgba(6, 9, 20, 0.68);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid rgba(104, 141, 255, 0.08);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(8, 12, 24, 0.95), rgba(10, 14, 28, 0.9));
            border-right: 1px solid rgba(105, 136, 255, 0.08);
        }

        [data-testid="stAppViewBlockContainer"] {
            padding-top: 1.25rem;
        }

        .terminal-brand-shell {
            position: relative;
            overflow: hidden;
            padding: 20px 22px;
            border-radius: 24px;
            border: 1px solid rgba(104, 141, 255, 0.16);
            background: linear-gradient(135deg, rgba(14, 20, 38, 0.92), rgba(8, 12, 26, 0.88));
            box-shadow:
                0 18px 48px rgba(0, 0, 0, 0.32),
                inset 0 1px 0 rgba(255, 255, 255, 0.04),
                inset 0 0 40px rgba(50, 112, 255, 0.05);
            backdrop-filter: blur(16px);
            margin-bottom: 12px;
        }

        .terminal-brand-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 15% 10%, rgba(0, 212, 255, 0.12), transparent 28%),
                radial-gradient(circle at 85% 25%, rgba(255, 140, 76, 0.10), transparent 20%);
            pointer-events: none;
        }

        .terminal-brand-kicker {
            font-size: 11px;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: #7f93c9;
            margin-bottom: 8px;
        }

        .terminal-brand-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }

        .terminal-brand-title {
            font-size: 34px;
            line-height: 1.05;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #f5f8ff;
            margin: 0;
        }

        .terminal-brand-desc {
            margin-top: 8px;
            color: #9dafd8;
            font-size: 14px;
            line-height: 1.6;
        }

        .terminal-status-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border-radius: 999px;
            border: 1px solid rgba(91, 130, 255, 0.22);
            background: rgba(11, 18, 34, 0.78);
            color: #d7e5ff;
            font-size: 12px;
            white-space: nowrap;
            box-shadow: inset 0 0 22px rgba(53, 110, 255, 0.08);
        }

        .terminal-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: linear-gradient(180deg, #53b8ff, #2d7bff);
            box-shadow: 0 0 12px rgba(83, 184, 255, 0.85);
        }

        div.stButton > button {
            min-height: 48px;
            border-radius: 999px;
            border: 1px solid rgba(102, 122, 178, 0.22);
            background: rgba(16, 22, 41, 0.78);
            color: #dfe9ff;
            font-weight: 700;
            letter-spacing: 0.01em;
            transition:
                transform 0.16s ease,
                border-color 0.18s ease,
                box-shadow 0.18s ease,
                background 0.18s ease;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.03),
                0 8px 22px rgba(0, 0, 0, 0.16);
        }

        div.stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(84, 170, 255, 0.56);
            box-shadow:
                0 12px 26px rgba(0, 0, 0, 0.22),
                0 0 0 1px rgba(84, 170, 255, 0.12),
                0 0 24px rgba(84, 170, 255, 0.14);
            background: rgba(20, 28, 52, 0.92);
        }

        div.stButton > button[kind="primary"] {
            border: 1px solid rgba(87, 158, 255, 0.72);
            background:
                linear-gradient(135deg, rgba(24, 84, 255, 0.92), rgba(0, 204, 255, 0.82)),
                rgba(15, 24, 48, 0.92);
            color: #ffffff;
            box-shadow:
                0 0 0 1px rgba(106, 174, 255, 0.26),
                0 12px 26px rgba(16, 96, 255, 0.28),
                0 0 32px rgba(0, 170, 255, 0.18);
        }

        .terminal-nav-caption {
            text-align: center;
            font-size: 11px;
            color: #7284ab;
            margin-top: 8px;
            margin-bottom: 6px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            transition: color 0.18s ease, transform 0.18s ease;
        }

        .terminal-nav-caption.active {
            color: #d9e8ff;
            transform: translateY(-1px);
        }

        .terminal-page-hero {
            position: relative;
            overflow: hidden;
            padding: 22px 24px;
            border-radius: 24px;
            border: 1px solid rgba(103, 131, 204, 0.16);
            background: linear-gradient(145deg, rgba(10, 16, 31, 0.88), rgba(9, 13, 24, 0.78));
            box-shadow:
                0 18px 44px rgba(0, 0, 0, 0.26),
                inset 0 1px 0 rgba(255, 255, 255, 0.03);
            margin: 14px 0 20px;
            animation: cockpit-enter 0.32s ease-out;
            backdrop-filter: blur(14px);
        }

        .terminal-page-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(53, 117, 255, 0.12), transparent 24%),
                linear-gradient(135deg, transparent 62%, rgba(255, 145, 77, 0.10));
            pointer-events: none;
        }

        .terminal-page-kicker {
            color: #7588b5;
            text-transform: uppercase;
            letter-spacing: 0.24em;
            font-size: 11px;
            margin-bottom: 8px;
        }

        .terminal-page-row {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }

        .terminal-page-title {
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #f4f8ff;
            margin: 0;
        }

        .terminal-page-desc {
            margin-top: 8px;
            color: #9aacd4;
            font-size: 14px;
            line-height: 1.7;
            max-width: 880px;
        }

        .terminal-page-index {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border-radius: 16px;
            border: 1px solid rgba(94, 126, 208, 0.18);
            background: rgba(11, 18, 34, 0.78);
            color: #dfe9ff;
            font-size: 13px;
            font-weight: 700;
            box-shadow: inset 0 0 24px rgba(77, 125, 255, 0.05);
        }

        .terminal-page-signal {
            margin-top: 10px;
            font-size: 11px;
            letter-spacing: 0.18em;
            color: #8ea5d8;
            text-transform: uppercase;
        }

        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stAlert"] {
            border-radius: 18px;
        }

        div[data-testid="stExpander"] {
            border: 1px solid rgba(103, 127, 191, 0.16);
            background: rgba(10, 15, 28, 0.62);
            backdrop-filter: blur(12px);
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(103, 127, 191, 0.14);
            background: rgba(11, 17, 31, 0.68);
            backdrop-filter: blur(10px);
            padding: 10px 12px;
        }

        @keyframes cockpit-enter {
            from {
                opacity: 0;
                transform: translateY(10px) scale(0.992);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_terminal_brand():
    """驾驶舱顶部品牌区"""
    status_text = (
        f"已登录 · {get_current_username()}"
        if is_logged_in()
        else "游客模式 · Terminal Access"
    )
    st.markdown(
        f"""
        <div class="terminal-brand-shell">
            <div class="terminal-brand-kicker">AI Market Cockpit</div>
            <div class="terminal-brand-row">
                <div>
                    <div class="terminal-brand-title">AI 股票市场终端</div>
                    <div class="terminal-brand-desc">
                        TradingView 风格导航 + Bloomberg 终端质感，保留原业务逻辑，仅升级导航与切换体验。
                    </div>
                </div>
                <div class="terminal-status-chip">
                    <span class="terminal-status-dot"></span>
                    {status_text}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_terminal_nav():
    """顶部胶囊导航"""
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = NAV_ITEMS[0]["key"]

    current_page = st.session_state["active_page"]
    nav_cols = st.columns(len(NAV_ITEMS))

    for col, item in zip(nav_cols, NAV_ITEMS):
        with col:
            is_active = current_page == item["key"]
            if st.button(
                f"{item['icon']} {item['label']}",
                key=f"nav_{item['key']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if not is_active:
                    st.session_state["active_page"] = item["key"]
                    st.rerun()
            st.markdown(
                f'<div class="terminal-nav-caption{" active" if is_active else ""}">{item["hint"]}</div>',
                unsafe_allow_html=True,
            )

    return st.session_state["active_page"]


def render_page_intro(page_key):
    """页面切换时的驾驶舱页头"""
    meta = NAV_META[page_key]
    st.markdown(
        f"""
        <div class="terminal-page-hero">
            <div class="terminal-page-kicker">Page {meta["index"]} / {meta["signal"]}</div>
            <div class="terminal-page-row">
                <div>
                    <div class="terminal-page-title">{meta["label"]}</div>
                    <div class="terminal-page-desc">{meta["subtitle"]}</div>
                    <div class="terminal-page-signal">{meta["title"]}</div>
                </div>
                <div class="terminal-page-index">Terminal View {meta["index"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.set_page_config(page_title="AI看盘助手", page_icon="📈", layout="wide")
from ui.theme import inject_theme
inject_terminal_nav_css()
inject_theme()

# 初始化 Cookie 管理器并检查自动登录
from auth.modal import check_auto_login, show_login_modal
check_auto_login()

# 顶部栏
col_title, col_login = st.columns([9, 1])
with col_title:
    render_terminal_brand()
with col_login:
    # 登录按钮（游客模式）
    if "user" not in st.session_state or not st.session_state["user"]:
        if st.button("🔐 登录", key="login_button_top"):
            st.session_state["show_login_modal"] = True
            st.rerun()

# 显示登录弹窗（使用 st.dialog）
show_login_modal()

# 显示用户信息侧边栏（包含模型选择）
from auth.modal import show_user_info_updated
user_logged_in = show_user_info_updated()

# 如果是游客模式，显示游客配额信息
if not user_logged_in:
    with st.sidebar:
        st.subheader("👤 游客模式")
        st.success("✅ 自由使用模式开启")
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
            key="model_selector_guest"
        )
        
        selected_model_name = model_options[selected_model]
        selected_model_config = next(m for m in models if m["name"] == selected_model_name)
        
        if selected_model_name != current_model:
            if set_current_model(selected_model_name):
                st.success(f"✅ 已切换到 {selected_model_config['display_name']}")
                st.rerun()
    
    # 配额信息
    if not user_logged_in:
        guest_used = st.session_state.get("guest_used", 0)
        st.sidebar.info(f"🎯 游客模式（剩余 {max(0, 5 - guest_used)}/5 次）")
    else:
        quota_info = get_user_quota_info()
        if quota_info['unlimited']:
            st.sidebar.info("🎉 无限分析次数")
        else:
            st.sidebar.caption(f"今日配额: {quota_info['used']}/{quota_info['limit']}")

current_page = render_terminal_nav()
render_page_intro(current_page)

if current_page == "stock_state":
    from ui.theme import inject_theme, state_tag, strength_bar

    inject_theme()
    st.markdown('<span class="section-title">⚡ 个股快评</span>', unsafe_allow_html=True)

    from ui.components import stock_selector_with_market
    stock, stock_name, market = stock_selector_with_market(
        key_prefix="single",
        default_market="cn",
        show_refresh=True,
        on_refresh_callback=load_company_data
    )

    col1, col2 = st.columns([4, 2])
    with col1:
        selected_date = st.date_input(
            "目标日期",
            value=datetime.now(),
            key="stock_state_selected_date",
            help="极速模式下可选择回看日期",
        )
    with col2:
        data_mode = st.radio(
            "模式",
            ["⚡极速", "📈标准", "🔍完整"],
            index=2,
            horizontal=True,
            label_visibility="collapsed"
        )

    data_mode_mapping = {
        "⚡极速": "⚡ 极速模式（仅个股数据）",
        "📈标准": "📈 标准模式（个股+市场情绪）",
        "🔍完整": "🔍 完整模式（全部数据）"
    }
    selected_data_mode = data_mode_mapping[data_mode]

    if st.button("🚀 开始分析", key="analyze_single", type="primary"):
        from auth.auth import can_analyze, record_analysis_usage
        can_do, msg = can_analyze()
        if not can_do:
            st.error(msg)
        elif not stock:
            st.error("请输入股票代码")
        else:
            progress_bar = st.progress(0, text="准备开始...")

            progress_bar.progress(10, text="📈 获取个股数据...")
            with st.spinner("📈 正在获取个股数据..."):
                if selected_data_mode == "⚡ 极速模式（仅个股数据）":
                    stock_data = get_stock_data_fast(stock, target_date=selected_date)
                else:
                    stock_data = get_stock_data(stock)

            if not stock_data:
                st.error(f"未找到股票代码: {stock}")
                progress_bar.progress(100, text="❌ 分析失败")
            else:
                progress_bar.progress(30, text="✅ 个股数据获取成功")

                sentiment_data = None
                hot_sectors = None

                if selected_data_mode == "⚡ 极速模式（仅个股数据）":
                    sentiment_data = {"market_mood": "待获取", "limit_up_count": 0, "limit_down_count": 0,
                        "bomb_rate": 0.0, "avg_change": 0.0, "rising_count": 0, "falling_count": 0,
                        "flat_count": 0, "total_count": 0, "rise_ratio": 0.0, "strong_count": 0,
                        "weak_count": 0, "total_volume": 0.0, "market_cap": 0.0}
                    hot_sectors = []
                    progress_bar.progress(40, text="✅ 准备完成，开始AI分析...")
                elif selected_data_mode == "📈 标准模式（个股+市场情绪）":
                    progress_bar.progress(40, text="📊 获取市场情绪...")
                    with st.spinner("📊 正在获取市场情绪..."):
                        sentiment_data = get_market_sentiment(use_cache=False)
                    progress_bar.progress(60, text="✅ 市场情绪数据获取成功")
                    hot_sectors = []
                    progress_bar.progress(70, text="✅ 数据准备完成...")
                else:
                    progress_bar.progress(40, text="📊 获取市场情绪...")
                    with st.spinner("📊 正在获取市场情绪..."):
                        sentiment_data = get_market_sentiment(use_cache=False)
                    progress_bar.progress(55, text="✅ 市场情绪获取成功")
                    progress_bar.progress(60, text="🔥 获取热门板块...")
                    with st.spinner("🔥 正在获取热门板块..."):
                        hot_sectors = get_hot_sectors(use_cache=False)
                    progress_bar.progress(75, text="✅ 数据准备完成...")

                progress_bar.progress(80, text="🤖 AI正在分析...")
                with st.spinner("🤖 AI正在分析中..."):
                    result = stock_review(stock, stock_data, sentiment_data, hot_sectors)

                record_analysis_usage()

                progress_bar.progress(90, text="💾 保存分析结果...")
                if sentiment_data and sentiment_data.get('market_mood') is not None:
                    mode = selected_data_mode.split('（')[0].strip()
                    market_mood = sentiment_data.get('market_mood', '未知')
                    if market_mood == "待获取":
                        market_mood = "极速模式"
                    save_analysis(stock_data, result, market_mood, mode, get_current_username())

                progress_bar.progress(100, text="✅ 分析完成！")
                st.success("✅ 分析完成")

                # ---- 短线状态卡片（优先展示） ----
                _render_short_term_card(stock, stock_data)

                # ---- AI复盘（折叠） ----
                with st.expander("🎯 AI复盘详情", expanded=False):
                    st.markdown(result)

                # ---- 数据预览（折叠） ----
                with st.expander("📊 个股数据", expanded=False):
                    st.json(stock_data)

                st.download_button(
                    label="📥 下载报告",
                    data=result,
                    file_name=f"复盘报告_{stock}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

elif current_page == "market_state":
    from ui.theme import inject_theme, state_tag, strength_bar, CYCLE_COLORS, CYCLE_HEX, RISK_HEX
    import json as _json

    inject_theme()

    if "dashboard_result" not in st.session_state:
        st.session_state["dashboard_result"] = None

    _, top_right = st.columns([6, 1])
    with top_right:
        if st.button("⚡ 刷新", key="dash_refresh"):
            st.session_state["dashboard_result"] = None
            st.session_state.pop("script_parsed", None)
            st.rerun()

    if st.session_state["dashboard_result"] is None:
        with st.spinner("📡 正在扫描全市场状态..."):
            from modules.market_engine import run_market_emotion_analysis
            st.session_state["dashboard_result"] = run_market_emotion_analysis()
            if st.session_state["dashboard_result"].get("script_prompt"):
                try:
                    from modules.market_engine import generate_ai_script
                    script = generate_ai_script(st.session_state["dashboard_result"]["script_prompt"])
                    st.session_state["script_result"] = script
                except Exception:
                    st.session_state["script_result"] = None
        st.rerun()

    R = st.session_state["dashboard_result"]
    cycle = R["cycle"]
    cycle_color = CYCLE_HEX.get(cycle, "#888")
    cycle_tag_color = CYCLE_COLORS.get(cycle, "blue")
    danger_signals = R.get("danger_signals", [])
    sentiment = R.get("sentiment", {})
    trend = R.get("trend", "")

    risk_level = "low"
    if danger_signals:
        severities = [s["严重程度"] for s in danger_signals]
        if "高" in severities:
            risk_level = "high"
        elif len(danger_signals) >= 2:
            risk_level = "medium"

    risk_text = {"low": "低", "medium": "中", "high": "高"}[risk_level]
    risk_hex = RISK_HEX[risk_level]
    risk_label_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}[risk_level]

    mainline_text = R.get("main_sector", "") or "暂无主线"

    # ---- Parse AI script for rich data ----
    script_parsed = {}
    if st.session_state.get("script_parsed"):
        script_parsed = st.session_state["script_parsed"]
    elif st.session_state.get("script_result"):
        try:
            raw = st.session_state["script_result"]
            if raw.startswith("```"):
                raw = raw.split("```", 1)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            script_parsed = _json.loads(raw.strip())
            st.session_state["script_parsed"] = script_parsed
        except Exception:
            script_parsed = {}

    ai_cycle = script_parsed.get("情绪周期", {})
    ai_mainline = script_parsed.get("主线演化", {})
    ai_fund = script_parsed.get("资金状态", {})
    ai_dangers = script_parsed.get("危险信号", [])
    ai_obs = script_parsed.get("明日观测点", [])

    if ai_mainline.get("主线板块"):
        mainline_text = ai_mainline["主线板块"]
    sub_mainlines = ai_mainline.get("次主线", [])[:2]
    mainline_stage = ai_mainline.get("阶段", "")
    mainline_leader = ai_mainline.get("龙头股", "")

    display_mainlines = [mainline_text] if mainline_text else []
    for sub in sub_mainlines:
        if sub and sub not in display_mainlines:
            display_mainlines.append(sub)
    mainline_display = " / ".join(display_mainlines[:3]) if display_mainlines else "暂无主线"

    # ---- One-line script ----
    if ai_fund.get("风险偏好"):
        script_text = f"{ai_fund['风险偏好']}情绪，{ai_fund.get('资金流向', '资金观望')}，{ai_fund.get('成交结构', '')}。"
    elif ai_cycle.get("阶段"):
        script_text = f"{ai_cycle['阶段']}，{ai_cycle.get('趋势', '震荡')}，明日关注{mainline_text}方向。"
    else:
        limit_up = sentiment.get("limit_up_count", 0)
        limit_down = sentiment.get("limit_down_count", 0)
        bomb = sentiment.get("bomb_rate", 0)
        if limit_up > 80:
            script_text = f"涨停{limit_up}家，市场情绪高涨，注意炸板率{bomb:.0%}风险。"
        elif limit_down > 20:
            script_text = f"跌停{limit_down}家，亏钱效应扩散，防守为主。"
        else:
            script_text = f"上涨{sentiment.get('rising_count',0)}家，涨停{limit_up}家，市场{cycle}中。"

    merged_dangers = ai_dangers if ai_dangers else danger_signals[:3]
    danger_list_html = ""
    sev_color_map = {"高": "#ff6b6b", "中": "#f7c948", "低": "#8fa2c9"}
    for ds in merged_dangers[:3]:
        sev = ds.get("严重程度", "中")
        sig = ds.get("信号", "")
        detail = ds.get("数值或个股", "")
        detail_text = f" · {detail}" if detail else ""
        danger_list_html += (
            f'<div class="market-cockpit-danger">'
            f'<strong style="color:{sev_color_map.get(sev, "#8fa2c9")};">⚠ {sev}风险</strong>'
            f' {sig}{detail_text}'
            f'</div>'
        )

    market_state_display = cycle.replace("期", "")
    if ai_cycle.get("阶段"):
        market_state_display = ai_cycle["阶段"].replace("期", "")
    trend_display = ai_cycle.get("趋势") or trend or ""
    if trend_display:
        if "修复" in trend_display and "分歧" in market_state_display:
            market_state_display = "分歧转修复"
        elif "退潮" in trend_display and "修复" in market_state_display:
            market_state_display = "修复防回落"
        elif trend_display not in market_state_display and len(trend_display) <= 8:
            market_state_display = f"{market_state_display} · {trend_display}"

    if cycle in ("主升期", "发酵期", "试错期"):
        hero_tone = "green"
    elif cycle in ("高潮期", "分歧期"):
        hero_tone = "yellow"
    elif cycle in ("退潮期",):
        hero_tone = "red"
    else:
        hero_tone = "blue"

    risk_display_map = {"low": "低风险", "medium": "中风险", "high": "中高风险"}
    risk_display_text = risk_display_map[risk_level]

    if cycle in ("主升期", "发酵期") and risk_level == "low":
        action_text = "偏进攻"
        action_hint = "顺主线扩大战果"
    elif cycle in ("分歧期", "高潮期") or risk_level == "medium":
        action_text = "控仓试错"
        action_hint = "聚焦回流确认"
    elif cycle in ("退潮期",) or risk_level == "high":
        action_text = "偏防守"
        action_hint = "先防回撤再等待"
    else:
        action_text = "观察切换"
        action_hint = "等待共振确认"

    if ai_fund.get("风险偏好"):
        cockpit_desc = (
            f"AI 正在实时监控市场，当前识别为 {market_state_display}，"
            f"资金风险偏好处于「{ai_fund.get('风险偏好', '观察中')}」阶段。"
        )
    else:
        cockpit_desc = (
            f"AI 正在实时监控市场，当前识别为 {market_state_display}，"
            f"建议以「{action_text}」为主，避免在高噪音区间无效出手。"
        )

    # ============================================================
    # 超大市场状态卡片
    # ============================================================
    st.markdown(f"""
    <div class="market-cockpit tone-{hero_tone}">
        <div class="market-cockpit-grid">
            <div class="market-cockpit-left">
                <div class="market-cockpit-kicker">
                    <span class="market-cockpit-dot"></span>
                    AI MARKET MONITOR ONLINE
                </div>
                <div class="market-cockpit-title">
                    <div>
                        <div class="terminal-state-label">当前市场状态</div>
                        <div class="market-cockpit-state">{market_state_display}</div>
                    </div>
                    <div class="market-cockpit-action">
                        <span>{action_text}</span>
                        <span style="opacity:0.72;">/ {action_hint}</span>
                    </div>
                </div>
                <div class="market-cockpit-desc">
                    {cockpit_desc}
                </div>
                <div class="market-cockpit-script">
                    <div class="market-cockpit-script-label">🎯 今日剧本</div>
                    <div class="market-cockpit-script-text">{script_text}</div>
                </div>
            </div>
            <div class="market-cockpit-panels">
                <div class="market-cockpit-panel">
                    <div class="market-cockpit-panel-label">🔥 当前主线</div>
                    <div class="market-cockpit-panel-value tone">{mainline_display}</div>
                    <div class="market-cockpit-panel-sub">{mainline_stage or '主线等待进一步确认'} {f"· 龙头 {mainline_leader}" if mainline_leader else ""}</div>
                </div>
                <div class="market-cockpit-panel">
                    <div class="market-cockpit-panel-label">⚠️ 风险等级</div>
                    <div class="market-cockpit-risk {risk_level}">{risk_label_emoji} {risk_display_text}</div>
                    <div class="market-cockpit-panel-sub">炸板率 {sentiment.get("bomb_rate", 0):.1%} · 跌停 {sentiment.get("limit_down_count", 0)} 家</div>
                </div>
                <div class="market-cockpit-panel">
                    <div class="market-cockpit-panel-label">📊 情绪强度</div>
                    <div class="market-cockpit-panel-value">涨停 {sentiment.get("limit_up_count", 0)} / 跌停 {sentiment.get("limit_down_count", 0)}</div>
                    <div class="market-cockpit-panel-sub">连板高度 {sentiment.get("连板高度", 0)} 板 · 上涨家数 {sentiment.get("rising_count", 0)}</div>
                </div>
                <div class="market-cockpit-panel">
                    <div class="market-cockpit-panel-label">🧠 风险提示</div>
                    <div class="market-cockpit-danger-list">
                        {danger_list_html if danger_list_html else '<div class="market-cockpit-danger"><strong style="color:#3ddc97;">✅ 风险可控</strong> AI 暂未捕捉到高优先级危险信号，允许围绕主线观察回流。</div>'}
                    </div>
                </div>
            </div>
        </div>
        <div class="market-cockpit-signals">
            <div class="market-cockpit-signal"><span>📍</span><strong>状态</strong> {state_tag(cycle, cycle_tag_color)}</div>
            <div class="market-cockpit-signal"><span>🔁</span><strong>趋势</strong> {trend or '—'}</div>
            <div class="market-cockpit-signal"><span>💰</span><strong>资金</strong> {ai_fund.get('资金流向', '资金待确认')}</div>
            <div class="market-cockpit-signal"><span>👁</span><strong>观测</strong> {(ai_obs[0].get('观测内容', '观察主线回流') if ai_obs else '观察主线回流')}</div>
            <div class="market-cockpit-signal"><span>🎯</span><strong>策略</strong> {action_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # TOP3 热点板块
    # ============================================================
    hot_sectors = R.get("hot_sectors", [])
    if hot_sectors:
        valid = [s for s in hot_sectors if isinstance(s, dict) and 'name' in s and 'change_pct' in s]
        if valid:
            st.markdown('<div class="terminal-section-header">🔥 TOP3 热点板块</div>', unsafe_allow_html=True)
            cols_s = st.columns(3)
            for i, s in enumerate(valid[:3]):
                with cols_s[i]:
                    change = s.get("change_pct", 0)
                    up = change > 0
                    bar_color = "#4ecdc4" if up else "#e74c3c"
                    st.markdown(f"""
                    <div class="terminal-sector-card">
                        <div style="display:flex; align-items:center; justify-content:space-between;">
                            <div style="font-size:15px; font-weight:700; color:#ddd;">{s["name"]}</div>
                            <div style="font-size:18px; font-weight:800; color:{bar_color};">{change:+.1f}%</div>
                        </div>
                        <div style="margin-top:8px; height:4px; border-radius:2px; background:#1c1c30;">
                            <div style="height:4px; border-radius:2px; width:{min(abs(change)*8, 100)}%; background:{bar_color};"></div>
                        </div>
                        <div style="margin-top:6px; font-size:11px; color:#555;">
                            成交 {s.get('volume', 0):.0f}亿 · 领涨 {s.get('leader', '—')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

elif current_page == "market_timeline":
    from ui.theme import inject_theme, CYCLE_COLORS, RISK_HEX, state_tag

    inject_theme()
    st.markdown('<span class="section-title">📋 市场时间轴</span>', unsafe_allow_html=True)
    st.caption("持续观察市场的 AI 时间记忆系统")

    if st.button("🔄 刷新", key="timeline_refresh"):
        st.rerun()

    # 加载股票列表 + 市场情绪历史
    all_stocks = get_all_stocks(username=get_current_username())
    sentiment_history = get_market_sentiment_history(limit=30)

    if not all_stocks and not sentiment_history:
        st.markdown('<div class="empty-state">📭 暂无历史记录<br><span style="font-size:13px;">先在「个股快评」中分析股票，或在「市场情绪引擎」中生成快照</span></div>', unsafe_allow_html=True)
    else:
        # ---- 市场情绪时间轴 ----
        if sentiment_history:
            st.markdown('<span class="section-title">🧠 市场情绪日志</span>', unsafe_allow_html=True)

            for i, record in enumerate(sentiment_history[:15]):
                mood = record.get("market_mood", "未知")
                color = CYCLE_COLORS.get(mood, "blue")
                tags_html = ""
                if record.get("limit_up_count", 0) > 80:
                    tags_html += state_tag("高潮", "red") + " "
                elif record.get("limit_up_count", 0) > 40:
                    tags_html += state_tag("活跃", "green") + " "
                if record.get("limit_down_count", 0) > 20:
                    tags_html += state_tag("退潮", "red") + " "

                # 情绪标签映射
                mood_map = {"高潮": "高潮期", "强势": "强势期", "震荡": "震荡期", "偏弱": "弱市期", "退潮": "退潮期"}
                period = mood_map.get(mood, mood)

                with st.expander(f"📅 {record['date']}  |  市场：{period}  |  涨停{record['limit_up_count']}/跌停{record['limit_down_count']}", expanded=(i == 0)):
                    cols_t = st.columns(4)
                    with cols_t[0]:
                        st.markdown(f"**情绪**: {mood}  |  **涨跌**: {record['avg_change']:+.2f}%")
                    with cols_t[1]:
                        st.markdown(f"上涨 **{record['rising_count']}**（{record['rise_ratio']:.0f}%）")
                        st.markdown(f"下跌 **{record['falling_count']}**")
                    with cols_t[2]:
                        st.markdown(f"强势 **{record['strong_count']}** 只")
                        st.markdown(f"弱势 **{record['weak_count']}** 只")
                    with cols_t[3]:
                        st.caption(f"记录于 {record.get('created_at', '')}")

        # ---- 个股分析时间轴 ----
        if all_stocks:
            st.markdown('<span class="section-title">📈 个股看盘记录</span>', unsafe_allow_html=True)
            stock_options = [f"{s['name']} ({s['code']})" for s in all_stocks]
            stock_codes = [s['code'] for s in all_stocks]

            selected = st.selectbox("按股票筛选", options=["全部"] + stock_options, key="history_select")

            if selected == "全部":
                # 展平所有记录
                all_records = []
                for code in stock_codes:
                    recs = get_stock_history(code, limit=5, username=get_current_username())
                    all_records.extend(recs)
                all_records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
                display_records = all_records[:30]
            else:
                idx = stock_options.index(selected)
                selected_code = stock_codes[idx]
                display_records = get_stock_history(selected_code, limit=20, username=get_current_username())

            if display_records:
                st.caption(f"共 {len(display_records)} 条记录")
                for i, record in enumerate(display_records):
                    created = record.get("created_at", "")
                    date_str = created[:10] if created else ""

                    # 情绪→颜色
                    mood = record.get("market_mood", "")
                    mood_color = {"高潮": "#e74c3c", "强势": "#4ecdc4", "震荡": "#f5a623", "偏弱": "#95e1d3", "退潮": "#a29bfe", "极速模式": "#888"}.get(mood, "#888")

                    with st.expander(f"📅 {date_str}  |  {record['stock_name']}({record['stock_code']})  |  {record.get('change_pct', 0):+.2f}%  |  情绪: {mood}", expanded=(i == 0)):
                        # 关键指标横排
                        cols_r = st.columns(4)
                        with cols_r[0]:
                            st.metric("价格", f"{record['price']:.2f}")
                        with cols_r[1]:
                            st.metric("涨跌", f"{record['change_pct']:.2f}%")
                        with cols_r[2]:
                            st.metric("模式", record.get('mode', '极速'))
                        with cols_r[3]:
                            st.markdown(f"情绪: <span style='color:{mood_color};'>{mood}</span>", unsafe_allow_html=True)

                        # AI 摘要（折叠）
                        with st.expander("🎯 AI 复盘摘要", expanded=False):
                            summary_text = record.get("ai_summary", "")
                            st.markdown(summary_text[:800] + ("..." if len(summary_text) > 800 else ""))

                        st.download_button(
                            label="📥 下载",
                            data=record.get("ai_summary", ""),
                            file_name=f"复盘_{record['stock_code']}_{date_str}.txt",
                            mime="text/plain",
                            key=f"tl_dl_item_{i}"
                        )
            else:
                st.info("暂无个股记录")

elif current_page == "attack_board":
    from ui.theme import CYCLE_HEX, RISK_HEX

    # ================================================================
    # SECTION 0：数据采集
    # ================================================================
    if "attack_result" not in st.session_state:
        st.session_state["attack_result"] = None

    col_sc, col_info = st.columns([2, 4])
    with col_sc:
        if st.button("⚔️ 扫描进攻目标", key="scan_attack", type="primary", use_container_width=True):
            with st.spinner("📡 采集市场情绪..."):
                from modules.market_engine import run_market_emotion_analysis
                emotion = run_market_emotion_analysis()
            with st.spinner("🔍 扫描全市场日线数据..."):
                from engines.attack_opportunity_engine import scan_attack_opportunities
                targets = scan_attack_opportunities(emotion)
                st.session_state["attack_result"] = {"emotion": emotion, "targets": targets}
            st.rerun()

    R = st.session_state.get("attack_result")
    if R is None:
        with col_info:
            st.markdown('<div class="empty-state">⚔️ 点击扫描，AI 将综合趋势、量能、龙头、情绪扫描全市场<br>输出今日最值得进攻的 TOP5 目标池</div>', unsafe_allow_html=True)
    else:
        emotion = R["emotion"]
        targets = R["targets"]
        cycle = emotion["cycle"]
        cycle_hex = CYCLE_HEX.get(cycle, "#888")
        danger = emotion.get("danger_signals", [])
        risk_level = "low"
        if danger:
            sevs = [d.get("严重程度", "") for d in danger]
            if "高" in sevs:
                risk_level = "high"
            elif len(danger) >= 2:
                risk_level = "medium"
        risk_text = {"low": "低", "medium": "中", "high": "高"}[risk_level]

        st.markdown(f"""
        <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; padding:14px 20px;
                    border-radius:16px; border:1px solid rgba(103, 131, 204, 0.14);
                    background:rgba(10, 16, 31, 0.68); margin-bottom:16px;">
            <span style="font-size:11px; color:#7284ab; letter-spacing:1px;">MARKET</span>
            <span style="font-size:16px; font-weight:700; color:{cycle_hex};">{cycle}</span>
            <span style="color:#444;">|</span>
            <span style="font-size:13px; color:#aab;">主线: {emotion.get('main_sector', '暂无')}</span>
            <span style="color:#444;">|</span>
            <span style="font-size:13px; color:{RISK_HEX.get(risk_level, '#888')};">风险: {risk_text}</span>
            <span style="color:#444;">|</span>
            <span style="font-size:13px; color:#aab;">涨停{emotion['sentiment'].get('limit_up_count', 0)}/跌停{emotion['sentiment'].get('limit_down_count', 0)}</span>
        </div>
        """, unsafe_allow_html=True)

        if cycle in ("退潮期", "冰点期") and risk_level == "high":
            st.warning("🚨 退潮/冰点 + 高风险，建议空仓观望，不进攻。以下目标仅供参考。")

        if not targets:
            st.info("📭 当前未发现符合条件的进攻目标。市场回暖后再扫描。")
        else:
            for rank, t in enumerate(targets):
                r = rank + 1
                rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(r, f"#{r}")
                score_color = "#4ecdc4" if t["score"] >= 80 else "#f5a623" if t["score"] >= 60 else "#e74c3c"
                risk_color = {"low": "#4ecdc4", "medium": "#f5a623", "high": "#e74c3c"}.get(t["risk"], "#888")
                change_sign = "+" if t["change_pct"] >= 0 else ""
                change_color = "#4ecdc4" if t["change_pct"] >= 0 else "#e74c3c"
                reasons_html = "".join([f'<span style="background:#1a1a2e; color:#aab; padding:2px 10px; border-radius:20px; font-size:11px; margin:2px;">{reason}</span>' for reason in t["reasons"]])

                st.markdown(f"""
<div class="market-card" style="position:relative; border-left:6px solid {score_color}; margin-bottom:18px;">
    <div style="display:flex; align-items:baseline; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <div style="display:flex; align-items:baseline; gap:12px;">
            <span style="font-size:22px;">{rank_emoji}</span>
            <div>
                <span style="font-size:22px; font-weight:800; color:#eee;">{t['name']}</span>
                <span style="font-size:13px; color:#666; margin-left:8px;">{t['code']}</span>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:38px; font-weight:900; color:{score_color};">{t['score']}</span>
            <span style="font-size:12px; color:#666;">分</span>
        </div>
    </div>
    <div style="display:flex; gap:8px; margin-top:12px; flex-wrap:wrap;">
        <span style="background:{'#0d2818' if t['state_key'] in ('acceleration','breakout','trend_follow') else '#28240d'}; color:{score_color}; border:1px solid {score_color}30; border-radius:20px; padding:2px 12px; font-size:12px;">{t['state_cn']}</span>
        <span style="font-size:12px; color:#cde; border:1px solid #333; border-radius:20px; padding:2px 12px;">{t['theme']}</span>
        <span style="font-size:13px; font-weight:700; color:{change_color};">{change_sign}{t['change_pct']}%</span>
        <span style="font-size:12px; color:#888;">风险 <b style="color:{risk_color};">{t['risk']}</b></span>
    </div>
    <div style="margin-top:12px; display:flex; gap:6px; flex-wrap:wrap;">{reasons_html}</div>
    <div style="margin-top:14px; padding:12px; background:#0f0f1a; border-radius:10px;">
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            <div style="flex:1; min-width:200px;">
                <span style="font-size:11px; color:#4ecdc4;">✅ 多头剧本</span>
                <div style="font-size:13px; color:#aaa; margin-top:4px;">{t['script_bull']}</div>
            </div>
            <div style="flex:1; min-width:200px;">
                <span style="font-size:11px; color:#e74c3c;">⚠️ 风险剧本</span>
                <div style="font-size:13px; color:#aaa; margin-top:4px;">{t['script_bear']}</div>
            </div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

elif current_page == "data_center":
    st.header("📈 行情数据")

    import pandas as pd
    import os
    from datetime import timedelta
    import akshare as ak

    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'cn', 'daily')

    MARKET_MAP = {
        'sh_main': {'name': '沪市主板', 'color': '#E74C3C'},
        'sh_star': {'name': '科创板', 'color': '#9B59B6'},
        'sz_main': {'name': '深市主板', 'color': '#3498DB'},
        'sz_sme': {'name': '中小板', 'color': '#27AE60'},
        'sz_gem': {'name': '创业板', 'color': '#F39C12'}
    }

    from data_sync.data_sync_manager import DataSyncManager

    sync_manager = DataSyncManager(data_dir=DATA_DIR)

    def get_market_from_code(code):
        """根据股票代码判断市场"""
        if code.startswith('6'):
            if code.startswith('688'):
                return 'sh_star'
            return 'sh_main'
        elif code.startswith('00') or code.startswith('30'):
            if code.startswith('002'):
                return 'sz_sme'
            elif code.startswith('003'):
                return 'sz_main'
            elif code.startswith('30'):
                return 'sz_gem'
            return 'sz_main'
        return 'sh_main'

    def get_stock_files():
        files = []
        for market in os.listdir(DATA_DIR):
            market_path = os.path.join(DATA_DIR, market)
            if not os.path.isdir(market_path) or market not in MARKET_MAP:
                continue
            for f in sorted(os.listdir(market_path)):
                if f.endswith('.csv'):
                    code = f.replace('.csv', '')
                    name = code_name_map.get(code, code)
                    files.append({
                        'code': code,
                        'name': name,
                        'market': market,
                        'file_path': os.path.join(market, f)
                    })
        return sorted(files, key=lambda x: x['code'])

    def get_stock_data(file_path):
        full_path = os.path.join(DATA_DIR, file_path)
        if not os.path.exists(full_path):
            return None
        return pd.read_csv(full_path)

    companies = get_company_list()
    code_name_map = {c['code']: c['name'] for c in companies} if companies else {}

    stocks = get_stock_files()

    existing_count = sync_manager.get_existing_stocks_count()
    total_stocks = len(stocks)
    
    stock_options = [""] + [f"{s['name']} ({s['code']})" for s in stocks]
    stock_file_map = {f"{s['name']} ({s['code']})": s['file_path'] for s in stocks}
    stock_info_map = {f"{s['name']} ({s['code']})": {'code': s['code'], 'name': s['name'], 'market': s['market']} for s in stocks}

    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        selected_stock = st.selectbox(
            "选择或输入股票",
            options=stock_options,
            index=0,
            format_func=lambda x: x if x else "输入/选择股票...",
            key="daily_stock_select"
        )
    with col_header2:
        st.write("")
        st.write("")
        update_date = st.date_input(
            "增量更新到",
            value=datetime.now(),
            key="update_date_input",
            help="选择增量更新的目标日期"
        )
    with col_header3:
        st.write("")
        st.write("")
        st.write("")

    col_status, col_full_btn, col_update_btn = st.columns([2, 1, 1])
    with col_status:
        st.caption(f"📊 已有 {existing_count} 只股票数据 | 共 {total_stocks} 只")

    with col_update_btn:
        st.write("")
        if selected_stock and st.button("🔄 增量更新当前股", key="update_current_stock", type="primary"):
            stock_info = stock_info_map.get(selected_stock, {})
            stock_code = stock_info.get('code', '')
            if stock_code:
                with st.spinner("正在增量更新..."):
                    success, message, count = sync_manager.update_stock_incremental(stock_code, update_date.strftime('%Y-%m-%d'))
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    with col_full_btn:
        st.write("")
        if st.button("📥 全量更新所有股", key="full_sync_all", help="从2023-01-13开始同步所有股票"):
            with st.spinner("全量同步中，请稍候..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total, message):
                    progress_bar.progress(current / total)
                    status_text.text(message)
                
                result = sync_manager.sync_all_full(progress_callback=progress_callback)
                
                progress_bar.empty()
                status_text.empty()
                st.success(f"✅ 全量同步完成！成功: {result['success']} 只，失败: {result['failed']} 只")
                st.rerun()

    if selected_stock:
        stock_info = stock_info_map.get(selected_stock, {})
        stock_code = stock_info.get('code', '')
        stock_name = stock_info.get('name', '')
        market_name = MARKET_MAP.get(stock_info.get('market', ''), {}).get('name', '')
        st.caption(f"📊 当前: {stock_name} ({stock_code}) | 市场: {market_name}")

        file_path = stock_file_map.get(selected_stock)
        df = get_stock_data(file_path)

        if df is not None:
            st.success(f"✅ 已加载 {df.shape[0]} 条日线数据")

            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            with col_stats1:
                latest_close = df['close'].iloc[-1] if 'close' in df.columns else 0
                st.metric("最新收盘", f"{latest_close:.2f}")
            with col_stats2:
                latest_change = df['price_change_pct'].iloc[-1] if 'price_change_pct' in df.columns else 0
                st.metric("最新涨跌", f"{latest_change:.2f}%")
            with col_stats3:
                max_close = df['close'].max() if 'close' in df.columns else 0
                st.metric("最高收盘", f"{max_close:.2f}")
            with col_stats4:
                min_close = df['close'].min() if 'close' in df.columns else 0
                st.metric("最低收盘", f"{min_close:.2f}")

            st.subheader("📊 最近30条日线数据")
            display_df = df.tail(30)[['date', 'open', 'high', 'low', 'close', 'volume', 'price_change_pct', 'turnover_rate']].copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
            display_df['price_change_pct'] = display_df['price_change_pct'].apply(lambda x: f"{x:.2f}%")
            st.dataframe(display_df, use_container_width=True)

            st.subheader("📈 价格走势图")
            if 'close' in df.columns and 'date' in df.columns:
                chart_data = df.tail(100)[['date', 'open', 'high', 'low', 'close']].copy()
                chart_data['date'] = pd.to_datetime(chart_data['date']).dt.strftime('%Y-%m-%d')
                st.line_chart(chart_data.set_index('date'))

            st.subheader("📊 成交量")
            if 'volume' in df.columns and 'date' in df.columns:
                vol_data = df.tail(100)[['date', 'volume']].copy()
                vol_data['date'] = pd.to_datetime(vol_data['date']).dt.strftime('%Y-%m-%d')
                st.bar_chart(vol_data.set_index('date'))
        else:
            st.error("无法加载数据")
    else:
        st.info("请从上方选择股票查看日线数据")

# 管理员后台
if st.session_state.get("show_admin"):
    from admin_auth.dashboard import show_admin_dashboard, go_back
    show_admin_dashboard()
    if st.sidebar.button("🏠 返回主应用"):
        go_back()
