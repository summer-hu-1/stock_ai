"""
量化成长卡片引擎 — Cognitive Engine

不是课程，不是教材。
而是每天一个市场核心认知，
让用户在不知不觉中建立交易理解。

使用方式：
    card = get_quant_growth_card()
    print(card["title"])   # "什么叫趋势？"
    print(card["content"]) # "趋势不是涨一天..."
"""

import random
from datetime import date, datetime
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# 成长路径 — 分四个阶段
# 每个阶段 8~10 个认知点
# ---------------------------------------------------------------------------

STAGE_1: list[Dict] = [
    {
        "title": "什么叫趋势？",
        "content": "趋势不是涨一天，而是资金持续愿意往一个方向推动。真正的趋势，通常伴随：放量、持续性、板块联动。一天的涨跌只是噪音，持续的方向才是趋势。",
        "tag": "趋势认知",
    },
    {
        "title": "为什么很多人总买在高点？",
        "content": "因为人会天然觉得：涨得越快越安全。但市场里，最危险的时候，往往也是情绪最兴奋的时候。当所有人都开始相信还能继续涨时，真正愿意接盘的人反而越来越少。",
        "tag": "情绪认知",
    },
    {
        "title": "什么叫成交量？",
        "content": "成交量是市场的温度计。放量代表分歧加大——有人急着买，有人急着卖。缩量代表意见统一——大家都不想动。真正的大行情，往往从缩量开始，到放量结束。",
        "tag": "量能认知",
    },
    {
        "title": "为什么要看板块？",
        "content": "个股很难独立于板块。一个股票大涨，如果板块不动，可能是游资炒作，来得快去得也快。如果整个板块都在涨，说明有资金在系统性布局，持续性更强。",
        "tag": "板块认知",
    },
    {
        "title": "什么叫主线？",
        "content": "主线不是一天的热点，而是一个阶段市场最认可的方向。它通常有产业逻辑支撑、有龙头带队、有板块助攻。看不懂主线，就容易在杂毛里浪费时间。",
        "tag": "主线认知",
    },
    {
        "title": "为什么亏了要止损？",
        "content": "亏损10%需要涨11%回本，亏损30%需要涨43%回本，亏损50%需要涨100%回本。止损不是认输，而是保留本金，等待下一个更好的机会。",
        "tag": "风控认知",
    },
    {
        "title": "什么叫情绪周期？",
        "content": "市场情绪像天气一样循环：冰点→试错→发酵→高潮→分歧→退潮→冰点。在退潮期强行交易，就像台风天出海。看懂情绪周期，就知道什么时候该出手。",
        "tag": "情绪认知",
    },
    {
        "title": "为什么要有交易纪律？",
        "content": "散户最大的问题不是技术差，而是没有纪律。涨了就追、跌了就慌、赚了不走、亏了死扛。交易纪律不是限制你，而是保护你。",
        "tag": "纪律认知",
    },
]

STAGE_2: list[Dict] = [
    {
        "title": "为什么追高很危险？",
        "content": "追高本质是在赌博——你把希望寄托在有人以更高价接盘。但市场不是击鼓传花。当股价已经涨了一倍，剩下的空间可能远小于下跌空间。",
        "tag": "交易认知",
    },
    {
        "title": "仓位为什么重要？",
        "content": "满仓一只股票，就像把所有鸡蛋放在一个篮子里。即使你看对了方向，一次波动就可能被震出局。合理的仓位管理，让市场波动变成机会，而不是风险。",
        "tag": "仓位认知",
    },
    {
        "title": "为什么会退潮？",
        "content": "退潮不是因为市场坏，而是因为买盘枯竭。当所有想买的人都买了，就没有新的资金来推动价格。这时候哪怕没有利空，价格也会自然回落。",
        "tag": "市场认知",
    },
    {
        "title": "为什么会炸板？",
        "content": "炸板的意思是涨停板被打开。这说明有资金在板上出货，或者市场抛压突然增大。连板股炸板率高，往往意味着这波炒作接近尾声。",
        "tag": "盘口认知",
    },
    {
        "title": "什么叫盈亏比？",
        "content": "盈亏比=预期收益÷预期亏损。如果一笔交易赚能赚10%，亏只亏5%，盈亏比是2:1。长期来看，哪怕只有50%的胜率，好的盈亏比也能让你盈利。",
        "tag": "数学认知",
    },
    {
        "title": "为什么利好出货？",
        "content": "利好消息出来时，懂得人早在低位买好了。消息公开的时候，正是他们卖给追进来的人的时候。这就是为什么利好出来反而跌——买预期，卖事实。",
        "tag": "博弈认知",
    },
    {
        "title": "什么叫洗盘？",
        "content": "主力拉升前，常常故意砸盘，把不坚定的人吓出去。洗盘的特征是：缩量下跌、跌幅不深、很快收回。如果你被洗出去，后面的大涨就跟你没关系了。",
        "tag": "主力认知",
    },
    {
        "title": "为什么横盘很久突然拉升？",
        "content": "长时间的横盘，说明买卖双方达成了平衡。突然拉升，往往是主力完成了吸筹，开始进入拉升阶段。横有多长，竖有多高——横盘时间越长，后续空间可能越大。",
        "tag": "形态认知",
    },
]

STAGE_3: list[Dict] = [
    {
        "title": "什么是回撤？",
        "content": "回撤就是从最高点跌下来的幅度。比如你的账户从100万跌到80万，回撤就是20%。控制回撤比追求收益更重要，因为一次大回撤可能毁掉你几个月的利润。",
        "tag": "量化认知",
    },
    {
        "title": "什么是胜率？",
        "content": "胜率=盈利交易÷总交易次数。很多人追求高胜率，但真正赚钱的交易者，胜率可能只有40%。他们靠的是：亏的时候亏得少，赚的时候赚得多。",
        "tag": "量化认知",
    },
    {
        "title": "什么是因子？",
        "content": "因子就是影响股价的某个特征。比如：动量因子（涨得好的股票更容易继续涨）、价值因子（便宜的股票更安全）。量化交易就是用这些因子来辅助决策。",
        "tag": "量化认知",
    },
    {
        "title": "什么叫夏普比率？",
        "content": "夏普比率=收益÷波动风险。它衡量的是：你每承担一份风险，能获得多少回报。夏普比率>1算不错，>2就很优秀。它告诉你赚钱的质量，而不只是赚了多少。",
        "tag": "量化认知",
    },
    {
        "title": "什么叫过拟合？",
        "content": "过拟合就是把策略调整得只适合过去的数据，但一到未来就失效。就像考试只背答案而不理解题目。好的策略应该简单、稳定、逻辑可解释。",
        "tag": "量化认知",
    },
    {
        "title": "什么是Alpha？",
        "content": "Alpha是超额收益。如果大盘涨了10%，你赚了15%，多出来的5%就是Alpha。量化交易的核心目标，就是找到稳定产生Alpha的策略。",
        "tag": "量化认知",
    },
    {
        "title": "为什么量化要分散？",
        "content": "单一策略可能会失效，单一股票可能会暴雷。量化交易通过分散投资（多股票、多策略、多周期），降低整体风险。不把命运押注在任何一个单一因素上。",
        "tag": "量化认知",
    },
    {
        "title": "什么是回测？",
        "content": "回测就是用历史数据检验你的交易策略。但注意：回测结果好不代表未来一定好。市场会变、参与者会变、规则也会变。回测只是参考，不是保证。",
        "tag": "量化认知",
    },
]

STAGE_4: list[Dict] = [
    {
        "title": "什么是策略？",
        "content": "策略不是随便买一只股票，而是一套完整的规则：什么条件买入、什么条件卖出、仓位多少、如何止损。没有策略的交易，本质上是在碰运气。",
        "tag": "系统认知",
    },
    {
        "title": "什么是纪律？",
        "content": "纪律就是：制定策略后，严格执行。哪怕这次严格执行亏了，也要做。因为纪律保护的是长期生存。一次不守纪律赚了钱，反而可能让你养成坏习惯。",
        "tag": "系统认知",
    },
    {
        "title": "什么是长期主义？",
        "content": "长期主义不是死扛不动，而是用长期视角做决策。不因为一天的涨跌改变判断，不因为一次亏损否定系统。市场短期是投票机，长期是称重机。",
        "tag": "系统认知",
    },
    {
        "title": "什么是风险控制？",
        "content": "风险控制不是少交易，而是：单笔亏损不超过总资金的2%、出现连续亏损时暂停交易、永远不要孤注一掷。活下来，是交易的第一个目标。",
        "tag": "系统认知",
    },
    {
        "title": "为什么要有交易日志？",
        "content": "不记录的交易就像没有发生过。交易日志帮你复盘：哪些决策是对的、哪些是情绪化的、哪些模式在重复发生。没有复盘，很难真正进步。",
        "tag": "系统认知",
    },
    {
        "title": "什么叫盈亏同源？",
        "content": "让你赚钱的方法，也可能让你亏钱。追涨杀跌可能赚到爆发收益，也可能买在最高点。不要羡慕别人的收益，因为你看不到他们承担的风险。",
        "tag": "系统认知",
    },
    {
        "title": "什么是护城河？",
        "content": "一个交易系统的护城河，是别人不容易复制的东西。比如：独特的数据源、长期的盘感积累、稳定的心态、严格的纪律。没有护城河的策略，迟早会失效。",
        "tag": "系统认知",
    },
    {
        "title": "什么是成长？",
        "content": "交易的成长不是从亏到赚，而是从无知到自知。知道自己不懂什么，比知道自己懂什么更重要。市场永远在变，唯一不变的是：持续学习的人能活得更久。",
        "tag": "系统认知",
    },
]

# 全量内容按阶段组织
ALL_CARDS = [
    *STAGE_1,
    *STAGE_2,
    *STAGE_3,
    *STAGE_4,
]

# 每个卡片的阶段映射（用于计算等级）
CARD_STAGE_MAP: list[int] = []
for i, _ in enumerate(STAGE_1):
    CARD_STAGE_MAP.append(1)
for i, _ in enumerate(STAGE_2):
    CARD_STAGE_MAP.append(2)
for i, _ in enumerate(STAGE_3):
    CARD_STAGE_MAP.append(3)
for i, _ in enumerate(STAGE_4):
    CARD_STAGE_MAP.append(4)

STAGE_LABELS = {
    1: "看懂市场",
    2: "理解交易",
    3: "理解量化",
    4: "理解系统",
}

STAGE_LEVEL = {
    1: "Lv1",
    2: "Lv2",
    3: "Lv3",
    4: "Lv4",
}


# ---------------------------------------------------------------------------
# 核心 API
# ---------------------------------------------------------------------------

def get_quant_growth_card(seed_date: Optional[date] = None) -> Dict:
    """
    返回当天的量化成长卡片。

    算法：以天数为种子，从全量卡片池中按序获取。
    这样做的好处：
    1. 同一天所有人看到的卡片相同（一致性）
    2. 每天自动推进
    3. 不需要数据库

    Args:
        seed_date: 指定日期（用于测试），默认今天

    Returns:
        Dict: {level, title, content, tag}
    """
    if seed_date is None:
        seed_date = date.today()

    # 以 2025-01-01 为起点
    origin = date(2025, 1, 1)
    day_offset = (seed_date - origin).days

    if day_offset < 0:
        day_offset = 0

    # 循环索引，确保永远有内容
    idx = day_offset % len(ALL_CARDS)
    stage = CARD_STAGE_MAP[idx]
    card = ALL_CARDS[idx]

    # 计算总天数（以显示进度感）
    total_days = len(ALL_CARDS)
    current_day = day_offset % total_days + 1

    return {
        "level": STAGE_LEVEL[stage],
        "title": card["title"],
        "content": card["content"],
        "tag": card["tag"],
        "stage_name": STAGE_LABELS[stage],
        "day": current_day,
        "total_days": total_days,
    }


def get_growth_card_by_index(index: int) -> Dict:
    """
    按索引获取卡片（用于测试）。

    Args:
        index: 卡片索引

    Returns:
        Dict: {level, title, content, tag}
    """
    idx = index % len(ALL_CARDS)
    stage = CARD_STAGE_MAP[idx]
    card = ALL_CARDS[idx]
    return {
        "level": STAGE_LEVEL[stage],
        "title": card["title"],
        "content": card["content"],
        "tag": card["tag"],
        "stage_name": STAGE_LABELS[stage],
        "day": idx + 1,
        "total_days": len(ALL_CARDS),
    }


def get_quant_term_card(seed_date: Optional[date] = None) -> dict:
    """
    返回当天的量化词条卡片，与成长卡片错开一天的内容。

    使用种子日期 + 1 偏移，确保每天两张卡片内容不重复。

    Args:
        seed_date: 指定日期，默认今天

    Returns:
        dict: {title, content, tag}
    """
    if seed_date is None:
        seed_date = date.today()

    origin = date(2025, 1, 1)
    day_offset = (seed_date - origin).days + 1  # 偏移一天

    if day_offset < 0:
        day_offset = 0

    idx = day_offset % len(ALL_CARDS)
    card = ALL_CARDS[idx]

    return {
        "title": card["title"],
        "content": card["content"],
        "tag": card["tag"],
    }


def format_growth_card(card: Dict) -> str:
    """
    格式化为可读文本（用于调试/日志）。

    Args:
        card: get_quant_growth_card() 返回的卡片

    Returns:
        str: 格式化文本
    """
    return (
        f"🌱 AI量化成长\n\n"
        f"{card['level']} · {card['tag']}\n\n"
        f"{card['title']}\n\n"
        f"{card['content']}\n\n"
        f"—— 第{card['day']}天 · {card['stage_name']}"
    )


if __name__ == "__main__":
    # 测试：预览未来 5 天的卡片
    from datetime import timedelta
    base = date.today()
    for i in range(5):
        d = base + timedelta(days=i)
        card = get_quant_growth_card(seed_date=d)
        print(f"=== Day {i+1} ({d.isoformat()}) ===")
        print(format_growth_card(card))
        print()
