from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import MarketState


class MemoryAdapter:
    def __init__(self):
        self._memory = None
        self._engine = None

    def _get_memory(self):
        if self._memory is None:
            try:
                from core.market_memory import MarketMemory
                self._memory = MarketMemory()
            except Exception as e:
                print(f"初始化 MarketMemory 失败: {e}")
                self._memory = None
        return self._memory

    def _get_engine(self):
        if self._engine is None:
            try:
                from core.market_memory.engine import MarketStateEngine
                self._engine = MarketStateEngine()
            except Exception as e:
                print(f"初始化 MarketStateEngine 失败: {e}")
                self._engine = None
        return self._engine

    def get_market_state(self, date: datetime) -> Optional[MarketState]:
        memory = self._get_memory()
        if memory is None:
            return self._create_default_state(date)

        try:
            snapshot = memory.get_latest_snapshot()
            if snapshot is None:
                return self._create_default_state(date)

            return MarketState(
                date=snapshot.date if hasattr(snapshot, 'date') else datetime.now(),
                cycle=snapshot.market_cycle if hasattr(snapshot, 'market_cycle') else "未知",
                cycle_stage=snapshot.cycle_stage if hasattr(snapshot, 'cycle_stage') else "未知",
                emotion_score=snapshot.emotion_score if hasattr(snapshot, 'emotion_score') else 50,
                emotion_trend="平稳",
                limit_up_count=snapshot.limit_up_count if hasattr(snapshot, 'limit_up_count') else 0,
                limit_down_count=snapshot.limit_down_count if hasattr(snapshot, 'limit_down_count') else 0,
                rise_ratio=snapshot.rise_ratio if hasattr(snapshot, 'rise_ratio') else 0,
                total_volume=snapshot.total_volume if hasattr(snapshot, 'total_volume') else 0,
                north_money=snapshot.north_money if hasattr(snapshot, 'north_money') else 0,
                risk_level=snapshot.risk_level if hasattr(snapshot, 'risk_level') else "中",
                top_sectors=self._parse_json_list(snapshot.top_sectors) if hasattr(snapshot, 'top_sectors') else [],
                hot_themes=self._parse_json_list(snapshot.hot_theme) if hasattr(snapshot, 'hot_theme') else []
            )
        except Exception as e:
            print(f"获取市场状态失败: {e}")
            return self._create_default_state(date)

    def get_market_state_history(self, days: int = 30) -> List[MarketState]:
        memory = self._get_memory()
        if memory is None:
            return []

        try:
            snapshots = memory.get_recent_snapshots(days)
            return [
                MarketState(
                    date=s.date if hasattr(s, 'date') else datetime.now(),
                    cycle=s.market_cycle if hasattr(s, 'market_cycle') else "未知",
                    cycle_stage=s.cycle_stage if hasattr(s, 'cycle_stage') else "未知",
                    emotion_score=s.emotion_score if hasattr(s, 'emotion_score') else 50,
                    emotion_trend="平稳",
                    limit_up_count=s.limit_up_count if hasattr(s, 'limit_up_count') else 0,
                    limit_down_count=s.limit_down_count if hasattr(s, 'limit_down_count') else 0,
                    rise_ratio=s.rise_ratio if hasattr(s, 'rise_ratio') else 0,
                    total_volume=s.total_volume if hasattr(s, 'total_volume') else 0,
                    north_money=s.north_money if hasattr(s, 'north_money') else 0,
                    risk_level=s.risk_level if hasattr(s, 'risk_level') else "中",
                    top_sectors=self._parse_json_list(s.top_sectors) if hasattr(s, 'top_sectors') else [],
                    hot_themes=self._parse_json_list(s.hot_theme) if hasattr(s, 'hot_theme') else []
                )
                for s in snapshots
            ]
        except Exception as e:
            print(f"获取市场状态历史失败: {e}")
            return []

    def analyze_market_cycle(self, days: int = 7) -> Dict[str, Any]:
        engine = self._get_engine()
        memory = self._get_memory()

        if engine is None or memory is None:
            return {"cycle": "未知", "stage": "未知", "description": "数据不足"}

        try:
            snapshots = memory.get_recent_snapshots(days)
            return engine.analyze_market_cycle(snapshots)
        except Exception as e:
            print(f"分析市场周期失败: {e}")
            return {"cycle": "未知", "stage": "未知", "description": f"分析失败: {e}"}

    def analyze_emotion_trend(self, days: int = 5) -> Dict[str, Any]:
        engine = self._get_engine()
        memory = self._get_memory()

        if engine is None or memory is None:
            return {"direction": "平稳", "description": "数据不足"}

        try:
            snapshots = memory.get_recent_snapshots(days)
            return engine.analyze_emotion_trend(snapshots, days)
        except Exception as e:
            print(f"分析情绪趋势失败: {e}")
            return {"direction": "平稳", "description": f"分析失败: {e}"}

    def _parse_json_list(self, json_str: str) -> List[str]:
        if not json_str:
            return []
        if isinstance(json_str, list):
            return json_str
        try:
            import json
            return json.loads(json_str)
        except Exception:
            return []

    def _create_default_state(self, date: datetime) -> MarketState:
        return MarketState(
            date=date,
            cycle="未知",
            cycle_stage="未知",
            emotion_score=50,
            emotion_trend="平稳",
            limit_up_count=0,
            limit_down_count=0,
            rise_ratio=0,
            total_volume=0,
            north_money=0,
            risk_level="中",
            top_sectors=[],
            hot_themes=[]
        )