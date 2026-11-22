"""Standalone quant research dashboard; no live market or brokerage connections."""
import io

import pandas as pd
import streamlit as st

from quant_research.engine import Costs, backtest_ma

st.set_page_config(page_title="Quant Research Lab", page_icon="📊", layout="wide")
st.title("Quant Research Lab · 量化研究实验室")
st.caption("离线研究 MVP · 只读取主动上传的日线 CSV · 不连接券商或自动交易")
st.info("历史研究不代表未来收益；当前未模拟停牌、涨跌停成交限制、最低佣金、市场冲击。")

upload = st.file_uploader("上传日线 CSV（日期、开高低收、成交量）", type=["csv"])
with st.expander("CSV 格式及模型说明", expanded=upload is None):
    st.code("date,open,high,low,close,volume\n2026-01-05,10,10.3,9.8,10.1,200000", language="csv")
    st.write("使用上一交易日完整收盘形成 MA 信号；最早下一交易日开盘交易。")
    st.write("默认卖出税 0 bps 仅为 ETF 示例；研究 A 股股票时须自行配置适用税费。")
fast = st.sidebar.number_input("短均线周期", min_value=1, value=5, step=1)
slow = st.sidebar.number_input("长均线周期", min_value=2, value=20, step=1)
commission = st.sidebar.number_input("单边佣金 (bps)", 0.0, 1000.0, 3.0, 1.0)
slippage = st.sidebar.number_input("单边滑点 (bps)", 0.0, 1000.0, 3.0, 1.0)
sell_tax = st.sidebar.number_input("卖出税费 (bps)", 0.0, 1000.0, 0.0, 1.0)
if upload is None:
    st.stop()

try:
    raw = pd.read_csv(io.BytesIO(upload.getvalue()), encoding="utf-8-sig")
    raw = raw.rename(columns={"日期": "date", "开盘": "open", "最高": "high",
                              "最低": "low", "收盘": "close", "成交量": "volume"})
    curve, stats = backtest_ma(raw, int(fast), int(slow), Costs(commission, slippage, sell_tax))
except (ValueError, KeyError, TypeError, UnicodeDecodeError, pd.errors.ParserError) as exc:
    st.error(f"数据校验或回测失败：{exc}")
    st.stop()
col1, col2, col3, col4 = st.columns(4)
col1.metric("策略累计收益", f"{stats['total_return']:.2%}")
col2.metric("最大回撤", f"{stats['max_drawdown']:.2%}")
col3.metric("夏普 (RF=0)", "—" if stats["annualized_sharpe_rf0"] is None else f"{stats['annualized_sharpe_rf0']:.2f}")
col4.metric("建仓/平仓", f"{stats['entries']}/{stats['exits_including_liquidation']}")
st.caption(f"{stats['observations']} 个开盘区间 · 持仓比例 {stats['exposure']:.1%} · 基准未扣成本")
st.subheader("累计净值")
st.line_chart(curve.set_index("date")[["equity", "benchmark_equity"]])
st.subheader("逐日计算明细")
st.dataframe(curve, use_container_width=True)
st.download_button("导出回测 CSV", curve.to_csv(index=False).encode("utf-8-sig"),
                   "quant_research_results.csv", "text/csv")
