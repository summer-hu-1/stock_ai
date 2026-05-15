"""
AgentOS - 统一的 AI 认知层入口

V10 架构：Agent 只做解释，不做计算
所有计算由 QuantCore 完成，AgentOS 仅负责理解和解释

核心原则：
- ❌ 不计算因子/信号/评分
- ❌ 不直接读数据
- ✅ 接收 QuantResult，理解并解释
- ✅ 生成市场分析和操作建议
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

from core.quant_core import get_quant_core
from core.quant_core.models import QuantResult

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


class AgentOS:
    """
    AgentOS - 统一的 AI 认知层入口
    """

    def __init__(self):
        self.quant_core = get_quant_core()

    def analyze_stock(
        self,
        stock_code: str,
        market: str = "cn",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行完整的股票分析（QuantCore + AgentOS）

        Args:
            stock_code: 股票代码
            market: 市场
            use_cache: 是否使用缓存

        Returns:
            Dict: {
                "success": bool,
                "quant_result": QuantResult,  # 量化结果
                "agent_report": str,           # Agent 报告
                "summary": dict,               # 快速摘要
                "generated_at": datetime
            }
        """
        logger.info(f"🤖 AgentOS 开始分析: {stock_code}")

        try:
            # 1. 调用 QuantCore 计算（AgentOS 不做计算）
            quant_result = self.quant_core.analyze(stock_code, market)

            # 2. AgentOS 解释结果
            agent_report = self._generate_report(quant_result)

            # 3. 生成快速摘要
            summary = self._generate_summary(quant_result)

            logger.info(f"✅ AgentOS 分析完成: {stock_code}")

            return {
                "success": True,
                "quant_result": quant_result,
                "agent_report": agent_report,
                "summary": summary,
                "generated_at": datetime.now()
            }

        except Exception as e:
            logger.error(f"❌ AgentOS 分析失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stock_code": stock_code
            }

    def _generate_report(self, quant_result: QuantResult) -> str:
        """
        Agent 核心功能：解释 QuantResult

        这是 AgentOS 的核心工作：理解数字，生成分析报告
        """
        score = quant_result.score
        factors = quant_result.factors
        signals = quant_result.signals
        state = quant_result.state
        leaders = quant_result.leaders

        today = datetime.now()
        today_str = today.strftime("%Y年%m月%d日")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

        prompt = f"""你是A股顶级游资复盘分析师，擅长多维度市场分析。

【时间信息】
今天日期：{today_str}（{weekday}）

【分析对象】
股票代码：{quant_result.code}

【QuantCore 量化结果（纯数字，请你解释）】
【综合评分】
最终评分：{score.final_score:.1f}/100
交易信号：{score.signal}
置信度：{score.confidence:.1%}

【因子得分】
趋势得分：{score.trend_score:.1f}/100
动量得分：{score.momentum_score:.1f}/100
量能得分：{score.volume_score:.1f}/100
波动率得分：{score.volatility_score:.1f}/100
强度得分：{score.strength_score:.1f}/100
龙头加分：{score.leader_bonus:.1f}
市场状态调整：{score.market_state_adj:.1f}

【市场状态】
市场周期：{state.cycle}
周期阶段：{state.cycle_stage}
情绪得分：{state.emotion_score:.1f}/100
情绪趋势：{state.emotion_trend}
涨停家数：{state.limit_up_count}家
下跌家数：{state.limit_down_count}家
上涨比例：{state.rise_ratio:.1%}
总成交额：{state.total_volume}万亿
北向资金：{state.north_money}亿
风险等级：{state.risk_level}
热门板块：{', '.join(state.top_sectors) if state.top_sectors else '暂未获取'}

【龙头信息】
是否龙头：{'是' if leaders.is_leader else '否'}
龙头类型：{leaders.leader_type}
龙头得分：{leaders.leader_score:.1f}/100

【核心任务】
请根据 QuantCore 提供的纯数字结果，以【分析对象】的个股为绝对核心，生成一份专业、简洁、针对该股的交易分析报告。

【严格要求】
1. **所有分析必须围绕该股展开**，不要泛泛而谈市场，市场背景只是用来衬托个股分析
2. **数字解读** - 解释 QuantCore 的数字含义（为什么这个评分？这个信号意味着什么？）
3. **市场关联** - 结合市场周期和情绪，该股在当前环境下处于什么位置？
4. **风险收益** - 就针对这只股票，现在值不值得参与？风险多大，收益空间多大？
5. **具体操作** - 给出针对这只股票的具体可执行建议（买入价位/持有策略/卖出点位/观望理由）
6. **明日走势** - 明天这只股票最可能怎么走？有什么关键点位需要关注？

输出要简洁有力，每一句话都要有根据（基于 QuantCore 的数据），不要说废话。
"""

        try:
            from core.model_config import get_current_model
            current_model = get_current_model()

            response = client.chat.completions.create(
                model=current_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"AI报告生成失败: {str(e)}"

    def _generate_summary(self, quant_result: QuantResult) -> Dict[str, Any]:
        """
        生成快速摘要
        """
        score = quant_result.score
        state = quant_result.state
        leaders = quant_result.leaders

        return {
            "股票": quant_result.code,
            "最终评分": f"{score.final_score:.1f}/100",
            "交易信号": score.signal,
            "置信度": f"{score.confidence:.1%}",
            "市场周期": state.cycle,
            "情绪得分": f"{state.emotion_score:.1f}/100",
            "风险等级": state.risk_level,
            "是否龙头": "是" if leaders.is_leader else "否",
            "龙头类型": leaders.leader_type
        }

    def generate_quick_report(self, stock_code: str) -> Dict[str, Any]:
        """
        快速报告（保持向后兼容）
        """
        return self.analyze_stock(stock_code)


# 全局单例
_agent_os_instance = None


def get_agent_os() -> AgentOS:
    """获取 AgentOS 单例"""
    global _agent_os_instance
    if _agent_os_instance is None:
        _agent_os_instance = AgentOS()
    return _agent_os_instance
