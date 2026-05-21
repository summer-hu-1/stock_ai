"""
今日进攻引擎 - AttackOpportunityEngine
综合多因子扫描全市场，识别今日最值得进攻的目标池 TOP5

输入：
- 本地 CSV 日线数据（data/cn/daily/）
- 市场情绪引擎数据
- 个股短线状态引擎

输出：
- TOP5 进攻目标卡（code, name, score, state, theme, risk, reasons, script）

权重体系：
- 趋势强度 25%
- 量能爆发 20%
- 龙头/突破信号 20%
- 短线状态 15%
- 市场情绪适配 20%
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class AttackOpportunityEngine:
    """今日进攻目标池扫描引擎"""

    def __init__(self, data_dir: str = None, max_stocks: int = 500):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cn', 'daily')
        self.data_dir = data_dir
        self.max_stocks = max_stocks

    # ============================================================
    # 核心：扫描 + 评分 + 排序
    # ============================================================
    def scan(self, market_emotion: Dict = None) -> List[Dict]:
        """
        扫描全市场，返回 TOP5 进攻目标

        Args:
            market_emotion: 市场情绪分析结果（来自 market_engine.run_market_emotion_analysis()）

        Returns:
            [{"code": str, "name": str, "score": int, "state": str, "state_cn": str,
              "theme": str, "risk": str, "reasons": [str], "script_bull": str, "script_bear": str,
              "change_pct": float, "volume": float}, ...]
        """
        cycle = market_emotion.get("cycle", "") if market_emotion else ""
        market_risk = self._market_risk_level(market_emotion)

        # 1. 获取所有本地股票文件
        stock_files = self._get_stock_files()
        if not stock_files:
            return []

        # 2. 逐个分析并评分
        candidates = []
        for sf in stock_files[:self.max_stocks]:
            try:
                df = pd.read_csv(sf["path"])
                if df is None or df.empty or len(df) < 10:
                    continue

                score_data = self._score_stock(df, sf["name"], sf["code"], cycle, market_risk)
                if score_data["score"] >= 40:  # 最低门槛
                    candidates.append(score_data)
            except Exception:
                continue

        # 3. 按评分降序，取 TOP5
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:5]

    # ============================================================
    # 个股评分
    # ============================================================
    def _score_stock(self, df: pd.DataFrame, name: str, code: str,
                     market_cycle: str, market_risk: str) -> Dict:
        """对单只股票综合评分"""
        closes = df["close"].values
        volumes = df["volume"].values
        pcts = df["price_change_pct"].values if "price_change_pct" in df.columns else np.zeros(len(closes))
        highs = df["high"].values
        lows = df["low"].values

        if len(closes) < 10:
            return {"score": 0}

        # --- 基础指标 ---
        latest_close = closes[-1]
        latest_volume = volumes[-1]
        latest_pct = pcts[-1] if len(pcts) > 0 else 0

        # --- 趋势得分 (25%) ---
        ma5 = np.mean(closes[-5:])
        ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        trend_5d = (closes[-1] - closes[-5]) / closes[-5] * 100 if closes[-5] != 0 else 0
        above_ma5 = latest_close > ma5
        above_ma20 = latest_close > ma20

        trend_score = 0
        if trend_5d > 10:
            trend_score = 90
        elif trend_5d > 5:
            trend_score = 75
        elif trend_5d > 2:
            trend_score = 60
        elif trend_5d > 0:
            trend_score = 45
        else:
            trend_score = max(10, 50 + trend_5d)

        if above_ma5:
            trend_score += 10
        if above_ma20:
            trend_score += 5
        trend_score = min(100, trend_score)

        # --- 量能得分 (20%) ---
        vol_ma5 = np.mean(volumes[-6:-1]) if len(volumes) >= 6 else np.mean(volumes[:-1])
        vol_ratio = latest_volume / vol_ma5 if vol_ma5 > 0 else 1
        vol_increasing = volumes[-1] > volumes[-2] > volumes[-3] if len(volumes) >= 3 else False

        volume_score = min(100, int(vol_ratio * 70))
        if vol_increasing:
            volume_score += 15
        if vol_ratio > 2:
            volume_score += 15
        volume_score = min(100, volume_score)

        # --- 短线状态得分 (15%) ---
        daily_5 = []
        for i in range(max(0, len(closes)-5), len(closes)):
            daily_5.append({
                "close": float(closes[i]),
                "volume": float(volumes[i]),
                "pct_chg": float(pcts[i]) if i < len(pcts) else 0,
                "high": float(highs[i]),
                "low": float(lows[i]),
            })

        from engines.structure_engine.short_term_state import get_short_term_state
        state = get_short_term_state(daily_5) if len(daily_5) >= 3 else {"strength": 50, "risk": "medium", "state_key": "unknown", "state_cn": "未知", "score_components": {}}

        # 状态 → 得分映射
        state_score_map = {
            "acceleration": 95, "breakout": 85, "reversal_reclaim": 75,
            "trend_follow": 65, "consolidation": 40,
            "panic_distribution": 10, "decay": 5
        }
        state_score = state_score_map.get(state.get("state_key", ""), 40)

        # --- 龙头/信号得分 (20%) ---
        signal_score = self._calc_signal_score(latest_pct, latest_volume, vol_ratio, trend_5d, highs, lows)

        # --- 市场环境适配 (20%) ---
        env_score = self._calc_env_score(market_cycle, market_risk, latest_pct, state.get("state_key", ""))

        # --- 综合评分 ---
        total_score = int(
            trend_score * 0.25 +
            volume_score * 0.20 +
            state_score * 0.15 +
            signal_score * 0.20 +
            env_score * 0.20
        )

        # --- 主线识别 ---
        theme = self._identify_theme(name, code, latest_pct)

        # --- 进攻理由 ---
        reasons = self._build_reasons(trend_5d, vol_ratio, state, latest_pct, market_cycle)

        # --- 剧本 ---
        script_bull = state.get("scenario_bullish", "趋势延续则可关注。")
        script_bear = state.get("scenario_bearish", "趋势破位则回避。")

        state_risk = state.get("risk", "medium")

        return {
            "code": code,
            "name": name,
            "score": total_score,
            "state_key": state.get("state_key", ""),
            "state_cn": state.get("state_cn", "未知"),
            "strength": state.get("strength", 50),
            "theme": theme,
            "risk": state_risk,
            "reasons": reasons,
            "script_bull": script_bull,
            "script_bear": script_bear,
            "change_pct": round(float(latest_pct), 2),
            "volume": float(latest_volume),
        }

    # ============================================================
    # 辅助评分
    # ============================================================
    def _calc_signal_score(self, pct, vol, vol_ratio, trend_5d, highs, lows) -> int:
        """基于价格行为的信号评分"""
        score = 50

        # 涨幅贡献
        if pct > 9.5:
            score += 35    # 涨停封板
        elif pct > 7:
            score += 25
        elif pct > 5:
            score += 15
        elif pct > 2:
            score += 8
        elif pct < -5:
            score -= 30
        elif pct < -2:
            score -= 15

        # 量能信号
        if vol_ratio > 3:
            score += 15
        elif vol_ratio > 2:
            score += 10

        # 高低点信号
        if len(highs) >= 3 and len(lows) >= 3:
            # 创5日新高
            if highs[-1] > max(highs[-6:-1]) if len(highs) > 5 else highs[-1] > highs[-2]:
                score += 10
            # 锤子线（长下影）
            body = abs(pct / 100 * highs[-1]) if highs[-1] != 0 else 0
            if (lows[-1] - lows[-2]) / lows[-2] < -0.03 and highs[-1] < highs[-2]:
                score -= 10

        return max(0, min(100, score))

    def _calc_env_score(self, cycle: str, risk: str, pct: float, state_key: str) -> int:
        """市场环境适配得分"""
        score = 50

        # 周期适配
        cycle_multiplier = {
            "主升期": 1.3, "发酵期": 1.2, "修复期": 1.1,
            "试错期": 1.0, "分歧期": 0.7, "退潮期": 0.4,
            "冰点期": 0.3, "高潮期": 0.8, "": 1.0
        }
        score = int(score * cycle_multiplier.get(cycle, 1.0))

        # 风险等级扣分
        if risk == "high":
            score -= 30
        elif risk == "medium":
            score -= 10

        # 退潮/恐慌状态不进攻
        if state_key in ("panic_distribution", "decay"):
            score -= 40

        return max(0, min(100, score))

    def _identify_theme(self, name: str, code: str, pct: float) -> str:
        """简易主线识别（基于股票名称和代码段）"""
        # AI / 科技
        ai_keywords = ["智能", "数据", "软件", "信息", "科技", "通信", "电子", "芯片", "半导体",
                       "计算机", "网络", "云", "数字", "AI", "算力", "大模型"]
        for kw in ai_keywords:
            if kw in name:
                return "AI / 科技"

        # 机器人 / 制造
        robot_kw = ["机器人", "机械", "设备", "精密", "制造", "机床", "电机"]
        for kw in robot_kw:
            if kw in name:
                return "机器人 / 制造"

        # 新能源
        energy_kw = ["能源", "电池", "光伏", "锂", "电力", "风电", "储能", "新能源"]
        for kw in energy_kw:
            if kw in name:
                return "新能源"

        # 消费
        consume_kw = ["食品", "饮料", "医药", "医疗", "家", "酒", "药", "消费"]
        for kw in consume_kw:
            if kw in name:
                return "消费 / 医药"

        # 涨停股 → 情绪核心
        if pct > 9.5:
            return "情绪核心"

        return "通用"

    def _build_reasons(self, trend_5d: float, vol_ratio: float, state: Dict,
                       pct: float, cycle: str) -> List[str]:
        """生成进攻理由"""
        reasons = []
        sc = state.get("score_components", {})

        if trend_5d > 5:
            reasons.append(f"5日涨幅 {trend_5d:.1f}%，趋势强劲")
        elif trend_5d > 0:
            reasons.append(f"5日涨幅 {trend_5d:.1f}%，稳步上行")

        if vol_ratio > 2:
            reasons.append(f"量比 {vol_ratio:.1f}x，放量突破")
        elif vol_ratio > 1.5:
            reasons.append(f"量比 {vol_ratio:.1f}x，量能放大")

        state_cn = state.get("state_cn", "")
        if state_cn in ["🚀 强势主升", "📈 平台突破", "🔄 弱转强"]:
            reasons.append(f"短线状态：{state_cn}")

        if sc.get("volume_score", 0) > 75:
            reasons.append("量能评分优秀")

        if pct > 9.5:
            reasons.append("涨停封板，资金认可度高")
        elif pct > 5:
            reasons.append("涨幅居前，板块龙头")

        if cycle in ("主升期", "发酵期"):
            reasons.append(f"市场处于{cycle}，进攻窗口")

        # 确保至少2条理由
        if len(reasons) < 2:
            reasons.append("综合评分进入进攻池")

        return reasons[:4]  # 最多4条

    def _market_risk_level(self, emotion: Dict = None) -> str:
        """从市场情绪数据提取风险等级"""
        if not emotion:
            return "medium"
        danger_signals = emotion.get("danger_signals", [])
        if not danger_signals:
            return "low"
        severities = [s.get("严重程度", "") for s in danger_signals]
        if "高" in severities:
            return "high"
        if len(danger_signals) >= 3:
            return "high"
        if len(danger_signals) >= 2:
            return "medium"
        return "low"

    # ============================================================
    # 数据加载
    # ============================================================
    def _get_stock_files(self) -> List[Dict]:
        """获取所有本地 CSV 文件路径"""
        files = []
        if not os.path.exists(self.data_dir):
            return files

        # 加载名称映射
        code_name_map = {}
        try:
            from modules.storage import get_all_companies
            companies = get_all_companies()
            if companies:
                code_name_map = {c["code"]: c["name"] for c in companies}
        except Exception:
            pass

        for market_dir in sorted(os.listdir(self.data_dir)):
            market_path = os.path.join(self.data_dir, market_dir)
            if not os.path.isdir(market_path):
                continue
            for f in sorted(os.listdir(market_path)):
                if f.endswith('.csv'):
                    code = f.replace('.csv', '')
                    name = code_name_map.get(code, code)
                    files.append({
                        "code": code,
                        "name": name,
                        "path": os.path.join(market_path, f)
                    })

        # 按最新成交量排序，优先扫描活跃股
        return sorted(files, key=lambda x: x["code"])


def scan_attack_opportunities(market_emotion: Dict = None) -> List[Dict]:
    """快捷函数"""
    engine = AttackOpportunityEngine()
    return engine.scan(market_emotion)


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    results = scan_attack_opportunities()
    import json
    print(f"扫描到 {len(results)} 个目标")
    for r in results:
        print(f"\n{r['score']}分 | {r['name']}({r['code']}) | {r['state_cn']} | {r['theme']} | 风险:{r['risk']}")
        print(f"理由: {'; '.join(r['reasons'])}")
        print(f"✅ {r['script_bull']}")
        print(f"⚠️ {r['script_bear']}")