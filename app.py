import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from agents.controller_agent import multi_agent_review
from modules.storage import init_db, save_analysis, save_market_sentiment, get_all_companies, save_company_info, get_company_by_code
from deepseek import stock_review, check_balance
from modules.market_data import get_stock_data, get_stock_data_fast, test_api_connection, set_mock_data_mode
from modules.market_sentiment import get_market_sentiment, get_hot_sectors

init_db()


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


st.set_page_config(page_title="AI股票复盘系统 V6", page_icon="🧠", layout="wide")
st.title("🧠 AI股票复盘系统（多Agent架构版）")

col_title, col_test, col_mock = st.columns([3, 1, 1])
with col_test:
    if st.button("🔍 检测网络连接", help="测试API连接状态"):
        with st.spinner("正在检测网络连接..."):
            results = test_api_connection()
            
            st.subheader("🔌 网络检测结果")
            for result in results:
                status_color = "green" if result['status'] == 'success' else "yellow" if result['status'] == 'warning' else "red"
                status_icon = "✅" if result['status'] == 'success' else "⚠️" if result['status'] == 'warning' else "❌"
                
                st.markdown(f"""
                <div style="padding: 8px; border-radius: 4px; margin-bottom: 8px; background-color: #f8f9fa;">
                    <strong>{status_icon} {result['name']}</strong>
                    <br/>
                    <span style="color: {status_color};">{result['message']}</span>
                    <span style="float: right; font-size: 12px; color: #666;">{result['response_time']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            all_success = all(r['status'] == 'success' for r in results)
            if all_success:
                st.success("🎉 所有API连接正常！")
            else:
                st.warning("⚠️ 部分API连接存在问题，请检查网络设置")

with col_mock:
    mock_mode = st.toggle("🎭 模拟数据模式", help="使用模拟数据进行测试（无需网络）")
    if mock_mode:
        set_mock_data_mode(True)
        st.success("✅ 已启用模拟数据模式")
    else:
        set_mock_data_mode(False)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ 单Prompt分析（快速）", "🧠 多Agent分析（完整）", "📊 各Agent详情", "📈 历史记录", "📅 情绪周期"])

with tab1:
    st.header("⚡ 单Prompt分析（快速）")

    companies = get_company_list()
    if not companies:
        companies = []

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 刷新数据", key="refresh_companies", help="点击从akshare全量加载公司数据"):
            load_company_data()
            st.rerun()
    with col_info:
        st.caption(f"📊 已加载 {len(companies)} 家公司 | 输入名称或代码搜索，选择或直接输入")

    stock_display_options = [f"{c['name']}({c['code']})" for c in companies]
    stock_code_map = {f"{c['name']}({c['code']})": c['code'] for c in companies}
    stock_name_map = {f"{c['name']}({c['code']})": c['name'] for c in companies}

    selected = st.selectbox(
        "输入股票名称或代码，如：贵州茅台、600519",
        options=[""] + stock_display_options,
        key="stock_autocomplete",
        format_func=lambda x: x if x else "请选择股票..."
    )

    if selected:
        stock = stock_code_map.get(selected, selected)
        stock_name = stock_name_map.get(selected, "")
    else:
        stock = ""
        stock_name = ""




    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
    with col1:
        selected_date = st.date_input(
            "日期选择", 
            value=datetime.now(),
            key="date_single",
            help="选择要分析的日期（极速模式下可用）"
        )

    with col3:
        api_placeholder = st.empty()
        if st.button("🔗 检测", key="check_api", help="点击检查API连接"):
            with st.spinner("检测中..."):
                balance_ok, balance_msg = check_balance(force_refresh=True)
            if balance_ok:
                api_placeholder.success("✅")
            else:
                api_placeholder.error("❌")
        else:
            api_placeholder.caption("🔗 API")

    with col4:
        data_mode = st.radio(
            "📊 模式",
            ["⚡极速", "📈标准", "🔍完整"],
            index=0,
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
        if not stock:
            st.error("请输入股票代码")
        else:
            progress_bar = st.progress(0, text="准备开始...")

            progress_bar.progress(10, text="📈 步骤 1/5：正在获取个股数据...")
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
                    sentiment_data = {
                        "market_mood": "待获取", 
                        "limit_up_count": 0, 
                        "limit_down_count": 0,
                        "bomb_rate": 0.0,
                        "avg_change": 0.0,
                        "rising_count": 0,
                        "falling_count": 0,
                        "flat_count": 0,
                        "total_count": 0,
                        "rise_ratio": 0.0,
                        "strong_count": 0,
                        "weak_count": 0,
                        "total_volume": 0.0,
                        "market_cap": 0.0
                    }
                    hot_sectors = []
                    with st.expander("📈 个股行情数据", expanded=True):
                        st.json(stock_data)
                    st.info("⚡ 极速模式：已获取个股数据，市场情绪已省略")
                    progress_bar.progress(40, text="✅ 准备完成，开始AI分析...")

                elif selected_data_mode == "📈 标准模式（个股+市场情绪）":
                    progress_bar.progress(40, text="📊 步骤 2/5：正在获取市场情绪数据...")
                    with st.spinner("📊 正在获取市场情绪数据..."):
                        sentiment_data = get_market_sentiment()
                    progress_bar.progress(60, text="✅ 市场情绪数据获取成功")

                    with st.expander("📈 个股行情数据", expanded=True):
                        st.json(stock_data)
                    with st.expander("📊 市场情绪数据", expanded=True):
                        st.json(sentiment_data)
                    hot_sectors = []
                    progress_bar.progress(70, text="✅ 数据准备完成，开始AI分析...")

                else:
                    progress_bar.progress(40, text="📊 步骤 2/5：正在获取市场情绪数据...")
                    with st.spinner("📊 正在获取市场情绪数据..."):
                        sentiment_data = get_market_sentiment()
                    progress_bar.progress(55, text="✅ 市场情绪数据获取成功")

                    progress_bar.progress(60, text="🔥 步骤 3/5：正在获取热门板块数据...")
                    with st.spinner("🔥 正在获取热门板块数据..."):
                        hot_sectors = get_hot_sectors()
                    progress_bar.progress(70, text="✅ 热门板块数据获取成功")

                    with st.expander("📈 个股行情数据", expanded=True):
                        st.json(stock_data)
                    with st.expander("📊 市场情绪数据", expanded=True):
                        st.json(sentiment_data)
                    with st.expander("🔥 热门概念板块", expanded=True):
                        st.json(hot_sectors)
                    progress_bar.progress(75, text="✅ 数据准备完成，开始AI分析...")

                progress_bar.progress(80, text="🤖 步骤 4/5：AI正在分析中...")
                with st.spinner("🤖 AI正在分析中..."):
                    result = stock_review(stock, stock_data, sentiment_data, hot_sectors)

                progress_bar.progress(90, text="💾 步骤 5/5：正在保存分析结果...")
                if sentiment_data and sentiment_data.get('market_mood') is not None:
                    mode = selected_data_mode.split('（')[0].strip()
                    market_mood = sentiment_data.get('market_mood', '未知')
                    if market_mood == "待获取":
                        market_mood = f"极速模式"
                    save_analysis(stock_data, result, market_mood, mode)

                progress_bar.progress(100, text="✅ 分析完成！")
                st.balloons()
                st.success("✅ 分析完成！已保存到历史记录。")

                st.subheader("🎯 AI复盘结果")
                st.markdown(result)

                st.download_button(
                    label="📥 下载报告",
                    data=result,
                    file_name=f"复盘报告_{stock}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

with tab2:
    st.header("🧠 多Agent协同分析（完整）")

    col1, col2 = st.columns([2, 1])

    with col1:
        stock = st.text_input("输入股票代码（如 601360）", placeholder="601360", key="stock_multi")

    with col2:
        st.write("")
        st.write("")

    if st.button("🚀 启动多Agent分析", key="analyze_multi", type="primary"):
        if not stock:
            st.error("请输入股票代码")
        else:
            progress_bar = st.progress(0, text="准备开始...")

            progress_bar.progress(20, text="📊 步骤 1/3：构建统一市场上下文...")
            with st.spinner("🔄 正在构建MarketContext..."):
                try:
                    from core.data_provider import DataProvider
                    context = DataProvider.build_context(stock)
                    
                    with st.expander("📈 个股行情数据", expanded=True):
                        st.json(context.stock_data)
                    with st.expander("📊 市场情绪数据", expanded=True):
                        st.json(context.market_sentiment)
                    with st.expander("🔥 热门板块数据", expanded=True):
                        st.json(context.sectors)
                    
                    progress_bar.progress(50, text="✅ MarketContext构建完成")
                    
                except Exception as e:
                    st.error(f"构建MarketContext失败: {str(e)}")
                    progress_bar.progress(100, text="❌ 分析失败")
                    st.stop()

            progress_bar.progress(60, text="🤖 步骤 2/3：多Agent协同分析...")
            with st.spinner("🧠 各Agent正在分析中..."):
                result = multi_agent_review(stock)

            progress_bar.progress(85, text="✅ Agent分析完成")
            agent_results = result["agent_results"]
            final_report = result["final_report"]
            summary = result["summary"]

            st.session_state.agent_results = agent_results
            st.session_state.last_stock_code = stock

            progress_bar.progress(90, text="💾 步骤 3/3：保存分析结果...")
            market_mood = agent_results.get("sentiment", {}).get("data", {}).get("market_mood", "")
            market_data = agent_results["market"]["data"]
            market_data_for_save = {
                "code": market_data.get("stock_code"),
                "name": market_data.get("stock_name"),
                "price": market_data.get("price"),
                "price_change_pct": market_data.get("price_change_pct"),
                "volume": market_data.get("volume"),
                "turnover_rate": market_data.get("turnover_rate"),
                "amplitude": market_data.get("amplitude")
            }
            save_analysis(market_data_for_save, final_report, market_mood, "多Agent分析")

            progress_bar.progress(100, text="✅ 分析完成！")
            st.balloons()
            st.success("✅ 多Agent分析完成！")

            with st.expander("📋 快速摘要", expanded=True):
                cols = st.columns(3)
                with cols[0]:
                    st.metric("股票", summary["股票"])
                    st.metric("情绪周期", summary["情绪周期"])
                with cols[1]:
                    st.metric("市场情绪", summary["市场情绪"])
                    st.metric("主线", summary["主线"])
                with cols[2]:
                    st.metric("风险等级", summary["风险等级"])
                    st.metric("短线操作", summary["短线可做"])

                st.info(f"操作建议：{summary['操作建议']}")

            st.subheader("🎯 AI综合分析报告")
            st.markdown(final_report)

            st.download_button(
                label="📥 下载完整报告",
                data=f"""
{'='*50}
股票：{summary['股票']}
分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

【快速摘要】
情绪周期：{summary['情绪周期']}
市场情绪：{summary['市场情绪']}
主线：{summary['主线']}
风险等级：{summary['风险等级']}
操作建议：{summary['操作建议']}

{'='*50}
【Agent详情】
{'='*50}

{agent_results['format']['market']}

{agent_results['format']['sentiment']}

{agent_results['format']['sector']}

{agent_results['format']['flow']}

{agent_results['format']['risk']}

{'='*50}
【AI综合分析报告】
{'='*50}

{final_report}
""",
                file_name=f"多Agent复盘报告_{stock}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

with tab3:
    st.header("📊 各Agent分析详情")

    st.info("💡 请先在「多Agent分析」tab中进行一次分析，然后查看各Agent详情会自动更新")

    if 'agent_results' not in st.session_state:
        st.session_state.agent_results = None
        st.session_state.last_stock_code = None

    if st.button("🔄 刷新数据"):
        st.rerun()

    if st.session_state.agent_results:
        st.subheader("📊 行情Agent")
        st.text(st.session_state.agent_results["format"]["market"])

        st.subheader("📉 情绪Agent")
        st.text(st.session_state.agent_results["format"]["sentiment"])

        st.subheader("🧭 板块Agent")
        st.text(st.session_state.agent_results["format"]["sector"])

        st.subheader("💰 资金Agent")
        st.text(st.session_state.agent_results["format"]["flow"])

        st.subheader("⚠️ 风险Agent")
        st.text(st.session_state.agent_results["format"]["risk"])

with tab4:
    st.header("📈 历史记录")
    from modules.storage import get_all_stocks, get_stock_history, delete_stock_history

    if 'refresh_history' not in st.session_state:
        st.session_state.refresh_history = True

    col_refresh, col_count = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 刷新列表"):
            st.session_state.refresh_history = True
            st.rerun()

    with col_count:
        if st.button("📊 查看全部历史"):
            st.session_state.refresh_history = True

    if st.session_state.refresh_history:
        all_stocks = get_all_stocks()
        st.session_state.cached_all_stocks = all_stocks
    else:
        all_stocks = st.session_state.get('cached_all_stocks', get_all_stocks())

    if all_stocks:
        stock_options = [f"{s['name']} ({s['code']})" for s in all_stocks]
        stock_codes = [s['code'] for s in all_stocks]

        selected = st.selectbox("选择股票查看历史", options=stock_options, key="history_select")

        if selected:
            idx = stock_options.index(selected)
            selected_code = stock_codes[idx]
            history = get_stock_history(selected_code)

            if history:
                st.write(f"**共找到 {len(history)} 条历史记录**")

                for i, record in enumerate(history):
                    mode_label = record.get('mode', '未知') if record.get('mode') else '极速'
                    with st.expander(f"📅 {record['created_at']} - {record['stock_name']}({record['stock_code']}) [{mode_label}]"):
                        col_info, col_report = st.columns([1, 3])

                        with col_info:
                            st.metric("价格", f"{record['price']:.2f}")
                            st.metric("涨跌", f"{record['change_pct']:.2f}%")
                            st.metric("模式", record.get('mode', '极速'))
                            st.metric("市场情绪", record['market_mood'])

                        with col_report:
                            st.markdown(record['ai_summary'])

                        col_download, col_delete = st.columns([1, 1])
                        with col_download:
                            st.download_button(
                                label="📥 下载报告",
                                data=record['ai_summary'],
                                file_name=f"复盘报告_{record['stock_code']}_{record['created_at'][:10]}.txt",
                                mime="text/plain",
                                key=f"download_history_{i}_{record['id']}"
                            )
                        with col_delete:
                            if st.button(f"🗑️ 删除记录", key=f"delete_history_{i}_{record['id']}"):
                                if delete_stock_history(record['id']):
                                    st.success("✅ 记录已删除")
                                    st.session_state.refresh_history = True
                                    st.rerun()
                                else:
                                    st.error("❌ 删除失败")
            else:
                st.info("该股票暂无历史记录")
    else:
        st.info("暂无历史记录，先在「单Prompt分析」或「多Agent分析」tab中分析股票吧！")

with tab5:
    st.header("📅 市场情绪周期")
    from modules.storage import get_market_sentiment_history, save_market_sentiment, get_cached_market_sentiment
    from modules.market_sentiment import analyze_sentiment

    @st.cache_data(ttl=300)
    def cached_get_sentiment_history():
        return get_market_sentiment_history()

    col_refresh, col_save = st.columns([1, 1])
    with col_refresh:
        if st.button("🔄 刷新情绪数据"):
            st.rerun()

    with col_save:
        if st.button("💾 保存当前情绪"):
            sentiment = analyze_sentiment()
            save_market_sentiment(sentiment)
            st.success("✅ 情绪数据已保存")

    cached_sentiment = get_cached_market_sentiment()
    if cached_sentiment:
        sentiment = cached_sentiment
        st.info("📦 使用缓存的市场情绪数据")
    else:
        with st.spinner("📊 获取市场情绪数据..."):
            sentiment = analyze_sentiment()

    st.subheader("📊 当前市场情绪")

    cols = st.columns(3)
    with cols[0]:
        st.metric("涨停家数", sentiment['limit_up_count'])
        st.metric("跌停家数", sentiment['limit_down_count'])
    with cols[1]:
        st.metric("上涨家数", f"{sentiment['rising_count']} ({sentiment['rise_ratio']}%)")
        st.metric("市场平均涨跌", f"{sentiment['avg_change']}%")
    with cols[2]:
        st.metric("强势股", sentiment['strong_count'])
        st.metric("弱势股", sentiment['weak_count'])

    st.info(f"**情绪周期：{sentiment.get('emotion_cycle', '未知')}** | **市场情绪：{sentiment['market_mood']}** | **操作信号：{'可以做短线' if sentiment.get('做多信号') else '观望' if sentiment.get('做多信号') is False else '观察'}**")

    sentiment_history = cached_get_sentiment_history()

    if sentiment_history:
        st.subheader("📅 历史情绪记录")

        for record in sentiment_history:
            mood_emoji = {
                "高潮": "🔥",
                "强势": "📈",
                "震荡": "⚡",
                "偏弱": "📊",
                "退潮": "📉"
            }.get(record['market_mood'], "❓")

            with st.expander(f"{mood_emoji} {record['date']} - 情绪：{record['market_mood']}"):
                cols = st.columns(3)
                with cols[0]:
                    st.metric("涨停", record['limit_up_count'])
                    st.metric("跌停", record['limit_down_count'])
                with cols[1]:
                    st.metric("上涨", f"{record['rising_count']} ({record['rise_ratio']:.1f}%)")
                    st.metric("平均涨跌", f"{record['avg_change']}%")
                with cols[2]:
                    st.metric("强势股", record['strong_count'])
                    st.metric("弱势股", record['weak_count'])
