"""
统一日志配置

为整个系统提供统一的日志记录机制，替换分散的 print 语句

日志级别：
- DEBUG: 详细的调试信息
- INFO: 一般信息
- WARNING: 警告信息（非致命问题）
- ERROR: 错误信息（需要关注）
- CRITICAL: 严重错误（系统可能崩溃）

使用方式：
    from core.logging_config import get_logger
    
    logger = get_logger(__name__)
    logger.info("正常操作")
    logger.warning("需要关注")
    logger.error("发生错误")
"""

import logging
import sys
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    配置全局日志系统
    
    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_file: 日志文件路径（None表示不输出到文件）
        enable_console: 是否输出到控制台
    """
    # 获取日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建日志格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除已存在的处理器（避免重复）
    root_logger.handlers = []
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常使用 __name__
    
    Returns:
        Logger: 配置好的日志器实例
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    装饰器：记录函数调用和返回
    
    使用方式：
        @log_function_call
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}")
            raise
    
    return wrapper


def log_execution_time(func):
    """
    装饰器：记录函数执行时间
    
    使用方式：
        @log_execution_time
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        result = func(*args, **kwargs)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"函数 {func.__name__} 执行耗时: {elapsed:.2f}秒")
        
        return result
    
    return wrapper


# 自动配置日志
setup_logging(
    level="INFO",
    log_file="logs/analysis.log"
)
