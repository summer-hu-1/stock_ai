"""
AgentOS 解释器

V10 架构核心：只做AI解释，不做计算

职责：
1. 解释量化结果
2. 生成交易洞察
3. 评估风险
4. 生成分析报告
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AgentOS:
    """
    AgentOS - Agent认知层

    只做解释，不做计算

    使用示例：
    ```python
    from agent import get_agent_os

    agent = get_agent_os()

    # 分析股票（需要QuantCore的结果）
    report = agent.analyze_stock("000002", "cn")

    # 生成交易洞察
    insight = agent.generate_trading_insight(quant_result)
    ```
    """

    def __init__(self):
        self.model = "deepseek"
        self._api_initialized = False
        self._init_api()

    def _init_api(self):
        """初始化API"""
        try:
            from deepseek import stock_review
            self._api = stock_review
            self._api_initialized = True
            logger.info("DeepSeek API 初始化成功")
        except ImportError:
            logger.warning("DeepSeek API 未安装")
        except Exception as e:
            logger.warning(f"DeepSeek API 初始化失败: {e}")

    def analyze_stock(self, code: str, market: str = "cn") -> str:
        """
        分析股票（完整分析）

        Args:
            code: 股票代码
            market: 市场代码

        Returns:
            str: 分析报告
        """
        from quant import get_quant_core
        from data import get_datahub

        datahub = get_datahub()
        df = datahub.get_ohlcv_dataframe(code, market)

        if df is None or df.empty:
            return "无法获取数据"

        quant_core = get_quant_core()
        quant_result = quant_core.analyze(code, market)

        if quant_result is None:
            return "量化分析失败"

        return self._generate_report(quant_result)

    def generate_trading_insight(
        self,
        quant_result: Dict[str, Any]
    ) -> str:
        """
        生成交易洞察

        Args:
            quant_result: QuantCore的分析结果

        Returns:
            str: 交易洞察
        """
        if not quant_result:
            return "无法生成交易洞察"

        factors = quant_result.get("factors", {})
        signals = quant_result.get("signals", {})
        state = quant_result.get("state", {})
        score = quant_result.get("score", 0.5)

        insight_parts = []

        if score >= 0.7:
            insight_parts.append("综合评分较高，建议关注买入机会")
        elif score >= 0.5:
            insight_parts.append("综合评分中等，建议观望")
        else:
            insight_parts.append("综合评分较低，建议谨慎")

        direction = signals.get("direction", "neutral")
        if direction == "up":
            insight_parts.append("短期趋势向上")
        elif direction == "down":
            insight_parts.append("短期趋势向下")

        market_state = state.get("state", "unknown")
        if market_state == "rally":
            insight_parts.append("市场处于主升阶段")
        elif market_state == "retreat":
            insight_parts.append("市场处于退潮阶段，注意风险")

        return "；".join(insight_parts)

    def _generate_report(self, quant_result: Dict[str, Any]) -> str:
        """生成分析报告"""
        if not quant_result:
            return "量化分析结果为空"

        code = quant_result.get("code", "")
        factors = quant_result.get("factors", {})
        signals = quant_result.get("signals", {})
        state = quant_result.get("state", {})
        score = quant_result.get("score", 0.5)

        if not self._api_initialized:
            return self._generate_simple_report(quant_result)

        try:
            prompt = self._build_prompt(code, factors, signals, state, score)
            response = self._api(prompt)
            return response if response else self._generate_simple_report(quant_result)
        except Exception as e:
            logger.error(f"AI报告生成失败: {e}")
            return self._generate_simple_report(quant_result)

    def _build_prompt(
        self,
        code: str,
        factors: Dict,
        signals: Dict,
        state: Dict,
        score: float
    ) -> str:
        """构建Prompt"""
        prompt = f"""分析股票 {code} 的量化结果：

因子评分：
- 趋势: {factors.get('trend', 0):.2f}
- 量能: {factors.get('volume', 0):.2f}
- 动量: {factors.get('momentum', 0):.2f}
- 波动率: {factors.get('volatility', 0):.2f}
- 强度: {factors.get('strength', 0):.2f}

信号状态：
- 方向: {signals.get('direction', 'neutral')}
- 信号强度: {signals.get('strength', 0):.2f}
- 市场状态: {state.get('state', 'unknown')}

综合评分: {score:.2f}

请给出简明的分析报告，包括：
1. 当前市场情况总结
2. 主要风险点
3. 交易建议
"""
        return prompt

    def _generate_simple_report(self, quant_result: Dict[str, Any]) -> str:
        """生成简单报告（无API时）"""
        code = quant_result.get("code", "")
        factors = quant_result.get("factors", {})
        signals = quant_result.get("signals", {})
        state = quant_result.get("state", {})
        score = quant_result.get("score", 0.5)

        report = f"""# {code} 量化分析报告

## 综合评分
{score:.2f} / 1.00

## 因子分析
| 因子 | 评分 |
|------|------|
| 趋势 | {factors.get('trend', 0):.2f} |
| 量能 | {factors.get('volume', 0):.2f} |
| 动量 | {factors.get('momentum', 0):.2f} |
| 波动率 | {factors.get('volatility', 0):.2f} |
| 强度 | {factors.get('strength', 0):.2f} |

## 信号状态
- 方向: {signals.get('direction', 'neutral')}
- 信号强度: {signals.get('strength', 0):.2f}

## 市场状态
- 状态: {state.get('state', 'unknown')}
- 描述: {state.get('description', '暂无')}

## 交易建议
{self.generate_trading_insight(quant_result)}
"""
        return report


_agent_os_instance: Optional[AgentOS] = None


def get_agent_os() -> AgentOS:
    """获取AgentOS单例"""
    global _agent_os_instance
    if _agent_os_instance is None:
        _agent_os_instance = AgentOS()
    return _agent_os_instance
