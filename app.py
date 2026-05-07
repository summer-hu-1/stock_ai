import streamlit as st
from deepseek import stock_review, check_balance
from modules.market_data import get_stock_data, format_stock_data
from modules.market_sentiment import get_market_sentiment, get_hot_sectors, format_market_sentiment
from modules.storage import (
    init_db, save_analysis, save_market_sentiment,
    get_stock_history, get_market_sentiment_history,
    get_all_stocks, format_history_for_display
)

init_db()

st.set_page_config(page_title="AI股票复盘系统", layout="wide")
st.title("🎯 AI股票复盘系统（历史记录版）")

tab1, tab2, tab3 = st.tabs(["📈 个股分析", "📊 历史记录", "📅 情绪周期"])

with tab1:
    with st.expander("⚠️ API 状态检查"):
        if st.button("检查余额"):
            with st.spinner("检查中..."):
                status = check_balance()
                st.info(status)

    col1, col2 = st.columns([2, 1])

    with col1:
        stock = st.text_input("输入股票代码（如 601360）", placeholder="601360")

    with col2:
        st.write("")
        st.write("")

    if st.button("🎯 开始复盘"):
        with st.spinner("正在获取市场情绪数据..."):
            market_sentiment = get_market_sentiment()
            hot_sectors = get_hot_sectors()

            if market_sentiment:
                save_market_sentiment(market_sentiment)
                st.success(f"✅ 市场情绪获取成功 - 今日情绪：【{market_sentiment['market_mood']}】")

                with st.expander("📊 市场情绪数据"):
                    sentiment_display = {
                        "涨停家数": market_sentiment['limit_up_count'],
                        "跌停家数": market_sentiment['limit_down_count'],
                        "市场情绪": market_sentiment['market_mood'],
                        "上涨家数": f"{market_sentiment['rising_count']} ({market_sentiment['rise_ratio']}%)",
                        "下跌家数": market_sentiment['falling_count'],
                        "强势股(≥5%)": market_sentiment['strong_count'],
                        "弱势股(≤-5%)": market_sentiment['weak_count'],
                        "平均涨跌": f"{market_sentiment['avg_change']}%",
                        "炸板率": f"{market_sentiment['bomb_rate']*100:.1f}%"
                    }
                    st.json(sentiment_display)

                    if hot_sectors:
                        st.write("**🔥 热门概念板块TOP5**")
                        for i, sector in enumerate(hot_sectors[:5], 1):
                            st.write(f"{i}. **{sector['name']}**: +{sector['change_pct']}% (换手{sector['turnover_rate']}%)")
            else:
                st.error("获取市场情绪数据失败")

        with st.spinner("正在获取股票行情数据..."):
            stock_data = get_stock_data(stock)

            if not stock_data:
                st.error("未找到股票数据，请检查股票代码是否正确")
            else:
                st.success(f"✅ {stock_data['name']} 数据获取成功")

                with st.expander("📈 个股行情数据"):
                    st.json(stock_data)

                with st.spinner("🤖 AI正在基于市场情绪+真实数据分析..."):
                    market_mood = market_sentiment['market_mood'] if market_sentiment else ""
                    result = stock_review(stock, stock_data, market_sentiment, hot_sectors)

                    save_analysis(stock_data, result, market_mood)

                    st.subheader("🎯 AI复盘结果")

                    col_result, col_actions = st.columns([4, 1])

                    with col_result:
                        st.markdown(result)

                    with col_actions:
                        st.write("")
                        st.write("")
                        if st.button("📋 复制报告", key="copy_current"):
                            st.code(result, language=None)
                            st.success("✅ 已生成可复制文本")

with tab2:
    st.subheader("📊 历史复盘记录")

    all_stocks = get_all_stocks()

    if all_stocks:
        stock_options = [f"{s['name']} ({s['code']})" for s in all_stocks]
        stock_codes = [s['code'] for s in all_stocks]

        selected = st.selectbox("选择股票查看历史", options=stock_options)

        if selected:
            idx = stock_options.index(selected)
            selected_code = stock_codes[idx]

            history = get_stock_history(selected_code)

            if history:
                st.write(f"**共找到 {len(history)} 条历史记录**")

                for i, record in enumerate(history, 1):
                    with st.expander(f"📅 {record['created_at']} - {record['stock_name']}({record['stock_code']}) - 点击展开完整报告"):
                        col_info, col_data = st.columns([1, 3])

                        with col_info:
                            st.write("**行情数据**")
                            st.metric("价格", f"{record['price']:.2f}")
                            st.metric("涨跌", f"{record['change_pct']:.2f}%")
                            st.metric("换手率", f"{record['turnover']:.2f}%")
                            st.metric("市场情绪", record['market_mood'])

                        with col_data:
                            st.write("**📝 AI完整分析报告**")

                            st.markdown("---")
                            st.markdown(record['ai_summary'])
                            st.markdown("---")

                            col_copy_btn, col_copy_hint = st.columns([1, 3])
                            with col_copy_btn:
                                if st.button("📋 复制报告", key=f"copy_{record['id']}"):
                                    st.code(record['ai_summary'], language=None)
                                    st.success("✅ 已生成可复制文本，请选中上方代码块进行复制")

                            with col_copy_hint:
                                st.caption("💡 点击上方按钮生成可复制文本块，或直接选中文本复制")
            else:
                st.info("该股票暂无历史记录")
    else:
        st.info("暂无历史记录，先在「个股分析」tab中分析股票吧！")

with tab3:
    st.subheader("📅 市场情绪周期记录")

    sentiment_history = get_market_sentiment_history()

    if sentiment_history:
        st.write(f"**共找到 {len(sentiment_history)} 天市场情绪记录**")

        for record in sentiment_history:
            mood_emoji = {
                "高潮": "🔥",
                "强势": "📈",
                "震荡": "⚡",
                "退潮": "📉"
            }.get(record['market_mood'], "❓")

            with st.expander(f"{mood_emoji} {record['date']} - 情绪：{record['market_mood']}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("涨停家数", record['limit_up_count'])
                    st.metric("跌停家数", record['limit_down_count'])

                with col2:
                    st.metric("上涨家数", f"{record['rising_count']} ({record['rise_ratio']:.1f}%)")
                    st.metric("强势股", record['strong_count'])

                with col3:
                    st.metric("平均涨跌", f"{record['avg_change']:.2f}%")
                    st.metric("炸板率", f"{record['bomb_rate']*100:.1f}%")

    else:
        st.info("暂无市场情绪历史记录，先在「个股分析」tab中触发一次分析吧！")
