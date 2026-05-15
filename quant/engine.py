"""
量化核心引擎 - QuantCore

V10 架构核心：统一量化计算引擎
"""

from typing import Optional, Dict, Any
import pandas as pd
import logging
from .models import QuantResult

logger = logging.getLogger(__name__)


class QuantCore:
    """
    QuantCore - 量化核心引擎

    唯一计算入口，所有量化计算必须通过此引擎
    """

    def __init__(self):
        self._factor_engine = None
        self._signal_engine = None
        self._state_engine = None
        self._score_engine = None

    def analyze(self, code: str, market: str = "cn") -> Optional[QuantResult]:
        """
        综合量化分析

        Args:
            code: 股票代码
            market: 市场代码

        Returns:
            QuantResult: 量化分析结果对象
        """
        from data import get_datahub

        datahub = get_datahub()
        df = datahub.get_ohlcv_dataframe(code, market)

        if df is None or df.empty:
            logger.warning(f"无法获取数据: {code}")
            return None

        factors = self.calculate_factors(df)
        signals = self.generate_signals(df)
        state = self.analyze_market_state(df)
        score = self.calculate_score(df)

        return QuantResult(
            code=code,
            market=market,
            factors=factors,
            signals=signals,
            state=state,
            score=score
        )

    def calculate_factors(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        计算因子

        Args:
            df: K线数据

        Returns:
            Dict: 因子字典
        """
        if self._factor_engine is None:
            from .factor.engine import FactorEngine
            self._factor_engine = FactorEngine()

        return self._factor_engine.calculate(df)

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成信号

        Args:
            df: K线数据

        Returns:
            Dict: 信号结果
        """
        if self._signal_engine is None:
            from .signal.engine import SignalEngine
            self._signal_engine = SignalEngine()

        return self._signal_engine.generate(df)

    def analyze_market_state(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场状态

        Args:
            df: K线数据

        Returns:
            Dict: 市场状态
        """
        if self._state_engine is None:
            from .state.engine import StateEngine
            self._state_engine = StateEngine()

        return self._state_engine.analyze(df)

    def calculate_score(self, df: pd.DataFrame) -> float:
        """
        计算综合评分

        Args:
            df: K线数据

        Returns:
            float: 0-1评分
        """
        if self._score_engine is None:
            from .score.engine import ScoreEngine
            self._score_engine = ScoreEngine()

        return self._score_engine.calculate(df)


_quant_core_instance: Optional[QuantCore] = None


def get_quant_core() -> QuantCore:
    """获取QuantCore单例"""
    global _quant_core_instance
    if _quant_core_instance is None:
        _quant_core_instance = QuantCore()
    return _quant_core_instance
