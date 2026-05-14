from typing import Optional
from datetime import datetime
import time
import logging
import pandas as pd

from core.datahub import get_datahub, OHLCV
from core.quant_core.models import (
    FactorOutput,
    SignalOutput,
    StateOutput,
    LeaderOutput,
    ScoreOutput,
    QuantResult
)
from core.quant_core.score_engine import ScoreEngine
from factors.factor_engine import FactorEngine
from signals.signal_engine import SignalEngine
from leaders.leader_engine import LeaderEngine
from core.market_memory import MarketMemory


logger = logging.getLogger(__name__)


class QuantCore:
    """
    量化核心引擎 - 唯一计算入口

    原则：
        ❌ 不调用 Agent
        ❌ 不调用 LLM
        ❌ 不生成文本
        ✅ 输入数据 → 输出数值

    核心流程：
        1. 数据获取（通过 DataHub）
        2. 因子计算
        3. 信号生成
        4. 龙头识别
        5. 市场状态获取
        6. 综合评分
        7. 输出 QuantResult
    """

    def __init__(self):
        self.datahub = get_datahub()
        self.factor_engine = FactorEngine()
        self.signal_engine = SignalEngine()
        self.leader_engine = LeaderEngine()
        self.market_memory = MarketMemory()
        self.score_engine = ScoreEngine()

    def analyze(
        self,
        code: str,
        market: str = "cn",
        days: int = 250,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> QuantResult:
        """
        完整分析流程：因子→信号→龙头→市场状态→评分

        Args:
            code: 股票代码
            market: 市场类型
            days: 获取历史天数
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            QuantResult: 量化完整输出
        """
        start_time = time.time()
        logger.info(f"🚀 QuantCore 开始分析: {code}")

        try:
            # 1. 获取日线数据（DataFrame 格式，兼容旧接口）
            df = self.datahub.get_ohlcv_dataframe(code, market, days, start_date, end_date)
            if df is None or len(df) == 0:
                logger.error(f"❌ 无法获取 {code} 的日线数据")
                raise ValueError(f"无法获取 {code} 的日线数据")

            # 2. 因子计算
            factor_output = self._calculate_factors(df, code)

            # 3. 信号生成
            signal_output = self._generate_signals(df, factor_output, code)

            # 4. 龙头识别
            leader_output = self._detect_leader(df, factor_output, signal_output, code)

            # 5. 获取市场状态
            state_output = self._get_market_state(end_date)

            # 6. 综合评分
            score_output = self.score_engine.calculate(
                code=code,
                factors=factor_output,
                signals=signal_output,
                state=state_output,
                leader_output=leader_output
            )

            # 7. 计算耗时
            elapsed_ms = int((time.time() - start_time) * 1000)

            # 8. 构建 QuantResult
            result = QuantResult(
                code=code,
                date=datetime.now(),
                factors=factor_output,
                signals=signal_output,
                state=state_output,
                leaders=leader_output,
                score=score_output,
                elapsed_ms=elapsed_ms
            )

            logger.info(f"✅ QuantCore 分析完成: {code} ({elapsed_ms}ms)")
            logger.info(f"  最终评分: {score_output.final_score:.1f}")
            logger.info(f"  交易信号: {score_output.signal}")

            return result

        except Exception as e:
            logger.error(f"❌ QuantCore 分析失败: {code}, 错误: {e}", exc_info=True)
            raise

    def _calculate_factors(self, df: pd.DataFrame, code: str) -> FactorOutput:
        """
        因子计算（适配旧接口）
        """
        # 调用旧引擎
        old_result = self.factor_engine.calculate(df)

        # 转换为新格式（暂时兼容，后续重构）
        date = datetime.now()

        # 构建 summary
        from core.quant_core.models import FactorSummary
        summary = FactorSummary(
            overall_score=old_result.get('summary', {}).get('overall_score', 50),
            trend_score=old_result.get('trend', {}).get('score', 50) if 'trend' in old_result else 50,
            momentum_score=old_result.get('momentum', {}).get('score', 50) if 'momentum' in old_result else 50,
            volume_score=old_result.get('volume', {}).get('score', 50) if 'volume' in old_result else 50,
            volatility_score=old_result.get('volatility', {}).get('score', 50) if 'volatility' in old_result else 50,
            strength_score=old_result.get('strength', {}).get('score', 50) if 'strength' in old_result else 50
        )

        # 暂时返回简化的 FactorOutput
        from core.quant_core.models import FactorItem
        factors = {}
        for name in ['trend', 'momentum', 'volume', 'volatility', 'strength']:
            if name in old_result:
                factors[name] = FactorItem(
                    name=name,
                    value=old_result[name].get('value', 0),
                    score=old_result[name].get('score', 50),
                    category=name,
                    description=old_result[name].get('description', '')
                )

        return FactorOutput(
            code=code,
            date=date,
            factors=factors,
            summary=summary,
            raw_data=old_result
        )

    def _generate_signals(self, df: pd.DataFrame, factor_output: FactorOutput, code: str) -> SignalOutput:
        """
        信号生成（适配旧接口）
        """
        # 调用旧引擎
        old_result = self.signal_engine.generate(df)

        # 转换为新格式
        date = datetime.now()

        from core.quant_core.models import SignalSummary, SignalItem
        summary = SignalSummary(
            overall_strength=old_result.get('summary', {}).get('overall_strength', 50),
            buy_signals=old_result.get('summary', {}).get('bullish_signals', 0),
            sell_signals=old_result.get('summary', {}).get('bearish_signals', 0),
            hold_signals=0,
            warning_signals=0,
            direction=old_result.get('summary', {}).get('overall_direction', 'neutral')
        )

        signals = {}
        for name in ['breakout', 'trend', 'reversal', 'volume']:
            if name in old_result and old_result[name]:
                signal_data = old_result[name]
                signals[name] = SignalItem(
                    name=name,
                    signal_type='buy' if signal_data.get('direction') == 'bullish' else 'sell',
                    strength=signal_data.get('strength', 50),
                    confidence=0.7,
                    description=signal_data.get('description', ''),
                    source=name
                )

        return SignalOutput(
            code=code,
            date=date,
            signals=signals,
            summary=summary,
            raw_data=old_result
        )

    def _detect_leader(self, df: pd.DataFrame, factors: FactorOutput, signals: SignalOutput, code: str) -> LeaderOutput:
        """
        龙头识别（适配旧接口）
        """
        # 调用旧引擎
        old_result = self.leader_engine.analyze(df)

        # 转换为新格式
        date = datetime.now()

        return LeaderOutput(
            code=code,
            date=date,
            is_leader=old_result.get('is_leader', False),
            leader_score=old_result.get('leader_score', 0),
            leader_type=old_result.get('leader_type', '普通'),
            sector_rank=0,
            peer_leaders=[],
            reason=old_result.get('reason', []),
            raw_data=old_result
        )

    def _get_market_state(self, date: Optional[datetime] = None) -> StateOutput:
        """
        获取市场状态（适配旧接口）
        """
        if date is None:
            date = datetime.now()

        # 获取最新快照
        try:
            snapshot = self.market_memory.get_latest_snapshot()
        except Exception:
            snapshot = None

        # 分析市场周期
        try:
            cycle_result = self.market_memory.analyze_market_cycle(days=7)
        except Exception:
            cycle_result = {}

        # 分析情绪趋势
        try:
            emotion_result = self.market_memory.analyze_emotion_trend(days=5)
        except Exception:
            emotion_result = {}

        # 构建 StateOutput
        return StateOutput(
            date=date,
            cycle=cycle_result.get('cycle', '未知'),
            cycle_stage=cycle_result.get('stage', '未知'),
            emotion_score=snapshot.emotion_score if hasattr(snapshot, 'emotion_score') else 50,
            emotion_trend=emotion_result.get('direction', '平稳'),
            limit_up_count=snapshot.limit_up_count if hasattr(snapshot, 'limit_up_count') else 0,
            limit_down_count=snapshot.limit_down_count if hasattr(snapshot, 'limit_down_count') else 0,
            rise_ratio=snapshot.rise_ratio if hasattr(snapshot, 'rise_ratio') else 0.5,
            total_volume=snapshot.total_volume if hasattr(snapshot, 'total_volume') else 0,
            north_money=snapshot.north_money if hasattr(snapshot, 'north_money') else 0,
            risk_level=snapshot.risk_level if hasattr(snapshot, 'risk_level') else '中',
            top_sectors=[] if not hasattr(snapshot, 'top_sectors') else snapshot.top_sectors if isinstance(snapshot.top_sectors, list) else [],
            hot_themes=[],
            sector_rotation=cycle_result.get('sector_rotation', {}),
            leader_rotation=cycle_result.get('leader_rotation', {}),
            raw_data={'snapshot': snapshot, 'cycle': cycle_result, 'emotion': emotion_result}
        )


_datahub_instance: Optional[QuantCore] = None


def get_quant_core() -> QuantCore:
    """
    获取 QuantCore 单例
    """
    global _datahub_instance
    if _datahub_instance is None:
        _datahub_instance = QuantCore()
    return _datahub_instance
