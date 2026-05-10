from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np


class BaseSignal(ABC):
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def generate(self, df: pd.DataFrame, factors: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

    def validate_data(self, df: pd.DataFrame, required_cols: List[str]) -> bool:
        for col in required_cols:
            if col not in df.columns:
                return False
        return len(df) > 0

    def get_required_columns(self) -> List[str]:
        return ["date", "open", "high", "low", "close", "volume"]

    def create_signal(
        self,
        signal_type: str,
        direction: str,
        strength: int,
        reasons: List[str],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        return {
            "signal": signal_type,
            "direction": direction,
            "strength": max(0, min(100, strength)),
            "reason": reasons,
            "metadata": metadata or {},
        }

    def calc_distance_percent(self, current: float, baseline: float) -> float:
        if baseline == 0 or np.isnan(baseline):
            return 0.0
        return float(((current - baseline) / baseline) * 100)
