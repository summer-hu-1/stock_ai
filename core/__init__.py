"""
AI Quant OS - 核心基础层（V10.1）

注意：V10.1 已将基础设施模块移至 data/ 层
此模块保留用于向后兼容
"""

__version__ = "10.1.0"
__architecture__ = "V10.1"

from data.config import Config, get_config
from data.constants import *
from data.exceptions import *
from data.utils import *

__all__ = [
    "Config",
    "get_config",
    "V10ArchitectureError",
    "DataNotFoundError",
    "ValidationError",
    "deepcopy",
    "generate_id",
    "format_number",
]
