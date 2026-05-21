"""
短线状态引擎 - ShortTermStateEngine
统一市场行为语义、规则化状态判定、剧本模板化、得分组件

输入：最近5日数据 [{close, volume, pct_chg, high, low}, ...]
输出：统一短线状态结构（state_cn, narrative, score_components, scenario）
"""

from typing import Dict, List, Tuple

# ============================================================
# 市场行为统一命名表
# ============================================================
STATE_MAPPING = {
    "acceleration":      "🚀 强势主升",
    "breakout":          "📈 平台突破",
    "reversal_reclaim":  "🔄 弱转强",
    "panic_distribution":"🆘 恐慌抛售",
    "decay":             "📉 缩量阴跌",
    "trend_follow":      "📈 趋势上行",
    "consolidation":     "⏸️ 横盘整理"
}

# ============================================================
# 剧本模板（杜绝 AI 胡编，所有输出基于规则）
# ============================================================
SCENARIO_TEMPLATES = {
    "acceleration": {
        "bullish": "若明日高开高走且半小时成交量＞今日50%，则主升延续。",
        "bearish": "若冲高回落收长上影，则分歧加大，减仓观察。"
    },
    "breakout": {
        "bullish": "明日站稳今日收盘价上方，则突破有效，可关注。",
        "bearish": "若低开低走或假突破回落，则需谨慎。"
    },
    "reversal_reclaim": {
        "bullish": "明日放量站稳今日高点，则弱转强确认。",
        "bearish": "若再次缩量下跌，则修复失败。"
    },
    "panic_distribution": {
        "bullish": "明日出现长下影或反包阳线，则恐慌释放完毕。",
        "bearish": "若继续放量杀跌，则退潮延续。"
    },
    "decay": {
        "bullish": "若出现倍量阳线反包，则可能止跌。",
        "bearish": "继续缩量阴跌则观望不抄底。"
    },
    "trend_follow": {
        "bullish": "沿5日线持有，不破则趋势健康。",
        "bearish": "跌破5日线且放量则趋势转弱。"
    },
    "consolidation": {
        "bullish": "放量突破箱体上沿可试多。",
        "bearish": "跌破箱体下沿则进入下降通道。"
    }
}

# ============================================================
# 风险提示文案（按状态）
# ============================================================
RISK_NOTES = {
    "acceleration":        "连续加速后分歧概率上升，注意高位回撤。",
    "breakout":            "突破初期需确认有效性，假突破伤害较大。",
    "reversal_reclaim":    "弱转强未完全确认，量能跟不上则再次转弱。",
    "panic_distribution":  "恐慌抛售未结束，盲目抄底风险极高。",
    "decay":               "缩量阴跌难言底，任何反弹都可能是诱多。",
    "trend_follow":        "趋势健康但需留意均线支撑，不破不卖。",
    "consolidation":       "方向选择节点，不宜重仓押注单方向。"}


# ============================================================
# 得分组件计算
# ============================================================
def _calc_score_components(closes, volumes, pcts):
    """
    计算趋势、量能、动量、风险得分（0-100）
    """
    # 趋势得分
    if closes[0] == 0:
        trend_score = 50
    else:
        total_pct = (closes[-1] - closes[0]) / closes[0] * 100
        trend_score = min(100, max(0, total_pct * 2 + 50))

    # 量能得分：近3日均量 / 5日均量
    avg_vol_3 = sum(volumes[-3:]) / 3
    avg_vol_5 = sum(volumes) / 5
    vol_ratio = avg_vol_3 / avg_vol_5 if avg_vol_5 > 0 else 1
    volume_score = min(100, int(vol_ratio * 80))

    # 动量得分
    momentum = sum(pcts[-3:]) if len(pcts) >= 3 else sum(pcts)
    momentum_score = min(100, max(0, int(50 + momentum * 2)))

    # 风险得分：最大回撤 + 负天数
    max_dd = 0
    peak = closes[0]
    for c in closes:
        if c > peak:
            peak = c
        dd = (peak - c) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    negative_days = sum(1 for p in pcts if p < 0)
    risk_score = min(100, int(max_dd * 200 + negative_days * 5))

    return {
        "trend_score": trend_score,
        "volume_score": volume_score,
        "momentum_score": momentum_score,
        "risk_score": risk_score
    }


# ============================================================
# 主引擎函数
# ============================================================
def get_short_term_state(daily_5: List[Dict]) -> Dict:
    """
    输入最近5日行情数据，输出统一短线状态结构

    Args:
        daily_5: [{"close": float, "volume": float, "pct_chg": float, "high": float, "low": float}, ...]

    Returns:
        {
            "state_key": str,        # 状态键（英文）
            "state_cn": str,         # 状态中文名
            "strength": int,         # 强度 0-100
            "risk": str,             # 风险等级 low/medium/high
            "tags": [str],           # 特征标签
            "narrative": str,        # 市场行为叙事
            "score_components": {},  # 四维得分
            "scenario_bullish": str, # 看多剧本
            "scenario_bearish": str, # 看空剧本
            "risk_note": str,        # 风险提示
        }
    """
    if not daily_5 or len(daily_5) < 3:
        return {
            "state_key": "insufficient_data",
            "state_cn": "数据不足",
            "strength": 0,
            "risk": "unknown",
            "tags": [],
            "narrative": f"仅有{len(daily_5) if daily_5 else 0}天数据，需要至少3天。",
            "score_components": {"trend_score": 0, "volume_score": 0, "momentum_score": 0, "risk_score": 0},
            "scenario_bullish": "数据不足，无法生成剧本。",
            "scenario_bearish": "数据不足，无法生成剧本。",
            "risk_note": "数据不足。"
        }

    closes = [d["close"] for d in daily_5]
    volumes = [d["volume"] for d in daily_5]
    pcts = [d["pct_chg"] for d in daily_5]

    positive_days = sum(1 for p in pcts if p > 0)
    negative_days = sum(1 for p in pcts if p < 0)

    total_pct = (closes[-1] - closes[0]) / closes[0] * 100 if closes[0] != 0 else 0
    is_volume_increasing = volumes[-1] > volumes[-2] > volumes[-3] if len(volumes) >= 3 else False

    # ---- 状态判定（统一命名） ----
    if total_pct > 15 and positive_days >= 4 and is_volume_increasing:
        state_key, tags, risk = "acceleration", ["连续阳线", "放量主升"], "medium"
    elif positive_days >= 3 and closes[-1] > max(closes[:-1]) and total_pct > 5:
        state_key, tags, risk = "breakout", ["平台突破", "创5日新高"], "low"
    elif pcts[-2] < -5 and pcts[-1] > 0 and volumes[-1] > volumes[-2]:
        state_key, tags, risk = "reversal_reclaim", ["弱转强", "反包预期"], "medium"
    elif pcts[-1] < -5 and volumes[-1] > volumes[-2]:
        state_key, tags, risk = "panic_distribution", ["放量下跌", "止损盘涌出"], "high"
    elif negative_days >= 4 and volumes[-1] < volumes[0]:
        state_key, tags, risk = "decay", ["缩量阴跌", "无人承接"], "high"
    elif total_pct > 0 and is_volume_increasing:
        state_key, tags, risk = "trend_follow", ["量价齐升", "多头排列"], "low"
    else:
        state_key, tags, risk = "consolidation", ["方向不明", "等待选择"], "medium"

    state_cn = STATE_MAPPING.get(state_key, "未知状态")
    strength = min(100, int(abs(total_pct) * 2)) if abs(total_pct) < 50 else 100

    # ---- 生成叙事 ----
    narrative = f"{state_cn}，{'，'.join(tags[:2])}。"
    if state_key in ["reversal_reclaim", "breakout"]:
        narrative += " 资金开始试盘，存在博弈机会。"
    elif state_key in ["panic_distribution", "decay"]:
        narrative += " 亏钱效应扩散，风险大于机会。"
    elif state_key == "acceleration":
        narrative += " 短期过热，注意分歧。"
    else:
        narrative += " 等待方向选择。"

    # ---- 得分组件 ----
    components = _calc_score_components(closes, volumes, pcts)
    if risk == "high":
        components["risk_score"] = min(100, components["risk_score"] + 30)
    elif risk == "medium":
        components["risk_score"] = min(100, components["risk_score"] + 10)

    # ---- 剧本 ----
    scenario = SCENARIO_TEMPLATES.get(state_key, SCENARIO_TEMPLATES["consolidation"])
    risk_note = RISK_NOTES.get(state_key, "注意仓位管理。")

    return {
        "state_key": state_key,
        "state_cn": state_cn,
        "strength": strength,
        "risk": risk,
        "tags": tags,
        "narrative": narrative,
        "score_components": {
            "trend_score": round(components["trend_score"]),
            "volume_score": round(components["volume_score"]),
            "momentum_score": round(components["momentum_score"]),
            "risk_score": round(components["risk_score"]),
        },
        "scenario_bullish": scenario["bullish"],
        "scenario_bearish": scenario["bearish"],
        "risk_note": risk_note,
    }


# ============================================================
# 从 akshare/CSV DataFrame 快速构造输入
# ============================================================
def daily_from_dataframe(df, n=5):
    """
    从 pandas DataFrame 提取最近 n 条日线数据

    期望列：date, open, high, low, close, volume, price_change_pct
    """
    if df is None or df.empty:
        return []
    tail = df.tail(n)
    result = []
    for _, row in tail.iterrows():
        result.append({
            "close": float(row.get("close", 0)),
            "volume": float(row.get("volume", 0)),
            "pct_chg": float(row.get("price_change_pct", 0) or row.get("pct_chg", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
        })
    return result


# ============================================================
# 测试
# ============================================================
if __name__ == "__main__":
    test_data = [
        {"close": 10,   "volume": 100, "pct_chg": 2,    "high": 10.2, "low": 9.9},
        {"close": 10.5, "volume": 120, "pct_chg": 5,    "high": 10.6, "low": 10.1},
        {"close": 11,   "volume": 140, "pct_chg": 4.76, "high": 11.2, "low": 10.8},
        {"close": 10.8, "volume": 160, "pct_chg": -1.8, "high": 11.0, "low": 10.6},
        {"close": 11.2, "volume": 180, "pct_chg": 3.7,  "high": 11.3, "low": 10.9},
    ]
    import json
    result = get_short_term_state(test_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))