from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def check_balance():
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=1
        )
        return "API 连接成功"
    except Exception as e:
        error_str = str(e)
        if "402" in error_str or "Insufficient Balance" in error_str:
            return "余额不足，请到 DeepSeek 平台充值"
        return f"错误: {error_str}"

def stock_review(stock_code, stock_data, market_sentiment=None, hot_sectors=None):
    today = datetime.now()
    today_str = today.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

    sentiment_str = ""
    if market_sentiment:
        sentiment_str = f"""
    【市场整体情绪】
    - 涨停家数: {market_sentiment['limit_up_count']}家
    - 跌停家数: {market_sentiment['limit_down_count']}家
    - 市场情绪: {market_sentiment['market_mood']}
    - 上涨家数: {market_sentiment['rising_count']}家 ({market_sentiment['rise_ratio']}%)
    - 下跌家数: {market_sentiment['falling_count']}家
    - 强势股(≥5%): {market_sentiment['strong_count']}家
    - 弱势股(≤-5%): {market_sentiment['weak_count']}家
    - 市场平均涨跌: {market_sentiment['avg_change']:.2f}%
    - 炸板率: {market_sentiment['bomb_rate']*100:.1f}%
    """

    hot_sectors_str = ""
    if hot_sectors and len(hot_sectors) > 0:
        hot_sectors_str = "\n    【热门概念板块TOP5】"
        for i, sector in enumerate(hot_sectors[:5], 1):
            hot_sectors_str += f"\n    {i}. {sector['name']}: +{sector['change_pct']}% (换手{sector['turnover_rate']}%)"

    data_str = f"""
    【股票基本信息】
    股票名称：{stock_data['name']}
    股票代码：{stock_data['code']}
    最新价：{stock_data['price']}元
    涨跌幅：{stock_data['price_change_pct']:.2f}%
    涨停状态：{stock_data['limit_status']}
    今开：{stock_data['open']} | 最高：{stock_data['high']} | 最低：{stock_data['low']}
    成交额：{stock_data['volume']/1e8:.2f}亿元
    换手率：{stock_data['turnover_rate']:.2f}%
    量比：{stock_data['volume_ratio']:.2f}
    振幅：{stock_data['amplitude']:.2f}%
    总市值：{stock_data['market_cap']/1e8:.2f}亿元
    流通市值：{stock_data['float_share']/1e8:.2f}亿元
    """

    prompt = f"""你是A股顶级游资复盘分析师，精通龙头战法、情绪周期、资金流向分析。

【重要时间信息】
- 今天日期：{today_str}（{weekday}）
- 分析时间点：今日收盘后复盘
{sentiment_str}
{hot_sectors_str}
{data_str}

【基于市场情绪 + 真实行情数据进行分析】

请先判断当前市场情绪周期，再对上述股票进行深度复盘分析。

【分析框架】

第一步：判断市场情绪周期
- 当前是：高潮 / 强势 / 震荡 / 退潮 哪个阶段？
- 涨停家数({market_sentiment['limit_up_count'] if market_sentiment else '?'}家)反映了什么情绪？
- 是否适合做连板龙头？

第二步：个股深度分析

1. **连板高度分析**
   - 近期最高连板数？
   - 该股属于第几梯队？
   - 梯度完整度？

2. **龙头地位评估**
   - 是板块龙头还是跟风补涨？
   - 是否有卡位机会？
   - 与当前热门板块的关联度？

3. **资金逻辑**
   - 今日主力资金净流入/流出？
   - 缩量还是放量？
   - 换手率情况？

4. **风险点**
   - 核按钮风险（隔夜摁跌停风险）？
   - 监管风险？
   - 解套盘压力？

5. **明日预期与操作建议**
   - 开盘预期（高开/低开/平开）？
   - 能否继续连板？
   - 操作建议（锁仓/减仓/清仓/空仓）？

【输出要求】
- 用专业A股短线交易风格输出
- 先给出市场情绪判断，再进行个股分析
- 每个维度分析简洁有力，不废话
- 关键数据要量化
- 最终给出明确操作建议
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=2000
    )

    return response.choices[0].message.content
