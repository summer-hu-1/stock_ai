"""
Core QuantCore - 向后兼容模块

V10.1 已将 QuantCore 移至 quant
此模块保留用于向后兼容
"""

from quant import QuantCore, get_quant_core
from quant.models import QuantResult, FactorResult, SignalResult, ScoreResult

__all__ = [
    "QuantCore",
    "get_quant_core",
    "QuantResult",
    "FactorResult",
    "SignalResult",
    "ScoreResult",
]
