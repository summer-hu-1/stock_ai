"""
通用工具 - AI Quant OS V10

通用工具函数
"""

import uuid
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from copy import deepcopy


def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    uid = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{timestamp}_{uid[:8]}" if prefix else f"{timestamp}_{uid[:8]}"


def generate_order_id() -> str:
    """生成订单ID"""
    return generate_id("ORD")


def generate_trade_id() -> str:
    """生成交易ID"""
    return generate_id("TRD")


def generate_hash(text: str) -> str:
    """生成文本哈希"""
    return hashlib.md5(text.encode()).hexdigest()


def format_number(value: float, precision: int = 2) -> str:
    """格式化数字"""
    if abs(value) >= 1e8:
        return f"{value / 1e8:.2f}亿"
    elif abs(value) >= 1e4:
        return f"{value / 1e4:.2f}万"
    else:
        return f"{value:.{precision}f}"


def format_percent(value: float, precision: int = 2) -> str:
    """格式化百分比"""
    return f"{value * 100:.{precision}f}%"


def format_date(date: Union[str, datetime], fmt: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    if isinstance(date, str):
        return date
    return date.strftime(fmt)


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法"""
    return a / b if b != 0 else default


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """安全获取嵌套字典值"""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result


def merge_dicts(*dicts: Dict) -> Dict:
    """合并多个字典"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def filter_dict(data: Dict, keys: List[str]) -> Dict:
    """过滤字典，只保留指定键"""
    return {k: v for k, v in data.items() if k in keys}


def remove_none(data: Dict) -> Dict:
    """移除字典中的None值"""
    return {k: v for k, v in data.items() if v is not None}


def to_dict(obj: Any) -> Dict:
    """对象转字典"""
    if isinstance(obj, dict):
        return obj
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "__dataclass_fields__"):
        return {f.name: getattr(obj, f.name) for f in obj.__dataclass_fields__.values()}
    else:
        return {"value": obj}


def clamp(value: float, min_value: float, max_value: float) -> float:
    """限制值在范围内"""
    return max(min_value, min(max_value, value))


def round_price(price: float, precision: int = 2) -> float:
    """价格取整（A股最小价格单位）"""
    return round(price, precision)


def round_quantity(quantity: int, min_unit: int = 100) -> int:
    """数量取整（A股最小交易单位）"""
    return (quantity // min_unit) * min_unit


def is_trading_day(date: datetime = None) -> bool:
    """判断是否为交易日（简化版）"""
    if date is None:
        date = datetime.now()
    return date.weekday() < 5


def get_date_range(start_date: str, end_date: str) -> List[str]:
    """获取日期范围"""
    from datetime import timedelta
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


__all__ = [
    "generate_id",
    "generate_order_id",
    "generate_trade_id",
    "generate_hash",
    "format_number",
    "format_percent",
    "format_date",
    "safe_divide",
    "safe_get",
    "merge_dicts",
    "filter_dict",
    "remove_none",
    "to_dict",
    "clamp",
    "round_price",
    "round_quantity",
    "is_trading_day",
    "get_date_range",
    "deepcopy",
]
