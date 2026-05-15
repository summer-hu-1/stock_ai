"""
配置管理 - AI Quant OS V10

统一配置管理，支持环境变量和配置文件
"""

import os
from typing import Optional, Dict, Any


class Config:
    """配置管理类"""

    def __init__(self):
        self._config = self._load_default_config()
        self._load_from_env()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            # 项目路径
            "project_dir": os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"),
            "storage_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage"),

            # DataHub配置
            "datahub": {
                "cache_enabled": True,
                "cache_ttl": 300,  # 5分钟
                "default_adapter": "csv",  # csv/ashare/memory
            },

            # QuantCore配置
            "quant_core": {
                "factor_window": 20,
                "signal_threshold": 0.6,
                "score_weights": {
                    "trend": 0.3,
                    "momentum": 0.2,
                    "volume": 0.2,
                    "volatility": 0.15,
                    "strength": 0.15,
                }
            },

            # AgentOS配置
            "agent_os": {
                "model": "deepseek",
                "temperature": 0.7,
                "max_tokens": 2000,
            },

            # StrategyOS配置
            "strategy_os": {
                "max_position": 0.3,  # 单只最大仓位30%
                "stop_loss": 0.05,    # 止损5%
                "max_drawdown": 0.15, # 最大回撤15%
            },

            # ExecutionOS配置
            "execution_os": {
                "initial_capital": 100000.0,
                "commission_rate": 0.0003,  # 万3
                "stamp_tax_rate": 0.001,    # 千1
                "slippage_rate": 0.001,     # 千1
            },

            # 数据库配置
            "database": {
                "signals_db": "storage/sqlite/signals.db",
                "stocks_db": "storage/sqlite/stocks.db",
            },

            # API配置
            "api": {
                "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "deepseek_base_url": "https://api.deepseek.com",
            }
        }

    def _load_from_env(self):
        """从环境变量加载配置"""
        if os.getenv("DEEPSEEK_API_KEY"):
            self._config["api"]["deepseek_api_key"] = os.getenv("DEEPSEEK_API_KEY")

        if os.getenv("INITIAL_CAPITAL"):
            self._config["execution_os"]["initial_capital"] = float(os.getenv("INITIAL_CAPITAL"))

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """获取全部配置"""
        return self._config.copy()


_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取配置单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
