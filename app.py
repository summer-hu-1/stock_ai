import streamlit as st
import sys
import os
import json
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# 0. 路径与基础初始化
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from admin_auth.db import init_db as init_admin_db
from admin_auth.service import AdminService

init_admin_db()
created, admin_username = AdminService.init_default_admin()
if created:
    st.sidebar.success(f"已创建默认管理员: {admin_username}")

from auth.auth import is_logged_in, get_user_quota_info
from modules.storage import init_db
from modules.market_sentiment import get_market_sentiment, get_hot_sectors
from modules.market_data import get_stock_data, get_stock_data_fast

init_db()

# ---------------------------------------------------------------------------
# 1. 工具函数
# ---------------------------------------------------------------------------

def get_current_username():
    if "user" in st.session_state and st.session_state["user"]:
        return st.session_state["user"]["username"]
    return "guest"


def load_company_data():
    """从 akshare 加载全量公司信息到数据库"""
    from modules.storage import save_company_info
    import akshare as ak
    try:
        with st.spinner("正在加载公司数据..."):
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                companies = []
                for _, row in df.iterrows():
                    companies.append({
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                    })
                save_company_info(companies)
                st.success(f"已加载 {len(companies)} 条公司信息")
                return True
    except Exception as e:
        st.error(f"加载公司数据失败: {e}")
    return False


# ---------------------------------------------------------------------------
# 2. 新导航定义（仅两个 Tab）
# ---------------------------------------------------------------------------

NAV_ITEMS = [
    {
        "key": "market_pulse",
        "label": "市场脉搏",
        "icon": "◉",
        "hint": "3分钟看懂市场",
        "index": "01",
    },
    {
        "key": "ai_stock",
        "label": "AI 个股",
        "icon": "◎",
        "hint": "明天怎么办",
        "index": "02",
    },
]

NAV_META = {item["key"]: item for item in NAV_ITEMS}


# ---------------------------------------------------------------------------
# 3. UI 渲染函数
# ---------------------------------------------------------------------------

def render_terminal_brand():
    """顶部品牌区"""
    status_text = (
        f"已登录 - {get_current_username()}"
        if is_logged_in()
        else "游客模式"
    )
    st.markdown(
        f"""
        <div class="terminal-brand-shell">
            <div class="terminal-brand-kicker">AI Market Terminal</div>
            <div class="terminal-brand-row">
                <div>
                    <div class="terminal-brand-title">AI 股票信息终端</div>
                    <div class="terminal-brand-desc">
                        3 分钟，看懂今天市场。
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
    """顶部双 Tab 导航"""
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = NAV_ITEMS[0]["key"]

    current_page = st.session_state["active_page"]
    nav_cols = st.columns(len(NAV_ITEMS))

    for col, item in zip(nav_cols, NAV_ITEMS):
        with col:
            is_active = current_page == item["key"]
            if st.button(
                f"{item['icon']}  {item['label']}",
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


# ---------------------------------------------------------------------------
# 4. 页面一：市场脉搏
# ---------------------------------------------------------------------------

def render_market_pulse():
    """渲染市场脉搏完整页面"""
    from core.trader_lang import (
        translate_market_status,
        extract_main_line,
        translate_danger_signals,
    )
    from core.minimal_analysis import distill_market_brief, distill_market_theme
    from modules.hot_timeline import generate_hot_timeline
    from modules.market_engine import detect_danger_signals

    # --- 加载数据 ---
    with st.spinner("正在获取市场数据..."):
        sentiment = get_market_sentiment(use_cache=True)
        hot_sectors = get_hot_sectors(use_cache=True) or []

    trader_status = translate_market_status(sentiment)
    main_line = extract_main_line(hot_sectors)

    # --- 4.1 动态状态条 ---
    signal = trader_status["signal"]
    dot_class = {"🟢": "green", "🔴": "red", "🟡": "yellow"}.get(signal, "yellow")
    status_text = trader_status["status_text"]

    st.markdown(
        f"""
        <div class="pulse-hero-bar">
            <div class="pulse-hero-grid">
                <div class="pulse-hero-main">
                    <div class="pulse-hero-signal">
                        <span class="dot {dot_class}"></span>
                        {status_text}
                    </div>
                    <div class="pulse-hero-meta">
                        <span>涨停 <strong>{trader_status['limit_up']}家</strong></span>
                        <span>跌停 <strong>{trader_status['limit_down']}家</strong></span>
                        <span>炸板率 <strong>{trader_status['bomb_rate']*100:.0f}%</strong></span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 4.2 主线 + 主题 ---
    today_theme = distill_market_theme(sentiment, hot_sectors)
    st.markdown(
        f"""
        <div class="pulse-hero-bar" style="margin-top:-8px;">
            <div style="display:flex; align-items:center; gap:14px; font-size:15px; color:var(--text-1);">
                <span style="font-size:18px;">🔥</span>
                <span>主线：<strong style="color:var(--text-0)">{main_line}</strong></span>
                <span style="color:var(--text-3);margin:0 8px;">|</span>
                <span style="font-size:16px;">🧠</span>
                <span style="color:var(--text-2);">市场在交易：{today_theme}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 4.3 AI 市场理解 ---
    brief = distill_market_brief(sentiment, hot_sectors, trader_status)
    st.markdown(
        f"""
        <div class="brief-card">
            <div class="label">AI 市场理解</div>
            {brief}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 4.4 今日异动时间线 ---
    timeline = generate_hot_timeline(hot_sectors, sentiment)
    if timeline:
        items_html = ""
        for item in timeline:
            items_html += f"""
            <div class="timeline-item">
                <span class="time">{item['time']}</span>
                <span>{item['event']}</span>
            </div>"""
        st.markdown(
            f"""
            <div class="timeline-list">
                <div class="label">今日异动</div>
                {items_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- 4.5 风险提醒 ---
    danger_signals = detect_danger_signals(
        涨停数=trader_status["limit_up"],
        跌停数=trader_status["limit_down"],
        炸板率=trader_status["bomb_rate"],
    )
    trader_dangers = translate_danger_signals(danger_signals)

    if trader_dangers:
        risk_items = ""
        for d in trader_dangers:
            risk_items += f'<div class="risk-item"><span class="icon">⚠️</span>{d}</div>'
        st.markdown(
            f"""
            <div class="risk-list">
                <div class="label">需要留意</div>
                {risk_items}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# 5. 页面二：AI 个股
# ---------------------------------------------------------------------------

def render_ai_stock():
    """渲染 AI 个股完整页面"""
    from modules.storage import get_all_companies, get_company_by_code
    from core.trader_lang import (
        STATE_TO_TRADER_CN,
        STATE_TO_LABEL,
        RISK_TO_TRADER_CN,
        analyze_main_force,
        analyze_market_position,
    )
    from core.minimal_analysis import distill_next_day_scenario
    from engines.structure_engine.short_term_state import get_short_term_state, daily_from_dataframe

    # --- 5.1 股票搜索 ---
    st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    companies = get_all_companies()
    if not companies:
        st.info("未加载公司数据，请先刷新数据")
        return

    stock_options = {}
    for c in companies:
        code = str(c.get("code", ""))
        name = str(c.get("name", ""))
        if code and name:
            label = f"{code}  {name}"
            stock_options[label] = code

    selected_label = st.selectbox(
        "输入股票代码或名称搜索",
        options=[""] + list(stock_options.keys()),
        key="ai_stock_search",
        placeholder="例如：300308 中际旭创",
        label_visibility="collapsed",
    )

    if not selected_label:
        st.info("输入股票代码开始分析")
        return

    stock_code = stock_options[selected_label]
    stock_name = selected_label.split("  ")[-1] if "  " in selected_label else selected_label

    # --- 5.2 加载数据 ---
    with st.spinner(f"正在分析 {stock_name} ..."):
        stock_data = get_stock_data(stock_code, "cn")
        if not stock_data:
            stock_data = get_stock_data_fast(stock_code)

    if not stock_data:
        st.error(f"未获取到 {stock_name}（{stock_code}）的行情数据")
        return

    # 加载本地日线，分析短线状态
    import pandas as pd
    data_dir = os.path.join(os.path.dirname(__file__), "data", "cn", "daily")
    state = None
    if os.path.exists(data_dir):
        csv_path = None
        for market_dir in os.listdir(data_dir):
            market_path = os.path.join(data_dir, market_dir)
            if not os.path.isdir(market_path):
                continue
            candidate = os.path.join(market_path, f"{stock_code}.csv")
            if os.path.exists(candidate):
                csv_path = candidate
                break
        if csv_path:
            try:
                df = pd.read_csv(csv_path)
                if len(df) >= 3:
                    daily_5 = daily_from_dataframe(df, n=5)
                    state = get_short_term_state(daily_5)
            except Exception:
                pass

    state_key = state.get("state_key", "consolidation") if state else "consolidation"
    trader_state = STATE_TO_TRADER_CN.get(state_key, "方向不明确，先看看")
    trader_label = STATE_TO_LABEL.get(state_key, "等待方向")
    risk_key = state.get("risk", "medium") if state else "medium"
    trader_risk = RISK_TO_TRADER_CN.get(risk_key, "状态不确定")

    # --- 5.3 量价特征 ---
    volumes = [d.get("volume", 0) for d in (daily_5 if state else [])] if state else []
    pcts = [d.get("pct_chg", 0) for d in (daily_5 if state else [])] if state else []
    force = analyze_main_force(volumes, pcts, state_key)

    # --- 5.4 板块定位 ---
    sector_name = stock_data.get("sector", "未知板块") if isinstance(stock_data, dict) else "未知板块"
    position = analyze_market_position(stock_name, sector_name, 2, 10, stock_data.get("price_change_pct", 0) if isinstance(stock_data, dict) else 0, 0.5)

    # --- 5.5 近期走势摘要 ---
    price = stock_data.get("price", 0) if isinstance(stock_data, dict) else 0
    pct_chg = stock_data.get("price_change_pct", 0) if isinstance(stock_data, dict) else 0
    volume_trend = force.get("feature", "")
    recent_pattern = f"{stock_name}当前{trader_state}，近5日{'红多绿少' if force.get('judgment', '') else '走势不明'}"

    # ==========================================
    # 渲染：次日剧本（第 1 块，最大）
    # ==========================================
    scenario = distill_next_day_scenario(
        stock_name=stock_name,
        stock_code=stock_code,
        current_price=price,
        pct_chg=pct_chg,
        trader_state=trader_state,
        sector_name=sector_name,
        sector_position=position["rank"],
        volume_trend=volume_trend,
        recent_pattern=recent_pattern,
    )

    st.markdown(
        f"""
        <div class="next-day-card">
            <div class="label">📅 明天怎么办？</div>
            <div style="white-space:pre-wrap; font-size:15px; color:var(--text-1); line-height:1.85;">
{scenario}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================================
    # 渲染：主力态度（第 2 块）
    # ==========================================
    st.markdown(
        f"""
        <div class="trader-card">
            <div class="label">💰 主力还在吗？</div>
            <div class="value">{force["attitude"]}</div>
            <div class="sub">{force["feature"]}</div>
            <div class="sub" style="margin-top:6px; color:var(--blue);">🧠 {force["judgment"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================================
    # 渲染：市场定位（第 3 块）
    # ==========================================
    st.markdown(
        f"""
        <div class="trader-card">
            <div class="label">🎯 市场定位</div>
            <div class="value">{position["role"]}</div>
            <div class="sub">🏆 {position["rank"]}</div>
            <div class="sub">📎 {position["relation"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================================
    # 渲染：当前状态（第 4 块，放最后）
    # ==========================================
    st.markdown(
        f"""
        <div class="trader-card">
            <div class="label">📌 当前状态</div>
            <div class="value">{trader_state}</div>
            <div class="sub">⚠️ 个股风险：{trader_risk}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# 6. 主入口
# ---------------------------------------------------------------------------

st.set_page_config(page_title="AI 股票信息终端", page_icon="◉", layout="wide")

from ui.theme import inject_theme

# 注入 CSS（旧有 + 新增 minimal-terminal 组件）
inject_theme()

# 自动登录检查
from auth.modal import check_auto_login, show_login_modal
check_auto_login()

# 顶部栏
col_title, col_login = st.columns([9, 1])
with col_title:
    render_terminal_brand()
with col_login:
    if "user" not in st.session_state or not st.session_state["user"]:
        if st.button("登录", key="login_button_top"):
            st.session_state["show_login_modal"] = True
            st.rerun()

show_login_modal()

# 侧边栏
from auth.modal import show_user_info_updated
user_logged_in = show_user_info_updated()

with st.sidebar:
    if not user_logged_in:
        st.caption("游客模式 - 自由使用")
    st.markdown("---")

# 导航 & 路由
current_page = render_terminal_nav()

if current_page == "market_pulse":
    render_market_pulse()
elif current_page == "ai_stock":
    render_ai_stock()