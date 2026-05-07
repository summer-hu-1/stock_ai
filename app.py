import streamlit as st
from deepseek import stock_review, check_balance
from modules.market_data import get_stock_data, format_stock_data

st.title("AI股票复盘（真实数据版）")

with st.expander("⚠️ API 状态检查"):
    if st.button("检查余额"):
        with st.spinner("检查中..."):
            status = check_balance()
            st.info(status)

stock = st.text_input("输入股票代码（如 601360）")

if st.button("开始复盘"):
    with st.spinner("正在获取真实行情数据..."):
        data = get_stock_data(stock)

        if not data:
            st.error("未找到股票数据，请检查股票代码是否正确")
        else:
            st.success("✅ 数据获取成功")

            with st.expander("📊 真实行情数据"):
                st.json(data)

            with st.spinner("AI正在基于真实数据分析..."):
                result = stock_review(stock, data)

                st.subheader("🤖 AI复盘结果")
                st.write(result)
