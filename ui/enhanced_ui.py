"""
UI Enhancement Module - 增强UI以充分展示系统能力

V10.1架构具备强大的量化、策略和AI能力，此模块提供完整的UI展示
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# ==================== 量化分析模块 ====================
def show_quant_analysis(stock_code: str, market: str = "cn"):
    """
    展示量化分析结果（QuantCore能力）
    """
    from quant import get_quant_core
    
    st.subheader("📊 QuantCore 量化分析")
    st.info("💡 QuantCore是系统的核心计算引擎，负责所有数学计算")
    
    with st.spinner("🔄 正在运行量化分析..."):
        quant_core = get_quant_core()
        result = quant_core.analyze(stock_code, market)
    
    if not result:
        st.error(f"无法获取股票 {stock_code} 的量化数据")
        return
    
    # 显示综合评分
    st.subheader("🏆 综合评分")
    score = result.score
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("最终评分", f"{score.final_score:.1f}/100")
    with col2:
        st.metric("交易信号", score.signal)
    with col3:
        st.metric("置信度", f"{score.confidence:.1%}")
    with col4:
        st.metric("风险等级", score.risk_level)
    
    # 显示因子得分
    st.subheader("📈 因子得分详情")
    factors = {
        "趋势得分": score.trend_score,
        "动量得分": score.momentum_score,
        "量能得分": score.volume_score,
        "波动率得分": score.volatility_score,
        "强度得分": score.strength_score,
        "龙头加分": score.leader_bonus,
        "市场调整": score.market_state_adj
    }
    df_factors = pd.DataFrame(list(factors.items()), columns=["因子", "得分"])
    fig = px.bar(df_factors, x="因子", y="得分", color="得分", 
                 color_continuous_scale="RdYlGn", range_y=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    
    # 显示信号
    st.subheader("📡 信号分析")
    signals = result.signals
    if signals:
        signal_df = pd.DataFrame([{
            "信号类型": s.signal_type,
            "方向": s.direction,
            "强度": s.strength,
            "置信度": s.confidence,
            "描述": s.description
        } for s in signals])
        st.dataframe(signal_df)
    
    # 显示市场状态
    st.subheader("🌡️ 市场状态")
    state = result.state
    if state:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("市场周期", state.cycle)
        with col2:
            st.metric("周期阶段", state.cycle_stage)
        with col3:
            st.metric("情绪得分", f"{state.emotion_score:.1f}/100")
        with col4:
            st.metric("风险等级", state.risk_level)
        
        st.markdown(f"**情绪趋势**: {state.emotion_trend}")
        st.markdown(f"**涨停家数**: {state.limit_up_count}家")
        st.markdown(f"**下跌家数**: {state.limit_down_count}家")
        st.markdown(f"**上涨比例**: {state.rise_ratio:.1%}")
        st.markdown(f"**总成交额**: {state.total_volume}万亿")
        st.markdown(f"**北向资金**: {state.north_money}亿")
        if state.top_sectors:
            st.markdown(f"**热门板块**: {', '.join(state.top_sectors)}")
    
    # 显示龙头信息
    st.subheader("👑 龙头分析")
    leaders = result.leaders
    if leaders:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("是否龙头", "是" if leaders.is_leader else "否")
        with col2:
            st.metric("龙头类型", leaders.leader_type)
        with col3:
            st.metric("龙头得分", f"{leaders.leader_score:.1f}/100")

# ==================== AI分析模块 ====================
def show_agent_analysis(stock_code: str, market: str = "cn"):
    """
    展示AI分析结果（AgentOS能力）
    """
    from services.agent.agent_os import get_agent_os
    
    st.subheader("🤖 AgentOS AI分析")
    st.info("💡 AgentOS是AI认知层，负责理解和解释QuantCore的量化结果")
    
    with st.spinner("🧠 AI正在分析中..."):
        agent_os = get_agent_os()
        result = agent_os.analyze_stock(stock_code, market)
    
    if not result.get("success"):
        st.error(f"AI分析失败: {result.get('error', '未知错误')}")
        return
    
    # 显示AI报告
    st.subheader("📝 AI分析报告")
    st.markdown(result["agent_report"])
    
    # 显示快速摘要
    st.subheader("🎯 快速摘要")
    summary = result["summary"]
    col1, col2, col3, col4 = st.columns(4)
    for i, (key, value) in enumerate(list(summary.items())[:4]):
        with [col1, col2, col3, col4][i]:
            st.metric(key, value)
    
    # 显示量化结果（供参考）
    with st.expander("📊 原始量化数据"):
        quant_result = result["quant_result"]
        st.json(quant_result.to_dict())

# ==================== 策略执行模块 ====================
def show_strategy_execution():
    """
    展示策略执行功能（ExecutionOS能力）
    """
    from strategy import get_strategy_os
    
    st.subheader("⚙️ StrategyOS 策略执行")
    st.info("💡 StrategyOS负责策略调度、风险控制和模拟交易执行")
    
    # 初始化执行引擎
    execution_os = get_strategy_os(initial_capital=100000.0)
    
    # 显示账户状态
    st.subheader("💰 账户概览")
    account = execution_os.get_account_status()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("初始资金", f"¥{account.initial_capital:,.2f}")
    with col2:
        st.metric("当前总资产", f"¥{account.total_assets:,.2f}")
    with col3:
        st.metric("持仓市值", f"¥{account.position_value:,.2f}")
    with col4:
        st.metric("可用现金", f"¥{account.available_cash:,.2f}")
    
    # 显示持仓
    st.subheader("📦 当前持仓")
    positions = execution_os.get_positions()
    if positions:
        pos_df = pd.DataFrame([{
            "股票代码": p.code,
            "股票名称": p.name,
            "持仓数量": p.quantity,
            "成本价": f"¥{p.cost_price:.2f}",
            "现价": f"¥{p.current_price:.2f}",
            "盈亏": f"{p.pnl:.2f}%",
            "市值": f"¥{p.market_value:.2f}"
        } for p in positions])
        st.dataframe(pos_df)
    else:
        st.info("📭 暂无持仓")
    
    # 显示交易历史
    st.subheader("📋 交易历史")
    trades = execution_os.get_trade_history()
    if trades:
        trade_df = pd.DataFrame([{
            "时间": t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "股票代码": t.code,
            "方向": t.side,
            "数量": t.quantity,
            "成交价": f"¥{t.price:.2f}",
            "金额": f"¥{t.amount:.2f}"
        } for t in trades])
        st.dataframe(trade_df)
    else:
        st.info("📭 暂无交易记录")
    
    # 模拟下单功能
    st.subheader("📝 模拟下单")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        order_code = st.text_input("股票代码", "000002")
    with col2:
        order_side = st.selectbox("方向", ["buy", "sell"])
    with col3:
        order_price = st.number_input("价格", value=10.0)
    with col4:
        order_quantity = st.number_input("数量", value=100, step=100)
    with col5:
        if st.button("提交订单", type="primary"):
            result = execution_os.place_order(
                code=order_code,
                side=order_side,
                price=order_price,
                quantity=order_quantity
            )
            if result["success"]:
                st.success(f"✅ 订单已提交: {result['order_id']}")
                st.rerun()
            else:
                st.error(f"❌ 下单失败: {result['error']}")

# ==================== 信号扫描模块 ====================
def show_signal_scanner():
    """
    展示信号扫描功能（SignalService能力）
    """
    from services.signal_service import get_signal_service
    
    st.subheader("📡 信号扫描中心")
    st.info("💡 全市场信号扫描与分析")
    
    signal_service = get_signal_service()
    
    # 市场概览
    summary = signal_service.get_signal_summary()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📡 今日信号", summary["total_signals"])
    with col2:
        st.metric("📈 看多", summary["up_signals"])
    with col3:
        st.metric("📉 看空", summary["down_signals"])
    with col4:
        st.metric("⚡ 平均强度", summary["avg_strength"])
    
    # 今日信号列表
    st.subheader("📋 今日信号")
    df = signal_service.get_today_signals()
    if not df.empty:
        st.dataframe(df[["code", "name", "signal_type", "direction", "strength", "date"]])
    else:
        st.info("📭 暂无今日数据")
    
    # 高强度信号
    st.subheader("🔥 强势信号股票")
    top_df = signal_service.get_top_signals(limit=10, min_strength=0.7)
    if not top_df.empty:
        st.dataframe(top_df[["code", "name", "signal_type", "direction", "strength"]])
    
    # 执行扫描
    if st.button("🔄 执行全市场扫描", type="primary"):
        from scheduler.daily_scan import run_daily_scan
        with st.spinner("🔄 正在扫描全市场..."):
            run_daily_scan()
        st.success("✅ 扫描完成！")
        st.rerun()

# ==================== 主页面组件 ====================
def render_enhanced_ui():
    """
    渲染增强版UI，充分展示系统能力
    """
    st.sidebar.title("🧠 AI Quant OS V10.1")
    st.sidebar.markdown("---")
    
    # 功能导航
    nav_options = [
        "📊 量化分析",
        "🤖 AI分析",
        "⚙️ 策略执行",
        "📡 信号扫描",
        "📈 历史记录",
        "📅 情绪周期"
    ]
    
    selected_nav = st.sidebar.selectbox("功能导航", nav_options)
    
    # 股票选择（全局）
    stock_code = st.sidebar.text_input("股票代码", "000002")
    market = st.sidebar.selectbox("市场", ["cn", "hk", "us"], index=0)
    
    # 根据选择显示不同功能
    if selected_nav == "📊 量化分析":
        show_quant_analysis(stock_code, market)
    elif selected_nav == "🤖 AI分析":
        show_agent_analysis(stock_code, market)
    elif selected_nav == "⚙️ 策略执行":
        show_strategy_execution()
    elif selected_nav == "📡 信号扫描":
        show_signal_scanner()
    elif selected_nav == "📈 历史记录":
        show_history()
    elif selected_nav == "📅 情绪周期":
        show_sentiment_cycle()

def show_history():
    """显示历史记录"""
    from modules.storage import get_all_stocks, get_stock_history
    
    st.subheader("📈 历史记录")
    all_stocks = get_all_stocks()
    
    if all_stocks:
        stock_options = [f"{s['name']} ({s['code']})" for s in all_stocks]
        selected = st.selectbox("选择股票", options=stock_options)
        
        if selected:
            stock_code = selected.split("(")[-1][:-1]
            history = get_stock_history(stock_code)
            
            if history:
                for record in history:
                    with st.expander(f"📅 {record['created_at']} - {record['stock_name']}"):
                        st.markdown(record.get('analysis_result', '无分析结果'))
            else:
                st.info("📭 暂无历史记录")
    else:
        st.info("📭 暂无股票数据")

def show_sentiment_cycle():
    """显示情绪周期"""
    from modules.market_sentiment import get_market_sentiment_history
    
    st.subheader("📅 市场情绪周期")
    history = get_market_sentiment_history(limit=30)
    
    if history:
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 情绪趋势图
        fig = px.line(df, x='date', y='emotion_score', 
                     title='情绪得分趋势',
                     labels={'emotion_score': '情绪得分', 'date': '日期'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 市场周期分布
        cycle_counts = df['market_cycle'].value_counts()
        fig2 = px.pie(values=cycle_counts.values, names=cycle_counts.index,
                      title='市场周期分布')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("📭 暂无情绪历史数据")

if __name__ == "__main__":
    render_enhanced_ui()
