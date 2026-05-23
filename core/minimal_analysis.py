"""
AI 蒸馏引擎 — 轻量级 DeepSeek 调用，将多源数据蒸馏为交易员可读的自然语言。

核心输出：
1. 市场理解简报（80-120字）
2. 过去5天市场主线叙事
3. 个股次日剧本
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.trader_lang import (
    build_market_brief_prompt,
    build_main_line_history_prompt,
    build_next_day_scenario_prompt,
)


def _call_deepseek(prompt: str, max_tokens: int = 600, temperature: float = 0.6) -> Optional[str]:
    """通用 DeepSeek 调用"""
    try:
        from deepseek import get_client
        from core.model_config import get_current_model

        client = get_client()
        model = get_current_model()

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[minimal_analysis] DeepSeek 调用失败: {e}")
        return None


# ============================================================
# 1. 市场理解简报
# ============================================================
def distill_market_brief(sentiment: dict, hot_sectors: list, trader_status: dict) -> str:
    """
    生成 80-120 字市场理解简报。

    降级策略：AI 不可用时用规则生成。
    """
    prompt = build_market_brief_prompt(sentiment, hot_sectors, trader_status)
    result = _call_deepseek(prompt, max_tokens=200, temperature=0.5)

    if result:
        return result

    # 降级：规则生成
    return _fallback_market_brief(sentiment, hot_sectors)


def _fallback_market_brief(sentiment: dict, hot_sectors: list) -> str:
    """规则降级：不调 AI 时生成简报"""
    mood = sentiment.get("market_mood", "震荡")
    limit_up = sentiment.get("limit_up_count", 0)
    limit_down = sentiment.get("limit_down_count", 0)
    rising = sentiment.get("rising_count", 0)
    falling = sentiment.get("falling_count", 0)
    bomb_rate = sentiment.get("bomb_rate", 0)

    hot_names = [s.get("name", "") for s in (hot_sectors or [])[:3]]
    hot_str = "、".join(hot_names) if hot_names else "多个方向"

    if mood == "高潮" or limit_up >= 80:
        return (
            f"今天市场情绪很高，涨停{limit_up}家，资金集中进攻{hot_str}方向。"
            f"但要注意，这波情绪已经过热，明天很容易分歧。"
        )
    elif mood == "强势" or limit_up >= 50:
        return (
            f"今天上涨{rising}家、下跌{falling}家，做多情绪还可以，"
            f"{hot_str}方向有资金在持续买。只要不出现大面积炸板，短期问题不大。"
        )
    elif mood == "退潮" or limit_down > 25:
        return (
            f"今天跌停{limit_down}家，短线开始不好做了。"
            f"{hot_str}方向还有一点热度，但整体在退潮，不要追高。"
        )
    else:
        return (
            f"今天上涨{rising}家、下跌{falling}家，市场在震荡等方向。"
            f"{hot_str}方向比较活跃，但不是全面进攻，多看少动。"
        )


# ============================================================
# 2. 市场主线记忆（5天）
# ============================================================
def distill_main_line_memory(hot_sectors_5d: list, sentiment_5d: list) -> str:
    """
    生成过去 5 天市场主线叙事。

    Args:
        hot_sectors_5d: [day1_sectors, day2_sectors, ...] 每天的热门板块列表
        sentiment_5d: [day1_sentiment, day2_sentiment, ...] 每天的市场情绪

    Returns:
        "Day 1（周一）：机器人方向启动，资金试探性进场\n..."
    """
    if len(hot_sectors_5d) < 3:
        return _fallback_main_line_memory(hot_sectors_5d)

    prompt = build_main_line_history_prompt(hot_sectors_5d, sentiment_5d)
    result = _call_deepseek(prompt, max_tokens=400, temperature=0.5)

    if result:
        return result

    return _fallback_main_line_memory(hot_sectors_5d)


def _fallback_main_line_memory(hot_sectors_5d: list) -> str:
    """规则降级"""
    weekdays = ["周一", "周二", "周三", "周四", "周五"]
    lines = []
    for i, sectors in enumerate(hot_sectors_5d):
        day = weekdays[i] if i < len(weekdays) else f"Day{i+1}"
        if sectors and len(sectors) > 0:
            top = sectors[0].get("name", "方向不明")
            pct = sectors[0].get("change_pct", 0)
            action = "资金涌入" if pct >= 3 else "资金关注" if pct >= 1 else "方向试探"
            lines.append(f"Day {i+1}（{day}）：{top}{action}")
        else:
            lines.append(f"Day {i+1}（{day}）：数据不足")
    return "\n".join(lines)


# ============================================================
# 3. 个股次日剧本
# ============================================================
def distill_next_day_scenario(
    stock_name: str,
    stock_code: str,
    current_price: float,
    pct_chg: float,
    trader_state: str,
    sector_name: str,
    sector_position: str,
    volume_trend: str,
    recent_pattern: str,
) -> str:
    """
    生成个股次日剧本。

    降级策略：AI 不可用时用规则模板。
    """
    prompt = build_next_day_scenario_prompt(
        stock_name=stock_name,
        stock_code=stock_code,
        current_price=current_price,
        pct_chg=pct_chg,
        trader_state=trader_state,
        sector_name=sector_name,
        sector_position=sector_position,
        volume_trend=volume_trend,
        recent_pattern=recent_pattern,
    )
    result = _call_deepseek(prompt, max_tokens=600, temperature=0.6)

    if result:
        return result

    return _fallback_next_day_scenario(stock_name, trader_state, current_price)


def _fallback_next_day_scenario(stock_name: str, trader_state: str, price: float) -> str:
    """规则降级：次日剧本模板"""
    return f"""📅 明天怎么办？

如果高开（>2%）：
  放量站稳今天高点 → 可以继续拿着
  冲高回落且炸板 → 该减就减

如果平开或小低开：
  半小时内翻红 → 可能是弱转强，关注
  持续水下震荡 → 先看戏

如果大幅低开（<-5%）：
  15 分钟内不能站回 -3% 以上 → 该止损就止损

⚠️ 关键风险：
  当前状态「{trader_state}」，明天如果板块分歧，不要追高。"""


# ============================================================
# 4. 交易主题蒸馏
# ============================================================
def distill_market_theme(sentiment: dict, hot_sectors: list) -> str:
    """
    生成"今天市场在交易什么"一句话总结。
    例如："AI 算力业绩确定性 + 铜缆新技术预期"
    """
    if not hot_sectors or len(hot_sectors) == 0:
        mood = sentiment.get("market_mood", "")
        return "方向还不明确" if mood != "强势" else "多个方向轮动"

    top = hot_sectors[:3]
    themes = []
    for s in top:
        name = s.get("name", "")
        pct = s.get("change_pct", 0)
        if pct >= 3:
            themes.append(f"{name}方向确定性")
        elif pct >= 1:
            themes.append(f"{name}预期")

    if not themes:
        themes = [f"{top[0].get('name', '')}试探"]

    return " + ".join(themes[:3])