from typing import Dict, Any, List, Optional
import pandas as pd
from .leader_detector import LeaderDetector
from .dragon_ranker import DragonRanker, rank_leaders
from .limitup_signal import LimitUpSignal
from .sector_leader import SectorLeader


class LeaderEngine:
    def __init__(self):
        self.leader_detector = LeaderDetector()
        self.dragon_ranker = DragonRanker()
        self.limitup_signal = LimitUpSignal()
        self.sector_leader = SectorLeader()

    def analyze(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        if df is None or len(df) == 0:
            return self._empty_result()

        leader_result = self.leader_detector.detect(df, factors, signals)
        limitup_result = self.limitup_signal.detect(df, factors, signals)

        combined_score = int(
            leader_result["leader_score"] * 0.6 +
            limitup_result["leader_score"] * 0.4
        )

        is_leader = leader_result["is_leader"] or limitup_result["is_leader"]

        if is_leader and limitup_result.get("metadata", {}).get("consecutive_limit_ups", 0) >= 2:
            combined_type = "龙头"
        elif is_leader:
            combined_type = leader_result.get("leader_type", "强势股")
        else:
            combined_type = "普通"

        combined_reasons = list(set(leader_result["reason"] + limitup_result["reason"]))

        return {
            "is_leader": is_leader,
            "leader_score": combined_score,
            "leader_type": combined_type,
            "reason": combined_reasons,
            "leader_detail": leader_result,
            "limitup_detail": limitup_result,
            "metadata": {
                **leader_result.get("metadata", {}),
                **limitup_result.get("metadata", {}),
            }
        }

    def rank(self, stock_data_list: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
        return self.dragon_ranker.rank_stocks(stock_data_list, top_n)

    def analyze_sector(self, sector_stocks: List[Dict[str, Any]], sector_name: str = "未知板块") -> Dict[str, Any]:
        return self.sector_leader.analyze_sector_leaders(sector_stocks, sector_name)

    def compare_sectors(self, sector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.sector_leader.compare_sectors(sector_results)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "is_leader": False,
            "leader_score": 0,
            "leader_type": "普通",
            "reason": [],
            "leader_detail": {},
            "limitup_detail": {},
            "metadata": {},
        }


def analyze_leader(df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
    engine = LeaderEngine()
    return engine.analyze(df, factors, signals)


def rank_leader_stocks(stock_data_list: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
    engine = LeaderEngine()
    return engine.rank(stock_data_list, top_n)
