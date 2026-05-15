"""
Core QuantCore Models - 向后兼容模块

V10.1 已将 QuantCore Models 移至 quant.models
此模块保留用于向后兼容
"""

from quant.models import QuantResult, FactorResult, SignalResult, ScoreResult

__all__ = ["QuantResult", "FactorResult", "SignalResult", "ScoreResult"]
