"""
Core Datahub - 向后兼容模块

V10.1 已将 DataHub 移至 data.hub
此模块保留用于向后兼容
"""

from data.hub import DataHub, get_datahub

__all__ = ["DataHub", "get_datahub"]
