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

def stock_review(stock_code, stock_data):
    today = datetime.now()
    today_str = today.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

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

{data_str}

【基于真实行情数据进行分析】

请对上述股票进行深度复盘分析。

【必须输出的分析维度】

1. **情绪周期定位**
   - 当前处于发酵期/加速期/分歧期/退潮期哪个阶段？
   - 昨日涨停今日溢价情况？
   - 最高标到达几板？

2. **连板高度分析**
   - 近期最高连板数？
   - 该股属于第几梯队？
   - 梯度完整度（1进2、2进3、3进4情况）？

3. **龙头地位评估**
   - 是板块龙头还是跟风补涨？
   - 龙头切换信号？
   - 卡位机会？

4. **板块强度**
   - 所属板块今日整体强度？
   - 板块内涨停数量？
   - 板块指数走势？

5. **游资风格**
   - 今日主要参与的游资类型（量化、庄游混合、合力打造）？
   - 席位溢价情况？
   - 龙虎榜情况？

6. **资金逻辑**
   - 今日主力资金净流入/流出？
   - 缩量还是放量？
   - 换手率情况？

7. **市场合力**
   - 散户情绪（讨论热度、股吧热度）？
   - 机构动向？
   - 外资动向？

8. **风险点**
   - 核按钮风险（隔夜摁跌停风险）？
   - 监管风险？
   - 解套盘压力？

9. **明日预期**
   - 开盘预期（高开/低开/平开）？
   - 能否继续连板？
   - 操作建议（锁仓/减仓/清仓）？

10. **龙头潜力最终判断**
    - 是/否具备龙头潜力
    - 理由简述

【输出要求】
- 用专业A股短线交易风格输出
- 每个维度分析简洁有力
    - 不废话，不废话，不废话
    - 重点突出，数据说话
- 关键数据要量化（涨幅、换手、金额）
- 最终给出明确操作建议
- 注意：今天是{today_str}，请基于这个时间点和上面的真实行情数据进行分析
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
