"""
热点时间线生成器 — 基于板块异动数据生成当日关键时间点的市场动作

核心逻辑：
- 基于板块涨幅排序，模拟关键时间点的市场异动
- 最高涨幅的板块分配到最早的交易时间段
- 可扩展接入东方财富/新浪真实异动接口
"""

import random
from typing import List, Dict


def generate_hot_timeline(
    hot_sectors: List[Dict],
    sentiment: Dict = None,
    stock_count: int = 5,
) -> List[Dict]:
    """
    基于热门板块数据生成今日异动时间线。

    Args:
        hot_sectors: 热门板块列表，每项含 name, change_pct, rise_count
        sentiment: 市场情绪数据（可选）
        stock_count: 最大返回条数（默认 5）

    Returns:
        [
            {"time": "09:35", "event": "AI 算力方向集体抢筹，中际旭创放量拉升"},
            ...
        ]
    """
    if not hot_sectors:
        return _fallback_timeline(sentiment)

    # 时间槽：从 09:35 开始，每 60-90 分钟一条
    time_slots = ["09:35", "10:12", "11:05", "13:18", "14:22"]
    events = []

    # 按涨幅从高到低排序
    sorted_sectors = sorted(hot_sectors, key=lambda x: x.get("change_pct", 0), reverse=True)
    top_sectors = sorted_sectors[:stock_count]

    # 领涨股的候选名称（板块 + 方向描述）
    sector_leaders = {
        "AI": ["中际旭创", "新易盛", "天孚通信", "工业富联", "寒武纪"],
        "算力": ["中际旭创", "浪潮信息", "中科曙光", "高新发展"],
        "芯片": ["韦尔股份", "北方华创", "中芯国际", "兆易创新"],
        "半导体": ["韦尔股份", "中芯国际", "北方华创"],
        "机器人": ["拓斯达", "绿的谐波", "埃斯顿", "汇川技术"],
        "新能源": ["宁德时代", "比亚迪", "阳光电源"],
        "光伏": ["隆基绿能", "通威股份", "阳光电源"],
        "锂电": ["宁德时代", "亿纬锂能", "赣锋锂业"],
        "铜缆": ["沃尔核材", "华脉科技", "神宇股份"],
        "汽车": ["比亚迪", "赛力斯", "长安汽车"],
        "军工": ["中航沈飞", "航发动力", "中无人机"],
        "医药": ["药明康德", "恒瑞医药", "迈瑞医疗"],
        "消费": ["贵州茅台", "中国中免", "海天味业"],
        "金融": ["中信证券", "东方财富", "中国平安"],
        "地产": ["万科A", "保利发展", "招商蛇口"],
    }

    for i, sector in enumerate(top_sectors):
        name = sector.get("name", "")
        change_pct = sector.get("change_pct", 0)
        rise_count = sector.get("rise_count", 0)
        fall_count = sector.get("fall_count", 0)

        # 匹配领涨股
        leader_name = ""
        for keyword, names in sector_leaders.items():
            if keyword in name:
                leader_name = random.choice(names)
                break
        if not leader_name:
            leader_name = "龙头股"

        # 生成异动描述
        if change_pct >= 5:
            action = "集体抢筹"
            detail = f"{leader_name}放量拉升"
        elif change_pct >= 3:
            action = "资金涌入"
            detail = f"{leader_name}领涨"
        elif change_pct >= 1:
            action = "异动"
            detail = f"{leader_name}开始有资金关注"
        elif change_pct >= 0:
            detail = f"板块微涨，方向还不明确"
        else:
            continue  # 下跌板块跳过

        event = f"{name}方向{action}，{detail}"
        if rise_count > 0 and fall_count > 0:
            event += f"（板块内 {rise_count} 涨 {fall_count} 跌）"

        time_slot = time_slots[min(i, len(time_slots) - 1)]
        events.append({
            "time": time_slot,
            "event": event,
            "importance": "high" if change_pct >= 5 else "medium",
        })

    return events[:stock_count]


def _fallback_timeline(sentiment: Dict = None) -> List[Dict]:
    """数据不足时的降级时间线"""
    if sentiment:
        mood = sentiment.get("market_mood", "")
        limit_up = sentiment.get("limit_up_count", 0)
        if limit_up >= 80:
            return [
                {"time": "09:35", "event": "开盘情绪偏高，多个方向出现抢筹", "importance": "high"},
                {"time": "10:30", "event": f"涨停数已超 {limit_up} 家，市场做多热情高涨", "importance": "medium"},
            ]
        elif limit_up < 30:
            return [
                {"time": "09:35", "event": "开盘情绪一般，资金偏谨慎", "importance": "medium"},
                {"time": "14:00", "event": "全天维持窄幅震荡，没有明确方向", "importance": "low"},
            ]

    return [
        {"time": "09:35", "event": "今日市场平稳开盘，暂无明显异动", "importance": "medium"},
        {"time": "10:30", "event": "板块轮动中，部分资金开始试探性进场", "importance": "low"},
        {"time": "14:00", "event": "尾盘资金面平稳，无明显恐慌或抢筹", "importance": "low"},
    ]