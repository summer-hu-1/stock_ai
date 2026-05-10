from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class BaseLeader(ABC):
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def detect(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

    def get_required_columns(self) -> List[str]:
        return ["date", "open", "high", "low", "close", "volume", "price_change_pct", "turnover_rate"]

    def validate_data(self, df: pd.DataFrame) -> bool:
        if df is None or len(df) == 0:
            return False
        for col in self.get_required_columns():
            if col not in df.columns:
                return False
        return True

    def create_leader_result(
        self,
        is_leader: bool,
        leader_score: int,
        leader_type: str,
        reasons: List[str],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        return {
            "is_leader": is_leader,
            "leader_score": max(0, min(100, leader_score)),
            "leader_type": leader_type,
            "reason": reasons,
            "metadata": metadata or {},
        }

    def calc_percentile_rank(self, value: float, values: List[float]) -> int:
        if not values or len(values) == 0:
            return 50
        rank = sum(1 for v in values if v < value) / len(values) * 100
        return max(0, min(100, int(rank)))
