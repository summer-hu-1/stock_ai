import streamlit as st
from deepseek import stock_review, check_balance
from modules.market_data import get_stock_data, format_stock_data
from modules.market_sentiment import get_market_sentiment, get_hot_sectors, format_market_sentiment

st.title("AI股票复盘（市场情绪驱动版）")

with st.expander("⚠️ API 状态检查"):
    if st.button("检查余额"):
        with st.spinner("检查中..."):
            status = check_balance()
            st.info(status)

col1, col2 = st.columns([2, 1])

with col1:
    stock = st.text_input("输入股票代码（如 601360）")

with col2:
    st.write("")  # spacing
    st.write("")

if st.button("🎯 开始复盘"):
    with st.spinner("正在获取市场情绪数据..."):
        market_sentiment = get_market_sentiment()
        hot_sectors = get_hot_sectors()

        if market_sentiment:
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
                result = stock_review(stock, stock_data, market_sentiment, hot_sectors)

                st.subheader("🎯 AI复盘结果")
                st.write(result)
