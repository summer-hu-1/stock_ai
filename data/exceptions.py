"""
异常定义 - AI Quant OS V10

统一的异常处理体系
"""


class V10ArchitectureError(Exception):
    """V10架构基础异常"""
    pass


class DataNotFoundError(V10ArchitectureError):
    """数据未找到异常"""
    pass


class DataSourceError(V10ArchitectureError):
    """数据源错误"""
    pass


class AdapterError(V10ArchitectureError):
    """适配器错误"""
    pass


class QuantCalculationError(V10ArchitectureError):
    """量化计算错误"""
    pass


class FactorError(V10ArchitectureError):
    """因子计算错误"""
    pass


class SignalError(V10ArchitectureError):
    """信号生成错误"""
    pass


class ScoreError(V10ArchitectureError):
    """评分计算错误"""
    pass


class AgentError(V10ArchitectureError):
    """Agent执行错误"""
    pass


class InterpretationError(AgentError):
    """AI解释错误"""
    pass


class ReportGenerationError(AgentError):
    """报告生成错误"""
    pass


class StrategyError(V10ArchitectureError):
    """策略执行错误"""
    pass


class PositionError(V10ArchitectureError):
    """仓位管理错误"""
    pass


class RiskControlError(V10ArchitectureError):
    """风控错误"""
    pass


class ExecutionError(V10ArchitectureError):
    """交易执行错误"""
    pass


class OrderError(ExecutionError):
    """订单错误"""
    pass


class InsufficientFundsError(OrderError):
    """资金不足"""
    pass


class InsufficientPositionError(OrderError):
    """持仓不足"""
    pass


class ValidationError(V10ArchitectureError):
    """数据验证错误"""
    pass


class ConfigError(V10ArchitectureError):
    """配置错误"""
    pass


class APIError(V10ArchitectureError):
    """API调用错误"""
    pass
