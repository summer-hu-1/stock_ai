#!/usr/bin/env python3
"""
模型配置管理模块
支持动态切换不同的DeepSeek模型
"""

from typing import List, Dict, Optional

# 模型配置列表
MODEL_CONFIGS = [
    {
        "name": "deepseek-chat",
        "display_name": "标准模型",
        "description": "平衡性能与速度",
        "price_per_1k_tokens": {
            "prompt": 0.0015,
            "completion": 0.002
        },
        "max_tokens": 4096,
        "recommended": True
    },
    {
        "name": "deepseek-v4",
        "display_name": "V4 模型",
        "description": "更强的推理能力",
        "price_per_1k_tokens": {
            "prompt": 0.003,
            "completion": 0.004
        },
        "max_tokens": 8192,
        "recommended": False
    },
    {
        "name": "deepseek-v4-flash",
        "display_name": "V4 Flash",
        "description": "更快更便宜",
        "price_per_1k_tokens": {
            "prompt": 0.00075,
            "completion": 0.001
        },
        "max_tokens": 8192,
        "recommended": False
    }
]

# 当前使用的模型（可被动态修改）
_current_model: str = "deepseek-chat"


def get_model_config(model_name: str) -> Optional[Dict]:
    """获取指定模型的配置信息"""
    for config in MODEL_CONFIGS:
        if config["name"] == model_name:
            return config
    return None


def get_all_models() -> List[Dict]:
    """获取所有可用模型列表"""
    return MODEL_CONFIGS


def get_current_model() -> str:
    """获取当前使用的模型名称"""
    return _current_model


def set_current_model(model_name: str) -> bool:
    """
    设置当前使用的模型
    
    Args:
        model_name: 模型名称
        
    Returns:
        bool: 是否设置成功
    """
    global _current_model
    if get_model_config(model_name):
        _current_model = model_name
        return True
    return False


def format_price_info(config: Dict) -> str:
    """格式化价格信息显示"""
    prompt_price = config["price_per_1k_tokens"]["prompt"]
    completion_price = config["price_per_1k_tokens"]["completion"]
    return f"💵 输入 ¥{prompt_price}/千token | 输出 ¥{completion_price}/千token"


def get_model_display_name(model_name: str) -> str:
    """获取模型的显示名称"""
    config = get_model_config(model_name)
    return config["display_name"] if config else model_name


def get_model_description(model_name: str) -> str:
    """获取模型的描述信息"""
    config = get_model_config(model_name)
    return config["description"] if config else ""


def get_model_price_info(model_name: str) -> str:
    """获取模型的价格信息"""
    config = get_model_config(model_name)
    return format_price_info(config) if config else ""
