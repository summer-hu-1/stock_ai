"""
交易语言翻译层 — 系统/引擎输出 → 交易员能理解的文案

原则：
- 不暴露任何技术指标名、评分数字、系统内部状态
- 每句话都像交易员之间聊天一样自然
- 用户读完后知道"该做什么"而不是"数据是什么"
"""

# ============================================================
# 个股状态 → 交易语言
# ============================================================
STATE_TO_TRADER_CN = {
    "acceleration":         "资金还在持续进攻",
    "trend_follow":         "稳步向上，做多情绪还在",
    "breakout":             "有资金开始抢筹",
    "reversal_reclaim":     "可能有资金在试盘",
    "consolidation":        "方向不明确，先看看",
    "panic_distribution":   "抛压在加大，要小心",
    "decay":                "短线开始不好做了",
}

# 状态 → 简洁版（用于标签）
STATE_TO_LABEL = {
    "acceleration":         "持续进攻",
    "trend_follow":         "稳步向上",
    "breakout":             "资金抢筹",
    "reversal_reclaim":     "资金试盘",
    "consolidation":        "等待方向",
    "panic_distribution":   "抛压加大",
    "decay":                "不好做",
}

# 风险等级 → 交易语言
RISK_TO_TRADER_CN = {
    "low":    "风险不大，正常波动",
    "medium": "高位开始有人兑现",
    "high":   "抛压明显，小心点",
    "unknown": "状态不确定，多看少动",
}


# ============================================================
# 市场情绪翻译
# ============================================================
def translate_market_status(sentiment: dict) -> dict:
    """
    输入 market_sentiment 数据，输出 trader 可读的动态状态。

    Returns:
        {
            "signal": "🟢" | "🔴" | "🟡",
            "status_text": str,   # 一句话动态状态，如"资金重新回流 AI"
            "main_line": str,     # 主线板块，如"AI 算力 / 铜缆高速连接"
            "ai_hint": str,       # AI 摘要标签
        }
    """
    limit_up = sentiment.get("limit_up_count", 0)
    limit_down = sentiment.get("limit_down_count", 0)
    bomb_rate = sentiment.get("bomb_rate", 0)
    rise_ratio = sentiment.get("rise_ratio", 0)
    mood = sentiment.get("market_mood", "")

    # --- 信号灯 ---
    if limit_up >= 80 and bomb_rate < 0.3:
        signal = "🟢"
    elif limit_up < 30 or bomb_rate > 0.45 or limit_down > 25:
        signal = "🔴"
    else:
        signal = "🟡"

    # --- 动态状态文案 ---
    if signal == "🟢":
        if limit_up >= 100:
            status_text = "今天情绪很高，但注意第二天容易分歧"
        else:
            status_text = "资金重新回流，做多情绪在恢复"
    elif signal == "🔴":
        if bomb_rate > 0.5:
            status_text = "高位开始集体兑现，追高的人今天全被埋了"
        elif limit_down > 30:
            status_text = "恐慌盘开始涌出，短线注意风险"
        else:
            status_text = "短线开始不好赚钱了，多看少动"
    else:
        status_text = "市场正在等新的主线，方向还不明确"

    return {
        "signal": signal,
        "status_text": status_text,
        "rise_ratio": rise_ratio,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "bomb_rate": bomb_rate,
    }


def extract_main_line(hot_sectors: list) -> str:
    """从热门板块提取主线描述"""
    if not hot_sectors or len(hot_sectors) == 0:
        return "方向还不明确"
    if len(hot_sectors) == 1:
        return hot_sectors[0].get("name", "方向还不明确")
    top2 = [s.get("name", "") for s in hot_sectors[:2]]
    return f"{top2[0]} / {top2[1]}"


# ============================================================
# 危险信号翻译
# ============================================================
DANGER_TRANSLATIONS = {
    "高位股炸板":    "高位连板票今天炸板明显增多，追高的人全被埋了",
    "中位股A杀":     "前面几天涨停的中位股今天直接跌停，短线生态恶化",
    "炸板率飙升":    "今天追涨停的人大部分都被坑了，短线不好做",
    "核按钮重现":    "恐慌盘开始不计成本地卖，跌停数量异常",
    "高位放量滞涨":  "成交大的票涨不动了，有资金在悄悄跑",
    "板块成交过热":  "钱太集中在少数板块，一旦松动跳水会很猛",
}


def translate_danger_signals(danger_signals: list) -> list:
    """
    将 detect_danger_signals 输出翻译为交易语言。
    返回最多 3 条。
    """
    if not danger_signals:
        return []

    result = []
    for ds in danger_signals[:3]:
        signal_name = ds.get("信号", "")
        trader_text = DANGER_TRANSLATIONS.get(signal_name)
        if trader_text:
            result.append(trader_text)
        else:
            # 兜底：直接描述
            severity = ds.get("严重程度", "")
            detail = ds.get("数值或个股", "")
            result.append(f"{signal_name}（{detail}），需要留意")

    return result[:3]


# ============================================================
# 主线记忆构建
# ============================================================
def build_main_line_history_prompt(hot_sectors_5d: list, sentiment_5d: list) -> str:
    """
    构建发给 AI 的"过去 5 天市场主线记忆" Prompt。

    hot_sectors_5d: 过去 5 天每天的热门板块数据 [day1_sectors, day2_sectors, ...]
    sentiment_5d: 过去 5 天每天的市场情绪数据 [day1_sentiment, day2_sentiment, ...]
    """
    weekdays = ["周一", "周二", "周三", "周四", "周五"]

    data_lines = []
    for i, (sectors, sent) in enumerate(zip(hot_sectors_5d, sentiment_5d)):
        day_label = weekdays[i] if i < 5 else f"Day{i+1}"
        top_sectors = ", ".join([s.get("name", "") for s in sectors[:3]]) if sectors else "数据不足"
        mood = sent.get("market_mood", "") if sent else ""
        data_lines.append(f"{day_label}：领涨板块 [{top_sectors}]，市场情绪 [{mood}]")

    prompt = f"""你是一个熟悉A股市场的交易员。请根据过去5天的领涨板块和市场情绪，用自然语言总结市场的"主线故事"。

要求：
- 用交易员聊天的语气，不要研报风格
- 每天一句话，连起来像一个完整的故事
- 注意主线是否持续、是否有新方向接力、资金是否在高位分歧
- 输出格式：每天一行，以 "Day 1（周一）：" 开头

过去 5 天数据：
{chr(10).join(data_lines)}

直接输出 5 行，每行以 "Day N（周X）：" 开头，不要额外解释。"""

    return prompt


# ============================================================
# 次日剧本 Prompt
# ============================================================
def build_next_day_scenario_prompt(
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
    构建发给 AI 的次日剧本 Prompt。
    返回包含高开/平开/低开三档的完整剧本。
    """
    prompt = f"""你是一个A股短线交易员。请为以下股票生成「明天怎么办」的剧本。

股票：{stock_name}（{stock_code}）
今天收盘：{current_price}元，涨跌幅 {pct_chg:+.2f}%
当前状态：{trader_state}
所在板块：{sector_name}（{sector_position}）
量价特征：{volume_trend}
近期走势：{recent_pattern}

请按以下格式输出（必须分三档，禁止通用套话如"注意风险控制仓位"）：

如果高开（>2%）：
  具体条件和对应动作
  
如果平开或小低开：
  具体条件和对应动作

如果大幅低开（<-5%）：
  具体条件和对应动作

⚠️ 关键风险：
  结合该股自身特点的最重要风险点

要求：
- 每句话都是具体的条件+具体的动作
- 禁止"建议逢低布局"、"注意风险控制仓位"等套话
- 像交易员之间聊天一样直接"""

    return prompt


# ============================================================
# 市场理解简报 Prompt
# ============================================================
def build_market_brief_prompt(sentiment: dict, hot_sectors: list, trader_status: dict) -> str:
    """
    构建市场理解蒸馏 Prompt（80-120 字）。
    """
    hot_names = ", ".join([s.get("name", "") for s in hot_sectors[:5]]) if hot_sectors else "暂无数据"
    mood = sentiment.get("market_mood", "")
    limit_up = sentiment.get("limit_up_count", 0)
    limit_down = sentiment.get("limit_down_count", 0)
    rising = sentiment.get("rising_count", 0)
    falling = sentiment.get("falling_count", 0)
    bomb_rate = sentiment.get("bomb_rate", 0)

    prompt = f"""你是一个A股市场老手，用交易员聊天的语气，把今天市场最重要的信息用80-120字说清楚。

今日数据：
- 涨停：{limit_up}家，跌停：{limit_down}家
- 上涨：{rising}家，下跌：{falling}家
- 炸板率：{bomb_rate*100:.0f}%
- 市场情绪：{mood}
- 热门方向：{hot_names}

要求：
- 回答三个问题：钱去哪了？钱从哪跑了？有没有伪热点？
- 一段话，不分点，不列标题
- 像交易员收盘后跟朋友聊天一样自然
- 严格 80-120 字

直接输出一段话："""

    return prompt


# ============================================================
# 主力行为分析
# ============================================================
def analyze_main_force(volumes: list, pcts: list, state_key: str) -> dict:
    """
    基于量价数据输出主力行为分析（纯规则，不调 AI）。

    Returns:
        {"attitude": str, "feature": str, "judgment": str}
    """
    if not volumes or len(volumes) < 3:
        return {
            "attitude": "数据不足，无法判断",
            "feature": "",
            "judgment": "",
        }

    # 量能趋势
    vol_avg_3 = sum(volumes[-3:]) / 3
    vol_avg_all = sum(volumes) / len(volumes)
    vol_ratio = vol_avg_3 / vol_avg_all if vol_avg_all > 0 else 1

    # 涨跌趋势
    positive_days = sum(1 for p in pcts if p > 0)
    negative_days = sum(1 for p in pcts if p < 0)

    # 主力态度
    if vol_ratio > 1.3 and positive_days >= 3:
        attitude = "主力没走，趋势资金还在里面"
        feature = f"已经连续放量，有大资金在买"
    elif vol_ratio > 1.1 and positive_days >= 2:
        attitude = "有资金在试盘，但还不算猛"
        feature = "量在慢慢放大，有人在收集筹码"
    elif vol_ratio < 0.8 and negative_days >= 3:
        attitude = "主力在撤退，资金在跑"
        feature = "缩量下跌，没人接盘"
    elif state_key in ("panic_distribution", "decay"):
        attitude = "主力大概率已经走了"
        feature = "量价都在往下走，等止跌信号"
    else:
        attitude = "主力态度不明确，还需要观察"
        feature = "量价没有明确方向"

    # AI 判断
    if state_key == "acceleration":
        judgment = "机构控盘，短期不容易深调"
    elif state_key == "trend_follow":
        judgment = "趋势健康，只要不破位就可以继续看"
    elif state_key == "breakout":
        judgment = "刚启动，能不能持续看明天确认"
    elif state_key in ("panic_distribution", "decay"):
        judgment = "等恐慌盘出清信号，现在别急着抄"
    else:
        judgment = "方向不明确，多看一天"

    return {
        "attitude": attitude,
        "feature": feature,
        "judgment": judgment,
    }


# ============================================================
# 市场定位分析
# ============================================================
def analyze_market_position(
    stock_name: str,
    sector_name: str,
    rank_in_sector: int,
    total_in_sector: int,
    pct_chg: float,
    sector_avg_chg: float,
) -> dict:
    """
    分析个股在板块中的定位（纯规则）。

    Returns:
        {"role": str, "rank": str, "relation": str}
    """
    if rank_in_sector <= 1:
        role = f"在{sector_name}板块里，这票是龙头角色"
        rank = "龙头（龙一）"
    elif rank_in_sector <= 3:
        role = f"在{sector_name}板块里，这票是中军角色，不是龙头但走得最稳"
        rank = f"龙{rank_in_sector}"
    elif rank_in_sector <= 10:
        role = f"在{sector_name}板块里属于前排跟风，龙头吃肉它喝汤"
        rank = f"板块第{rank_in_sector}"
    else:
        role = f"在{sector_name}板块里属于后排补涨，弹性一般"
        rank = f"板块第{rank_in_sector}/{total_in_sector}"

    if pct_chg > sector_avg_chg:
        relation = f"比板块平均强，有自己独立的资金在运作"
    else:
        relation = f"跟板块同步走，没有独立行情"

    return {
        "role": role,
        "rank": rank,
        "relation": relation,
    }