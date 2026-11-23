"""Streamlit UI for deterministic, offline Quant Research Lab.

All code lives behind render_quant_lab(), so importing it from app.py has
no page_config or side effects. CSV content remains in this Streamlit session.
"""
import io

import pandas as pd
import streamlit as st

from quant_research.engine import Costs, backtest_ma


def render_quant_lab():
    st.markdown("### 📊 Quant Research Lab · 量化研究实验室")
    st.caption("离线回测 MVP · 上传日线 CSV · 不连接券商、不下单、不调用 AI 生成交易结论")
    st.info("研究用途：目前未模拟停牌、涨跌停成交限制、最低佣金、冲击成本和复权现金流。")

    with st.expander("数据格式 / 方法说明", expanded=False):
        st.code("date,open,high,low,close,volume\n2026-01-05,10,10.3,9.8,10.1,200000", language="csv")
        st.write("使用上一交易日收盘形成信号，下一交易日开盘执行；下一开盘估值，样本末尾按最后可用开盘价平仓。")
        st.write("默认卖出税 0 bps 仅用于 ETF 演示，A 股股票请根据交易日期自行设置实际适用税费。")

    with st.form("quant_lab_parameters"):
        uploaded = st.file_uploader("上传本地历史日线 CSV", type="csv", key="quant_lab_csv")
        a, b, c = st.columns(3)
        with a:
            fast = st.number_input("短均线周期", min_value=1, value=5, step=1, key="quant_ma_fast")
            slow = st.number_input("长均线周期", min_value=2, value=20, step=1, key="quant_ma_slow")
        with b:
            commission = st.number_input("单边佣金 (bps)", min_value=0.0, max_value=1000.0,
                                         value=3.0, step=1.0, key="quant_commission")
            slippage = st.number_input("单边滑点 (bps)", min_value=0.0, max_value=1000.0,
                                       value=3.0, step=1.0, key="quant_slippage")
        with c:
            sell_tax = st.number_input("卖出税费 (bps)", min_value=0.0, max_value=1000.0,
                                      value=0.0, step=1.0, key="quant_sell_tax")
            st.caption("1 bps = 0.01%")
        submitted = st.form_submit_button("运行离线回测", type="primary")

    if not submitted:
        st.caption("上传 CSV，设置参数后点击「运行离线回测」。")
        return
    if uploaded is None:
        st.warning("请先上传 CSV 日线数据。")
        return

    try:
        raw = pd.read_csv(io.BytesIO(uploaded.getvalue()), encoding="utf-8-sig")
        raw = raw.rename(columns={"日期": "date", "开盘": "open", "最高": "high",
                                  "最低": "low", "收盘": "close", "成交量": "volume"})
        curve, stats = backtest_ma(raw, int(fast), int(slow),
                                   Costs(float(commission), float(slippage), float(sell_tax)))
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        st.error(f"数据校验或回测失败：{exc}")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("策略累计收益", f"{stats['total_return']:.2%}")
    m2.metric("最大回撤", f"{stats['max_drawdown']:.2%}")
    sharp = stats["annualized_sharpe_rf0"]
    m3.metric("夏普（RF=0）", "—" if sharp is None else f"{sharp:.2f}")
    m4.metric("建仓 / 平仓次数", f"{stats['entries']} / {stats['exits_including_liquidation']}")
    st.caption(f"观察区间 {stats['observations']} · 持仓暴露 {stats['exposure']:.1%} · 基准为未扣费买入持有")
    st.subheader("策略净值与基准")
    st.line_chart(curve.set_index("date")[["equity", "benchmark_equity"]])
    st.subheader("计算明细与证据")
    st.dataframe(curve, use_container_width=True)
    st.download_button("下载回测明细 CSV",
                       data=curve.to_csv(index=False).encode("utf-8-sig"),
                       file_name="quant_research_results.csv",
                       mime="text/csv",
                       key="quant_lab_export")
