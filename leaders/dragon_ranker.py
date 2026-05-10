from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .leader_detector import LeaderDetector


class DragonRanker:
    def __init__(self):
        self.leader_detector = LeaderDetector()

    def rank_stocks(
        self,
        stock_data_list: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Dict[str, Any]:
        if not stock_data_list:
            return self._empty_result()

        leader_results = []
        for stock_data in stock_data_list:
            code = stock_data.get("code", "unknown")
            df = stock_data.get("df")
            factors = stock_data.get("factors")
            signals = stock_data.get("signals")

            if df is None or len(df) == 0:
                continue

            result = self.leader_detector.detect(df, factors, signals)
            result["code"] = code
            result["name"] = stock_data.get("name", code)
            leader_results.append(result)

        leader_results.sort(key=lambda x: x["leader_score"], reverse=True)

        top_leaders = leader_results[:top_n]

        leaders_only = [r for r in leader_results if r["is_leader"]]
        leaders_only.sort(key=lambda x: x["leader_score"], reverse=True)

        sector_analysis = self._analyze_sectors(top_leaders)

        return {
            "top_leaders": top_leaders,
            "all_leaders": leaders_only,
            "total_stocks": len(leader_results),
            "leader_count": len(leaders_only),
            "sector_analysis": sector_analysis,
        }

    def rank_single_stock(
        self,
        code: str,
        df: pd.DataFrame,
        factors: Dict[str, Any] = None,
        signals: Dict[str, Any] = None,
        name: str = None
    ) -> Dict[str, Any]:
        stock_data = {
            "code": code,
            "name": name or code,
            "df": df,
            "factors": factors,
            "signals": signals,
        }
        return self.leader_detector.detect(df, factors, signals)

    def _analyze_sectors(self, leaders: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not leaders:
            return {"sector_distribution": {}, "top_sectors": []}

        sector_map = {}
        for leader in leaders:
            leader_type = leader.get("leader_type", "普通")
            if leader_type not in ["普通", "潜力股"]:
                score = leader.get("leader_score", 0)
                sector_map[leader_type] = sector_map.get(leader_type, 0) + score

        sorted_sectors = sorted(sector_map.items(), key=lambda x: x[1], reverse=True)

        return {
            "sector_distribution": sector_map,
            "top_sectors": [{"type": s[0], "total_score": s[1]} for s in sorted_sectors[:5]],
        }

    def get_leader_summary(self, ranking_result: Dict[str, Any]) -> str:
        if not ranking_result or not ranking_result.get("top_leaders"):
            return "暂无龙头股"

        lines = []
        lines.append(f"共发现 {ranking_result['leader_count']} 只龙头/强势股")
        lines.append("")

        top = ranking_result["top_leaders"][:5]
        for i, leader in enumerate(top, 1):
            code = leader.get("code", "?")
            name = leader.get("name", code)
            score = leader.get("leader_score", 0)
            leader_type = leader.get("leader_type", "普通")
            limit_count = leader.get("metadata", {}).get("limit_up_count", 0)

            lines.append(f"{i}. {name}({code}) - {leader_type} 评分:{score}")
            if limit_count > 0:
                lines.append(f"   连续涨停: {limit_count}天")

        return "\n".join(lines)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "top_leaders": [],
            "all_leaders": [],
            "total_stocks": 0,
            "leader_count": 0,
            "sector_analysis": {"sector_distribution": {}, "top_sectors": []},
        }


def rank_leaders(stock_data_list: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
    ranker = DragonRanker()
    return ranker.rank_stocks(stock_data_list, top_n)
