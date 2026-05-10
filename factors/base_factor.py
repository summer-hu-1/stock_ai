from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class BaseFactor(ABC):
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        pass

    def validate_data(self, df: pd.DataFrame, required_cols: list) -> bool:
        for col in required_cols:
            if col not in df.columns:
                return False
        return len(df) > 0

    def get_required_columns(self) -> list:
        return ["date", "open", "high", "low", "close", "volume"]

    def safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        if denominator == 0 or np.isnan(denominator):
            return default
        return numerator / denominator

    def safe_percentile(self, series: pd.Series, percentile: float, default: float = 0.0) -> float:
        if len(series) == 0:
            return default
        result = np.percentile(series, percentile)
        if np.isnan(result):
            return default
        return float(result)

    def calculate_returns(self, close: pd.Series, periods: list) -> Dict[str, float]:
        returns = {}
        for period in periods:
            if len(close) >= period:
                ret = (close.iloc[-1] / close.iloc[-period] - 1) * 100
                returns[f"return_{period}d"] = float(ret) if not np.isnan(ret) else 0.0
            else:
                returns[f"return_{period}d"] = 0.0
        return returns

    def calculate_ma(self, close: pd.Series, period: int) -> Optional[float]:
        if len(close) < period:
            return None
        ma = close.iloc[-period:].mean()
        return float(ma) if not np.isnan(ma) else None

    def calculate_distance_percent(self, value: float, baseline: float) -> float:
        if baseline == 0 or np.isnan(baseline):
            return 0.0
        return float(((value - baseline) / baseline) * 100)
