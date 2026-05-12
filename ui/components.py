"""
UI Components - 共享UI组件

提供可复用的UI组件，避免重复代码
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional, Callable


def stock_selector_with_market(
    key_prefix: str = "stock",
    default_market: str = "cn",
    show_refresh: bool = True,
    on_refresh_callback: Optional[Callable] = None
) -> Tuple[str, str, str]:
    """
    股票选择器组件（包含市场选择）

    布局：
    [市场选择] [刷新按钮]
    [股票下拉选择]

    Args:
        key_prefix: 组件key前缀，用于区分不同Tab中的组件
        default_market: 默认市场
        show_refresh: 是否显示刷新按钮
        on_refresh_callback: 刷新按钮点击时的回调函数，用于执行真正的数据刷新

    Returns:
        (stock_code, stock_name, market): 股票代码、股票名称、市场代码
    """
    market_options = [
        ("cn", "🇨🇳 A股"),
        ("hk", "🇭🇰 港股"),
        ("us", "🇺🇸 美股")
    ]
    markets = [m[0] for m in market_options]
    market_labels = [m[1] for m in market_options]

    col_market, col_refresh = st.columns([1, 4]) if show_refresh else st.columns([1, 1])

    with col_market:
        selected_market_label = st.selectbox(
            "选择市场",
            options=market_labels,
            index=markets.index(default_market) if default_market in markets else 0,
            key=f"{key_prefix}_market_select"
        )
        market_map = {label: code for code, label in market_options}
        current_market = market_map[selected_market_label]

    with col_refresh:
        st.write("")
        st.write("")
        if show_refresh:
            if st.button("🔄 刷新列表", key=f"{key_prefix}_refresh", help="点击更新公司列表"):
                cache_key = f'companies_{current_market}'
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                if on_refresh_callback:
                    with st.spinner("🔄 正在刷新数据..."):
                        on_refresh_callback()
                st.rerun()

    cache_key = f'companies_{current_market}'
    if cache_key not in st.session_state:
        try:
            from modules.storage import get_all_companies
            companies = get_all_companies(market=current_market)
            st.session_state[cache_key] = companies
        except Exception as e:
            st.warning(f"无法加载公司列表: {e}")
            st.session_state[cache_key] = []
    else:
        companies = st.session_state[cache_key]

    stock_options = [""] + [f"{c['name']} ({c['code']})" for c in companies]
    stock_code_map = {f"{c['name']} ({c['code']})": c['code'] for c in companies}
    name_code_map = {c['code']: c['name'] for c in companies}

    selected_stock = st.selectbox(
        "选择或输入股票",
        options=stock_options,
        index=0,
        format_func=lambda x: x if x else "输入/选择股票...",
        key=f"{key_prefix}_stock_select"
    )
    stock_code = stock_code_map.get(selected_stock, selected_stock if selected_stock else "")
    stock_name = name_code_map.get(stock_code, "")

    if stock_code and stock_name:
        st.caption(f"📊 {len(companies)} 家公司 | 当前: {stock_name} ({stock_code})")
    else:
        st.caption(f"📊 已加载 {len(companies)} 家公司")

    return stock_code, stock_name, current_market


def market_selector(
    key_prefix: str = "market",
    default_market: str = "cn"
) -> str:
    """
    市场选择器组件（单独使用）

    Args:
        key_prefix: 组件key前缀
        default_market: 默认市场

    Returns:
        market: 选中的市场代码
    """
    market_options = [
        ("cn", "🇨🇳 A股"),
        ("hk", "🇭🇰 港股"),
        ("us", "🇺🇸 美股")
    ]

    markets = [m[0] for m in market_options]
    market_labels = [m[1] for m in market_options]

    selected_index = markets.index(default_market) if default_market in markets else 0

    selected_label = st.selectbox(
        "选择市场",
        options=market_labels,
        index=selected_index,
        key=f"{key_prefix}_market"
    )

    market_map = {label: code for code, label in market_options}
    return market_map[selected_label]


def analysis_mode_selector(
    key_prefix: str = "mode",
    default_mode: str = "fast"
) -> Tuple[str, str]:
    """
    分析模式选择器

    Args:
        key_prefix: 组件key前缀
        default_mode: 默认模式

    Returns:
        (mode_key, mode_label): 模式标识和显示标签
    """
    modes = {
        "fast": "⚡ 极速模式（仅个股数据）",
        "standard": "📈 标准模式（个股+市场情绪）",
        "full": "🔍 完整模式（全部数据）"
    }

    mode_labels = list(modes.values())
    mode_keys = list(modes.keys())

    selected_index = mode_keys.index(default_mode) if default_mode in mode_keys else 0

    selected_label = st.radio(
        "📊 模式",
        mode_labels,
        index=selected_index,
        horizontal=True,
        key=f"{key_prefix}_mode"
    )

    mode_map = {label: key for key, label in modes.items()}
    return mode_map[selected_label], selected_label
