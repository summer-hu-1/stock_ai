"""
市场状态分析引擎 - QuantCore

功能：
1. 识别市场状态：冰点、修复、主升、高潮、退潮
2. 龙头股检测与分析
3. 连板信号识别

迁移自旧 leaders/ 系统
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class StateEngine:
    """
    市场状态分析引擎

    基于量价关系识别市场状态和龙头股
    """

    STATES = ["iceberg", "recovery", "rally", "high", "retreat"]

    def __init__(self):
        self.leader_detector = LeaderFeatureDetector()

    def analyze(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分析市场状态

        Args:
            df: K线数据
            factors: 因子数据（可选）
            signals: 信号数据（可选）

        Returns:
            Dict: 市场状态和龙头分析结果
        """
        if df is None or df.empty or len(df) < 20:
            return self._default_state()

        state = self._identify_state(df)
        description = self._get_state_description(state)
        sentiment = self._calculate_sentiment(df)
        
        leader_result = self.leader_detector.detect(df, factors, signals)

        return {
            "state": state,
            "description": description,
            "sentiment": sentiment,
            "volatility": self._calculate_volatility(df),
            **leader_result,
        }

    def rank_stocks(
        self,
        stock_data_list: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        对股票进行龙头排名

        Args:
            stock_data_list: 股票数据列表
            top_n: 返回前N名

        Returns:
            Dict: 排名结果
        """
        if not stock_data_list:
            return self._empty_rank_result()

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

    def _default_state(self) -> Dict[str, Any]:
        """默认状态"""
        return {
            "state": "unknown",
            "description": "数据不足",
            "sentiment": 0.5,
            "volatility": 0,
            "is_leader": False,
            "leader_score": 0,
            "leader_type": "普通",
            "leader_reasons": [],
            "limit_up_info": {},
        }

    def _empty_rank_result(self) -> Dict[str, Any]:
        return {
            "top_leaders": [],
            "all_leaders": [],
            "total_stocks": 0,
            "leader_count": 0,
            "sector_analysis": {"sector_distribution": {}, "top_sectors": []},
        }

    def _identify_state(self, df: pd.DataFrame) -> str:
        """识别市场状态"""
        closes = df["close"].values
        volumes = df["volume"].values if "volume" in df.columns else np.ones(len(df))

        if len(df) < 20:
            return "unknown"

        price_change = (closes[-1] - closes[-20]) / closes[-20] if closes[-20] != 0 else 0
        vol_change = (np.mean(volumes[-5:]) - np.mean(volumes[-20:-5])) / np.mean(volumes[-20:-5]) if np.mean(volumes[-20:-5]) != 0 else 0

        if price_change > 0.15 and vol_change > 1.0:
            return "high"
        elif price_change > 0.1 and vol_change > 0.5:
            return "rally"
        elif price_change > 0.05 and vol_change > 0.2:
            return "recovery"
        elif price_change < -0.1:
            return "retreat"
        elif vol_change < -0.3 and price_change < 0.02:
            return "iceberg"

        return "sideways"

    def _get_state_description(self, state: str) -> str:
        """获取状态描述"""
        descriptions = {
            "rally": "主升阶段，趋势明确，可积极做多",
            "recovery": "修复阶段，震荡向上，可逢低布局",
            "high": "高潮阶段，注意高位风险",
            "retreat": "退潮阶段，控制仓位或空仓",
            "iceberg": "冰点阶段，市场清淡，等待机会",
            "sideways": "震荡阶段，方向不明",
            "unknown": "状态未知",
        }
        return descriptions.get(state, "状态未知")

    def _calculate_sentiment(self, df: pd.DataFrame) -> float:
        """计算情绪评分"""
        if len(df) < 5:
            return 0.5

        closes = df["close"].values
        returns = np.diff(closes) / closes[:-1]

        if len(returns) < 5:
            return 0.5

        avg_return = np.mean(returns[-5:])
        positive_ratio = np.sum(returns[-5:] > 0) / 5

        sentiment = 0.5 + avg_return * 10 + (positive_ratio - 0.5) * 0.3
        return float(np.clip(sentiment, 0, 1))

    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """计算波动率"""
        if len(df) < 20 or "close" not in df.columns:
            return 0

        closes = df["close"].values
        returns = np.diff(closes) / closes[:-1]

        return float(np.std(returns[-20:]))

    def _analyze_sectors(self, leaders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析板块分布"""
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


class LeaderFeatureDetector:
    """
    龙头特征检测器

    检测股票是否具备龙头股特征
    """

    def detect(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        检测龙头特征

        Args:
            df: K线数据
            factors: 因子数据
            signals: 信号数据

        Returns:
            Dict: 龙头检测结果
        """
        if df is None or len(df) == 0:
            return self._empty_result()

        leader_det_result = self._detect_leader_features(df, factors, signals)
        limitup_result = self._detect_limit_up(df, factors, signals)

        combined_score = int(
            leader_det_result["leader_score"] * 0.6 +
            limitup_result["leader_score"] * 0.4
        )

        is_leader = leader_det_result["is_leader"] or limitup_result["is_leader"]
        consecutive_limit_ups = limitup_result.get("metadata", {}).get("consecutive_limit_ups", 0)

        if is_leader and consecutive_limit_ups >= 2:
            combined_type = "龙头"
        elif is_leader:
            combined_type = leader_det_result.get("leader_type", "强势股")
        else:
            combined_type = "普通"

        combined_reasons = list(set(leader_det_result["reasons"] + limitup_result["reasons"]))

        return {
            "is_leader": is_leader,
            "leader_score": combined_score,
            "leader_type": combined_type,
            "leader_reasons": combined_reasons,
            "limit_up_info": {
                "count": consecutive_limit_ups,
                "recent_limit_up": limitup_result.get("recent_limit_up", False),
                "limit_up_ratio": limitup_result.get("limit_up_ratio", 0),
            },
            "metadata": {
                **leader_det_result.get("metadata", {}),
                **limitup_result.get("metadata", {}),
            }
        }

    def _detect_leader_features(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测龙头特征"""
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        reasons = []
        score = 0
        is_leader = False
        leader_type = "普通"

        current_close = float(close.iloc[-1])
        avg_price = float(close.mean())

        if current_close > avg_price * 1.3:
            score += 20
            reasons.append("近期涨幅显著")
            leader_type = "强势股"

        if len(close) >= 10:
            recent_returns = close.pct_change().dropna()
            if len(recent_returns) >= 5:
                avg_return = float(recent_returns.iloc[-5:].mean())
                if avg_return > 0.03:
                    score += 15
                    reasons.append("连续上涨")

        current_vol = float(volume.iloc[-1])
        vol_ma5 = float(volume.iloc[-5:].mean()) if len(volume) >= 5 else current_vol
        vol_ratio = current_vol / vol_ma5 if vol_ma5 > 0 else 1.0

        if vol_ratio > 2.0:
            score += 15
            reasons.append("成交量暴增")

        if factors:
            momentum = factors.get("momentum", {})
            if momentum.get("score", 50) > 70:
                score += 10
                reasons.append("动量强劲")

            strength = factors.get("strength", {})
            if strength.get("score", 50) > 70:
                score += 10
                reasons.append("强度较高")

        if signals:
            breakout = signals.get("breakout", {})
            if breakout.get("direction") == "bullish" and breakout.get("strength", 0) > 70:
                score += 15
                reasons.append("突破信号")

            trend = signals.get("trend", {})
            if trend.get("direction") == "bullish" and trend.get("strength", 0) > 60:
                score += 10
                reasons.append("趋势向上")

        if score >= 60:
            is_leader = True
            if score >= 80:
                leader_type = "核心龙头"
            elif score >= 70:
                leader_type = "强势龙头"

        return {
            "is_leader": is_leader,
            "leader_score": min(100, score),
            "leader_type": leader_type,
            "reasons": reasons,
            "metadata": {"vol_ratio": vol_ratio},
        }

    def _detect_limit_up(self, df: pd.DataFrame, factors: Dict[str, Any] = None, signals: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测涨停信号"""
        close = df["close"].astype(float)
        open_price = df["open"].astype(float) if "open" in df.columns else close
        high = df["high"].astype(float) if "high" in df.columns else close

        reasons = []
        score = 0
        is_leader = False
        consecutive_limit_ups = 0
        recent_limit_up = False

        limit_up_ratio = 0.098

        for i in range(min(5, len(df))):
            idx = -(i + 1)
            if i >= len(df):
                break

            close_p = float(close.iloc[idx])
            open_p = float(open_price.iloc[idx])

            if open_p > 0:
                change = (close_p - open_p) / open_p
                if change >= limit_up_ratio * 0.95:
                    consecutive_limit_ups += 1
                    if i == 0:
                        recent_limit_up = True
                else:
                    break

        if consecutive_limit_ups >= 1:
            score += consecutive_limit_ups * 25
            reasons.append(f"连续{consecutive_limit_ups}天涨停")
            is_leader = True

        if len(close) >= 5:
            recent_max_high = float(high.iloc[-5:].max())
            if float(close.iloc[-1]) >= recent_max_high * 0.99:
                score += 10
                reasons.append("逼近近期高点")

        return {
            "is_leader": is_leader,
            "leader_score": min(100, score),
            "leader_type": "连板股",
            "reasons": reasons,
            "recent_limit_up": recent_limit_up,
            "limit_up_ratio": limit_up_ratio,
            "metadata": {"consecutive_limit_ups": consecutive_limit_ups},
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "is_leader": False,
            "leader_score": 0,
            "leader_type": "普通",
            "reasons": [],
            "metadata": {},
        }
