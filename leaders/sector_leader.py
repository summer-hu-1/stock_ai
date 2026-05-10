from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .leader_detector import LeaderDetector


class SectorLeader:
    def __init__(self):
        self.leader_detector = LeaderDetector()

    def analyze_sector_leaders(
        self,
        sector_stocks: List[Dict[str, Any]],
        sector_name: str = "未知板块"
    ) -> Dict[str, Any]:
        if not sector_stocks:
            return self._empty_result()

        leader_scores = []
        total_change = 0
        total_volume = 0

        for stock in sector_stocks:
            df = stock.get("df")
            factors = stock.get("factors")
            signals = stock.get("signals")
            code = stock.get("code", "unknown")
            name = stock.get("name", code)

            if df is None or len(df) == 0:
                continue

            result = self.leader_detector.detect(df, factors, signals)
            result["code"] = code
            result["name"] = name

            leader_scores.append(result)

            if len(df) > 0:
                total_change += float(df["price_change_pct"].iloc[-1]) if "price_change_pct" in df.columns else 0
                total_volume += float(df["volume"].iloc[-1]) if "volume" in df.columns else 0

        leader_scores.sort(key=lambda x: x["leader_score"], reverse=True)

        top_leader = leader_scores[0] if leader_scores else None
        sector_strength = self._calc_sector_strength(leader_scores)
        sector_momentum = total_change / len(sector_stocks) if sector_stocks else 0

        leaders_in_sector = [s for s in leader_scores if s["is_leader"]]

        return {
            "sector_name": sector_name,
            "sector_strength": sector_strength,
            "sector_momentum": round(sector_momentum, 2),
            "top_leader": top_leader,
            "all_leaders": leader_scores,
            "leader_count": len(leaders_in_sector),
            "total_stocks": len(sector_stocks),
            "total_volume": total_volume,
        }

    def compare_sectors(
        self,
        sector_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not sector_results:
            return []

        for result in sector_results:
            result["rank_score"] = (
                result.get("sector_strength", 0) * 0.4 +
                max(0, result.get("sector_momentum", 0)) * 3 +
                result.get("leader_count", 0) * 10
            )

        sector_results.sort(key=lambda x: x["rank_score"], reverse=True)

        for i, result in enumerate(sector_results):
            result["rank"] = i + 1

        return sector_results

    def _calc_sector_strength(self, leader_scores: List[Dict[str, Any]]) -> int:
        if not leader_scores:
            return 0

        total_score = sum(s.get("leader_score", 0) for s in leader_scores)
        leader_count = len([s for s in leader_scores if s.get("is_leader", False)])

        base_strength = total_score / len(leader_scores)
        leader_bonus = min(20, leader_count * 5)

        return max(0, min(100, int(base_strength + leader_bonus)))

    def get_sector_summary(self, sector_result: Dict[str, Any]) -> str:
        if not sector_result:
            return "板块数据不足"

        sector_name = sector_result.get("sector_name", "未知板块")
        strength = sector_result.get("sector_strength", 0)
        momentum = sector_result.get("sector_momentum", 0)
        leader_count = sector_result.get("leader_count", 0)

        lines = [
            f"板块: {sector_name}",
            f"强度评分: {strength}",
            f"板块涨幅: {momentum}%",
            f"龙头数量: {leader_count}",
        ]

        top = sector_result.get("top_leader")
        if top:
            lines.append(f"领涨股: {top.get('name', '?')}({top.get('code', '?')}) 评分:{top.get('leader_score', 0)}")

        return "\n".join(lines)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "sector_name": "未知板块",
            "sector_strength": 0,
            "sector_momentum": 0,
            "top_leader": None,
            "all_leaders": [],
            "leader_count": 0,
            "total_stocks": 0,
            "total_volume": 0,
        }
