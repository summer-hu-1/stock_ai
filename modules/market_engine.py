"""
市场情绪引擎 - Market Emotion Engine
实现量化情绪分析：周期判定、危险信号检测、明日观测点、AI剧本生成

四个执行项：
1. get_emotion_cycle()       — 情绪周期量化判定
2. detect_danger_signals()   — 危险信号自动检测
3. generate_observation_points() — 明日观测点
4. build_market_script_prompt()  — AI 每日市场剧本 Prompt
"""

from typing import Dict, List, Tuple


# ================================================================
# 执行项2：情绪周期量化判定函数
# ================================================================
def get_emotion_cycle(
    涨停数: int,
    跌停数: int,
    连板高度: int,
    昨日涨停溢价: float,
    炸板率: float
) -> Tuple[str, str]:
    """
    根据盘后核心数据，量化判定当前情绪周期阶段
    
    Returns:
        (阶段, 趋势)
    
    阶段可选：冰点期/试错期/发酵期/主升期/高潮期/分歧期/退潮期/修复期
    """
    if 连板高度 <= 2 and 涨停数 < 30 and 昨日涨停溢价 < 0:
        return "冰点期", "待观察"
    if 3 <= 连板高度 <= 4 and 涨停数 >= 40 and 跌停数 < 10:
        return "试错期", "尝试修复"
    if 连板高度 >= 5 and 涨停数 >= 60 and 炸板率 < 0.3:
        return "发酵期", "逐步强化"
    if 连板高度 >= 7 and 涨停数 >= 80 and 炸板率 < 0.25:
        return "主升期", "加速"
    if 连板高度 >= 6 and 炸板率 > 0.4 and 昨日涨停溢价 < 2:
        return "高潮期", "即将分歧"
    if 炸板率 > 0.4 and 跌停数 > 15 and 昨日涨停溢价 < 1:
        return "分歧期", "转退潮" if 跌停数 > 25 else "转修复"
    if 连板高度 <= 3 and 跌停数 > 20:
        return "退潮期", "延续"
    if 昨日涨停溢价 > 3 and 跌停数 < 10 and 连板高度 <= 4:
        return "修复期", "向上"
    return "分歧期", "震荡"


# ================================================================
# 执行项3：危险信号自动检测规则
# ================================================================
def detect_danger_signals(
    涨停数: int,
    跌停数: int,
    炸板率: float,
    昨日最高连板股: str = "",
    昨日最高连板股今日涨跌: float = 0,
    昨日最高连板股今日最高涨跌: float = 0,
    前日3连板以上跌停数: int = 0,
    最大板块成交额: float = 0,
    全市场成交额: float = 1,
    成交前10滞涨股数: int = 0,
) -> List[Dict]:
    """
    危险信号自动检测
    
    Returns:
        [{"信号": str, "严重程度": "高/中/低", "数值或个股": str}, ...]
    """
    signals = []
    
    # 1. 高位股炸板
    if 昨日最高连板股 and 昨日最高连板股今日涨跌 < 5 and 昨日最高连板股今日最高涨跌 < 5:
        signals.append({
            "信号": "高位股炸板",
            "严重程度": "高",
            "数值或个股": 昨日最高连板股
        })
    
    # 2. 中位股A杀
    if 前日3连板以上跌停数 >= 2:
        signals.append({
            "信号": "中位股A杀",
            "严重程度": "高",
            "数值或个股": f"前日3连板以上跌停{前日3连板以上跌停数}只"
        })
    
    # 3. 板块成交过热
    if 最大板块成交额 > 0 and 全市场成交额 > 0:
        ratio = 最大板块成交额 / 全市场成交额
        if ratio > 0.35:
            signals.append({
                "信号": "板块成交过热",
                "严重程度": "中" if ratio < 0.45 else "高",
                "数值或个股": f"最大板块占比 {ratio:.1%}"
            })
    
    # 4. 炸板率飙升
    if 炸板率 > 0.45:
        signals.append({
            "信号": "炸板率飙升",
            "严重程度": "高" if 炸板率 > 0.5 else "中",
            "数值或个股": f"{炸板率:.0%}"
        })
    
    # 5. 核按钮重现（需要早盘数据，此处按跌停家数代理）
    if 跌停数 > 25:
        signals.append({
            "信号": "核按钮重现",
            "严重程度": "高",
            "数值或个股": f"跌停家数{跌停数}只（异常）"
        })
    
    # 6. 高位放量滞涨
    if 成交前10滞涨股数 >= 3:
        signals.append({
            "信号": "高位放量滞涨",
            "严重程度": "中",
            "数值或个股": f"成交前10中{成交前10滞涨股数}只涨幅<2%且换手>15%"
        })
    
    return signals


# ================================================================
# 执行项4：明日观测点生成规则
# ================================================================
def generate_observation_points(
    主线板块: str = "主线板块",
    危险信号: List[Dict] = None,
) -> List[Dict]:
    """
    基于当日数据自动生成明日3个固定类型观测点
    
    Returns:
        [{"观测内容": str, "判定标准": str, "如果成立": str, "如果不成立": str}, ...]
    """
    if not 危险信号:
        危险信号 = []
    
    first_danger = 危险信号[0]["信号"] if 危险信号 else "昨日主线走弱"
    
    return [
        {
            "观测内容": f"{主线板块} 是否继续强化",
            "判定标准": "板块内涨停家数 ≥ 5 只，且龙头股高开高走",
            "如果成立": "继续聚焦主线，加仓龙头",
            "如果不成立": "注意主线分歧，降低仓位至5成以下"
        },
        {
            "观测内容": f"今日 {first_danger} 是否扩散",
            "判定标准": "昨日炸板股今日平均跌幅 > -3%",
            "如果成立": "管住手，不开新仓，防守为主",
            "如果不成立": "情绪修复，可轻仓试错（2成仓以内）"
        },
        {
            "观测内容": "开盘前30分钟涨跌家数比",
            "判定标准": "上涨家数 > 3000 且 昨日涨停溢价 > 1%",
            "如果成立": "积极做多，提高仓位到7成",
            "如果不成立": "防守为主，等待10:00后确认方向"
        }
    ]


# ================================================================
# 执行项1：每日市场剧本 Prompt（结构化AI分析）
# ================================================================
def build_market_script_prompt(
    涨停数: int,
    跌停数: int,
    连板高度: int,
    昨日涨停溢价: float,
    炸板率: float,
    板块数据: List[Dict] = None,
    最高连板股: str = "",
    北向资金: str = "",
    市场成交额: float = 0,
) -> str:
    """
    构建发给 AI 的市场剧本分析 Prompt
    """
    cycle, trend = get_emotion_cycle(涨停数, 跌停数, 连板高度, 昨日涨停溢价, 炸板率)
    
    板块文本 = ""
    if 板块数据:
        板块文本 = "\n".join([
            f"- {b.get('name', '')}: {b.get('change_pct', 0):+.2f}%, 成交{b.get('volume', 0):.0f}亿"
            for b in (板块数据 or [])[:5]
        ])
    
    prompt = f"""你是专业市场情绪分析AI。请根据以下行情数据输出「每日市场剧本」JSON。

输出格式严格如下：
{{
  "情绪周期": {{"阶段": "{cycle}", "趋势": "{trend}"}},
  "主线演化": {{"主线板块": "", "次主线": [], "阶段": "", "龙头股": "", "板块成交占比": 0.0}},
  "资金状态": {{"风险偏好": "", "资金流向": "", "成交结构": ""}},
  "危险信号": [{{"信号": "", "严重程度": "", "数值或个股": ""}}],
  "明日观测点": [{{"观测内容": "", "判定标准": "", "如果成立": "", "如果不成立": ""}}]
}}

情绪周期阶段可选：冰点期/试错期/发酵期/主升期/高潮期/分歧期/退潮期/修复期
主线演化阶段可选：萌芽期/强化期/分化期/退潮期
风险偏好可选：冰点/降低中/提升中/激进

今日数据：
- 涨停家数：{涨停数}
- 跌停家数：{跌停数}
- 连板高度：{连板高度}板（{最高连板股}）
- 昨日涨停溢价：{昨日涨停溢价}%
- 炸板率：{炸板率:.1%}
- 市场成交额：{市场成交额:.0f}亿
- 北向资金：{北向资金 or '暂无数据'}
- 量化判定情绪周期：{cycle}（{trend}）

强势板块TOP5：
{板块文本 or '暂无板块数据'}

请基于以上数据，完成主线演化、资金状态、危险信号和明日观测点的填充。
直接输出完整JSON，不要额外解释。"""
    
    return prompt


# ================================================================
# 综合数据采集 + 全流程引擎
# ================================================================
def run_market_emotion_analysis() -> Dict:
    """
    一站式市场情绪分析：采集数据 → 周期判定 → 危险检测 → 观测点生成 → AI剧本
    """
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from modules.market_sentiment import get_market_sentiment, get_hot_sectors
    
    # 1. 采集数据
    sentiment = get_market_sentiment(use_cache=False)
    hot_sectors = get_hot_sectors(use_cache=False) or []
    
    # 2. 提取核心指标
    涨停数 = sentiment.get("limit_up_count", 0)
    跌停数 = sentiment.get("limit_down_count", 0)
    炸板率 = sentiment.get("bomb_rate", 0)
    连板高度 = sentiment.get("连板高度", 2)
    昨日涨停溢价 = sentiment.get("昨日涨停溢价", 2.0)
    市场成交额 = sentiment.get("total_volume", 0) * 10000  # 万亿转亿
    
    # 3. 周期判定
    cycle, trend = get_emotion_cycle(涨停数, 跌停数, 连板高度, 昨日涨停溢价, 炸板率)
    
    # 4. 危险信号检测
    max_sector_vol = max((s.get("volume", 0) for s in hot_sectors), default=0) if hot_sectors else 0
    danger_signals = detect_danger_signals(
        涨停数=涨停数,
        跌停数=跌停数,
        炸板率=炸板率,
        最大板块成交额=max_sector_vol,
        全市场成交额=市场成交额,
    )
    
    # 5. 主线板块识别
    main_sector = ""
    if hot_sectors and len(hot_sectors) > 0:
        first = hot_sectors[0]
        main_sector = first.get("name", "") if isinstance(first, dict) else ""
    
    # 6. 明日观测点
    observation_points = generate_observation_points(
        主线板块=main_sector or "主线板块",
        危险信号=danger_signals,
    )
    
    # 7. AI 剧本 Prompt
    script_prompt = build_market_script_prompt(
        涨停数=涨停数,
        跌停数=跌停数,
        连板高度=连板高度,
        昨日涨停溢价=昨日涨停溢价,
        炸板率=炸板率,
        板块数据=hot_sectors[:5] if hot_sectors else [],
        最高连板股=sentiment.get("最高连板股", ""),
        市场成交额=市场成交额,
    )
    
    return {
        "sentiment": sentiment,
        "data_source": sentiment.get("data_source", "unknown"),
        "cycle": cycle,
        "trend": trend,
        "danger_signals": danger_signals,
        "main_sector": main_sector,
        "observation_points": observation_points,
        "script_prompt": script_prompt,
        "hot_sectors": hot_sectors,
    }


def generate_ai_script(script_prompt: str) -> str:
    """调用 DeepSeek API 生成市场剧本 JSON"""
    import os
    try:
        import openai
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
        if not api_key:
            return "❌ 未配置 DEEPSEEK_API_KEY"
        
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": script_prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI生成失败: {str(e)}"