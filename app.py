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

# 如果未登录，显示登录页面
if not is_logged_in():
    from auth.pages import show_login_page
    show_login_page()
else:
    # 登录后才导入业务模块
    from modules.storage import init_db, save_analysis, save_market_sentiment, get_all_companies, save_company_info, get_company_by_code, get_all_stocks, get_stock_history, get_market_sentiment_history, get_cached_market_sentiment
    from deepseek import stock_review, check_balance
    from modules.market_data import get_stock_data, get_stock_data_fast
    from modules.market_sentiment import get_market_sentiment, get_hot_sectors, analyze_sentiment

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

    # 显示用户信息侧边栏
    from auth.pages import show_user_info
    show_user_info()

    # 模型选择区域
    from core.model_config import (
        get_all_models, 
        get_current_model, 
        set_current_model, 
        format_price_info,
        get_model_display_name,
        get_model_description
    )

    col_model, col_api_check, col_quota = st.columns([3, 1, 1])

    with col_model:
        models = get_all_models()
        current_model = get_current_model()
        
        model_options = {f"{m['display_name']} - {m['description']}": m["name"] for m in models}
        
        selected_model_display = next(k for k, v in model_options.items() if v == current_model)
        
        selected_model = st.selectbox(
            "🤖 选择AI模型",
            options=list(model_options.keys()),
            index=list(model_options.values()).index(current_model),
            key="model_selector"
        )
        
        selected_model_name = model_options[selected_model]
        selected_model_config = next(m for m in models if m["name"] == selected_model_name)
        
        if selected_model_name != current_model:
            if set_current_model(selected_model_name):
                st.success(f"✅ 已切换到 {selected_model_config['display_name']}")
                st.rerun()
        
        st.caption(f"{format_price_info(selected_model_config)} | Max Tokens: {selected_model_config['max_tokens']}")

    with col_api_check:
        api_status = check_balance()
        if api_status[0]:
            st.success("✅ API正常")
        else:
            st.error(f"❌ {api_status[1]}")

    with col_quota:
        quota_info = get_user_quota_info()
        if quota_info['unlimited']:
            st.info("🎉 无限分析次数")
        else:
            st.caption(f"今日配额: {quota_info['used']}/{quota_info['limit']}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["⚡ 单Prompt分析（快速）", "🧠 多Agent分析（完整）", "📊 各Agent详情", "📈 历史记录", "📅 情绪周期", "📈 日线数据"])

    with tab1:
        st.header("⚡ 单Prompt分析（快速）")

        # 使用共享组件
        from ui.components import stock_selector_with_market

        stock, stock_name, market = stock_selector_with_market(
            key_prefix="single",
            default_market="cn",
            show_refresh=True,
            on_refresh_callback=load_company_data
        )

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
            # 检查配额
            from auth.auth import can_analyze, record_analysis_usage
            can_do, msg = can_analyze()
            if not can_do:
                st.error(msg)
            elif not stock:
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
                            try:
                                if hot_sectors and isinstance(hot_sectors, list):
                                    valid_sectors = []
                                    for sector in hot_sectors:
                                        if isinstance(sector, dict) and 'name' in sector and 'change_pct' in sector:
                                            valid_sectors.append(sector)
                                    
                                    if valid_sectors:
                                        st.markdown("### 🔥 热门概念板块 TOP 10")
                                        for i, sector in enumerate(valid_sectors[:10], 1):
                                            change_pct = sector.get('change_pct', 0)
                                            change_color = "red" if change_pct > 0 else "green"
                                            change_sign = "+" if change_pct > 0 else ""
                                            st.markdown(f"{i}. **{sector['name']}**: <span style='color:{change_color};font-weight:bold;'>{change_sign}{change_pct}%</span> (换手 {sector.get('turnover_rate', 0)}%, 涨/跌 {sector.get('rise_count', 0)}/{sector.get('fall_count', 0)})", unsafe_allow_html=True)
                                    else:
                                        st.info("📦 暂无有效的热门概念数据")
                                else:
                                    st.info("📦 暂无热门概念数据，使用模拟数据")
                                    from modules.market_sentiment import _get_mock_hot_sectors
                                    mock_sectors = _get_mock_hot_sectors()
                                    st.markdown("### 🔥 热门概念板块 TOP 10（模拟数据）")
                                    for i, sector in enumerate(mock_sectors[:10], 1):
                                        change_color = "red" if sector['change_pct'] > 0 else "green"
                                        st.markdown(f"{i}. **{sector['name']}**: <span style='color:{change_color};font-weight:bold;'>+{sector['change_pct']}%</span> (换手 {sector['turnover_rate']}%, 涨/跌 {sector['rise_count']}/{sector['fall_count']})", unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"显示热门板块时出错: {e}")
                                st.info("📦 暂无热门概念数据")
                        progress_bar.progress(75, text="✅ 数据准备完成，开始AI分析...")

                    progress_bar.progress(80, text="🤖 步骤 4/5：AI正在分析中...")
                    with st.spinner("🤖 AI正在分析中..."):
                        result = stock_review(stock, stock_data, sentiment_data, hot_sectors)

                    # 记录使用次数
                    record_analysis_usage()

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
        st.header("🧠 统一Pipeline分析（完整）")

        # 使用共享组件
        from ui.components import stock_selector_with_market

        stock, stock_name, market = stock_selector_with_market(
            key_prefix="multi",
            default_market="cn",
            show_refresh=True
        )

        if st.button("🚀 启动Pipeline分析", key="analyze_multi", type="primary"):
            # 检查配额
            from auth.auth import can_analyze, record_analysis_usage
            can_do, msg = can_analyze()
            if not can_do:
                st.error(msg)
            elif not stock:
                st.error("请输入股票代码")
            else:
                progress_bar = st.progress(0, text="准备开始...")

                # 使用统一Pipeline进行分析
                from core.analysis_pipeline import get_pipeline
                
                progress_bar.progress(30, text="🔧 初始化分析管线...")
                pipeline = get_pipeline()

                progress_bar.progress(50, text="🚀 执行完整分析流程...")
                with st.spinner("🔄 正在执行分析..."):
                    result = pipeline.analyze(stock, market=market)

                # 记录使用次数
                record_analysis_usage()

                progress_bar.progress(85, text="✅ 分析完成")

                if result.get("success"):
                    # 保存结果到session
                    st.session_state.last_stock_code = stock
                    st.session_state.pipeline_result = result

                    progress_bar.progress(95, text="💾 保存分析结果...")
                    
                    progress_bar.progress(100, text="✅ 分析完成！")
                    st.balloons()
                    st.success("✅ Pipeline分析完成！")

                    # 显示综合评分
                    with st.expander("📋 分析摘要", expanded=True):
                        cols = st.columns(4)
                        with cols[0]:
                            st.metric("综合评分", f"{result['score']}/100")
                        with cols[1]:
                            st.metric("风险等级", result.get("risk_level", "中"))
                        with cols[2]:
                            st.metric("信号", result.get("signal", "观望"))
                        with cols[3]:
                            st.metric("耗时", f"{result.get('elapsed_time', 0):.2f}秒")

                    # 显示因子分析结果
                    with st.expander("📊 因子分析", expanded=False):
                        if result.get("factors"):
                            st.json(result["factors"])
                        else:
                            st.info("暂无因子数据")

                    # 显示信号分析结果
                    with st.expander("📡 信号分析", expanded=False):
                        if result.get("signals"):
                            st.json(result["signals"])
                        else:
                            st.info("暂无信号数据")

                    # 显示龙头识别结果
                    with st.expander("🐉 龙头识别", expanded=False):
                        if result.get("leaders"):
                            is_leader = result["leaders"].get("is_leader", False)
                            st.markdown(f"**是否龙头**: {'👑 是龙头股' if is_leader else '普通股票'}")
                            st.json(result["leaders"])
                        else:
                            st.info("暂无龙头数据")

                    # 显示Agent分析结果
                    if result.get("agent") and result["agent"].get("success"):
                        st.subheader("🎯 AI综合分析报告")
                        agent_data = result["agent"].get("data", {})
                        if isinstance(agent_data, dict):
                            st.markdown(agent_data.get("final_report", "暂无报告"))
                        else:
                            st.markdown(str(agent_data))
                    else:
                        st.info("Agent分析未完成")
                else:
                    st.error(f"分析失败: {result.get('error', '未知错误')}")

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

                            st.download_button(
                                label="📥 下载报告",
                                data=record['ai_summary'],
                                file_name=f"复盘报告_{record['stock_code']}_{record['created_at'][:10]}.txt",
                                mime="text/plain",
                                key=f"download_history_{i}_{record['id']}"
                            )
                else:
                    st.info("该股票暂无历史记录")
        else:
            st.info("暂无历史记录，先在「单Prompt分析」或「多Agent分析」tab中分析股票吧！")

    with tab5:
        st.header("📅 市场情绪周期")
        from core.market_memory import MarketMemory

        @st.cache_data(ttl=300)
        def cached_get_sentiment_history():
            return get_market_sentiment_history()

        col_refresh, col_save, col_snapshot = st.columns([1, 1, 1])
        with col_refresh:
            if st.button("🔄 刷新情绪数据"):
                st.rerun()

        with col_save:
            if st.button("💾 保存当前情绪"):
                sentiment = analyze_sentiment()
                save_market_sentiment(sentiment)
                st.success("✅ 情绪数据已保存")

        with col_snapshot:
            if st.button("📸 生成市场快照"):
                sentiment = analyze_sentiment()
                memory = MarketMemory()
                success = memory.save_snapshot(sentiment)
                if success:
                    st.success("✅ 市场快照已保存")
                else:
                    st.error("❌ 市场快照保存失败")

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

        st.divider()
        st.subheader("🧠 市场记忆 - 历史趋势分析")

        memory = MarketMemory()
        context = memory.get_market_context(days=5)

        if context.get("has_context"):
            col_cycle, col_emotion = st.columns(2)
            with col_cycle:
                st.info(f"**📊 市场周期**：{context['market_cycle']['cycle']}（{context['market_cycle']['stage']}）")
                st.caption(context['market_cycle']['description'])

            with col_emotion:
                trend_emoji = {
                    "上升": "📈",
                    "下降": "📉",
                    "震荡": "⚡"
                }.get(context['emotion_trend']['direction'], "❓")
                st.info(f"**{trend_emoji} 情绪趋势**：{context['emotion_trend']['direction']}")
                st.caption(context['emotion_trend']['description'])

            col_sector, col_leader = st.columns(2)
            with col_sector:
                st.info(f"**🔄 板块轮动**")
                st.caption(context['sector_rotation']['description'])

            with col_leader:
                st.info(f"**🐉 龙头切换**")
                st.caption(context['leader_rotation']['description'])

            col_risk = st.columns(1)
            with col_risk[0]:
                risk_emoji = {
                    "上升": "⚠️",
                    "下降": "✅",
                    "稳定": "➖"
                }.get(context['risk_change']['trend'], "❓")
                st.info(f"**{risk_emoji} 风险变化**：{context['risk_change']['trend']}")
                st.caption(context['risk_change']['description'])

            st.divider()
            st.subheader("📈 趋势图表")

            snapshots = memory.get_recent_snapshots(10)
            if len(snapshots) >= 2:
                import pandas as pd

                dates = [s.date for s in reversed(snapshots)]
                emotion_scores = [s.emotion_score for s in reversed(snapshots)]
                limit_ups = [s.limit_up_count for s in reversed(snapshots)]

                chart_df = pd.DataFrame({
                    "日期": dates,
                    "情绪得分": emotion_scores,
                    "涨停家数": limit_ups
                })

                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.line_chart(chart_df.set_index("日期")[["情绪得分"]])

                with col_chart2:
                    st.line_chart(chart_df.set_index("日期")[["涨停家数"]])
            else:
                st.info("📊 历史数据不足，需要至少2天的市场快照才能生成趋势图表")

        st.divider()
        st.subheader("🤖 AI市场洞察")

        col_insight_days, col_generate = st.columns([1, 1])
        with col_insight_days:
            insight_days = st.selectbox("分析天数", options=[3, 5, 7, 10], index=1, key="insight_days")
        with col_generate:
            if st.button("🧠 生成AI洞察", key="generate_insight"):
                with st.spinner("🤖 AI正在分析市场..."):
                    insight = memory.generate_market_insight(days=insight_days)
                    memory.save_insight(insight)
                    st.success("✅ AI洞察已生成并保存")
                    st.rerun()

        latest_insight = memory.get_latest_insight()
        if latest_insight:
            col_state, col_confidence = st.columns([3, 1])
            with col_state:
                st.info(f"**📊 市场状态**：{latest_insight.current_state}")
                st.caption(latest_insight.state_description)
            with col_confidence:
                confidence_color = "🟢" if latest_insight.confidence > 0.8 else "🟡" if latest_insight.confidence > 0.6 else "🔴"
                st.metric(f"{confidence_color} 置信度", f"{latest_insight.confidence*100:.0f}%")

            col_trend, col_risk = st.columns(2)
            with col_trend:
                with st.expander("📈 趋势分析", expanded=True):
                    st.markdown(latest_insight.trend_analysis)

            with col_risk:
                with st.expander("⚠️ 风险提示", expanded=True):
                    st.warning(latest_insight.risk_alert)

            col_opp, col_action = st.columns(2)
            with col_opp:
                with st.expander("💡 机会提示", expanded=True):
                    st.success(latest_insight.opportunity)

            with col_action:
                with st.expander("🎯 操作建议", expanded=True):
                    st.info(latest_insight.action_suggestion)

            if latest_insight.key_changes:
                with st.expander("🔑 关键观察点"):
                    for change in latest_insight.key_changes:
                        st.markdown(f"- {change}")

            st.divider()
            st.subheader("📜 历史洞察记录")

            recent_insights = memory.get_recent_insights(10)
            if recent_insights:
                for insight in recent_insights:
                    with st.expander(f"📅 {insight.date} - {insight.current_state}"):
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("市场状态", insight.current_state)
                            st.metric("置信度", f"{insight.confidence*100:.0f}%")
                        with cols[1]:
                            st.caption("**风险提示**")
                            st.warning(insight.risk_alert)
                        with cols[2]:
                            st.caption("**操作建议**")
                            st.info(insight.action_suggestion)
            else:
                st.info("📊 暂无历史洞察记录")
        
        st.divider()
        st.subheader("📥 历史快照拉取")
        
        col_start, col_end, col_fetch = st.columns([2, 2, 1])
        with col_start:
            start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=7), key="history_start")
        with col_end:
            end_date = st.date_input("结束日期", value=datetime.now(), key="history_end")
        with col_fetch:
            if st.button("🚀 拉取历史快照", key="fetch_history"):
                if start_date > end_date:
                    st.error("❌ 开始日期不能大于结束日期")
                else:
                    with st.spinner(f"⏳ 正在拉取 {start_date} 到 {end_date} 的快照..."):
                        result = memory.fetch_date_range(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                        st.success(f"✅ 拉取完成！成功: {result['success']} | 失败: {result['failed']} | 跳过: {result['skipped']}")
        
        col_update_days, col_update = st.columns([2, 1])
        with col_update_days:
            update_days = st.selectbox("增量更新最近N天", options=[7, 14, 30, 60], index=2, key="update_days")
        with col_update:
            if st.button("🔄 增量更新快照", key="update_snapshots"):
                with st.spinner(f"⏳ 正在增量更新最近 {update_days} 天的快照..."):
                    result = memory.update_missing_snapshots(days=update_days)
                    st.success(f"✅ 更新完成！缺失: {result['total_missing']} | 成功: {result['success']} | 失败: {result['failed']}")
        
        snapshots = memory.get_recent_snapshots(365)
        if snapshots:
            earliest_date = snapshots[-1].date
            latest_date = snapshots[0].date
            st.info(f"📊 当前已有快照: {len(snapshots)} 天（{earliest_date} 至 {latest_date}）")
        else:
            st.info("📊 当前暂无快照数据")

    with tab6:
        st.header("📈 A股日线数据")

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

