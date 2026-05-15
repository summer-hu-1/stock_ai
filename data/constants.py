"""
常量定义 - AI Quant OS V10

系统级常量定义
"""

# 架构版本
ARCHITECTURE_VERSION = "V10"
ARCHITECTURE_NAME = "AI Quant OS"

# 市场常量
MARKET_CN = "cn"
MARKET_HK = "hk"
MARKET_US = "us"

MARKET_NAMES = {
    MARKET_CN: "A股",
    MARKET_HK: "港股",
    MARKET_US: "美股",
}

# 市场状态
MARKET_STATE_UNKNOWN = "unknown"
MARKET_STATE_RALLY = "rally"           # 主升
MARKET_STATE_RECOVERY = "recovery"    # 修复
MARKET_STATE_ICEBERG = "iceberg"      # 冰点
MARKET_STATE_HIGH = "high"             # 高潮
MARKET_STATE_RETREAT = "retreat"       # 退潮

# 交易方向
SIDE_BUY = "买入"
SIDE_SELL = "卖出"
SIDE_HOLD = "持有"

# 订单类型
ORDER_TYPE_MARKET = "市价"
ORDER_TYPE_LIMIT = "限价"

# 订单状态
ORDER_STATUS_PENDING = "待成交"
ORDER_STATUS_FILLED = "已成交"
ORDER_STATUS_PARTIAL = "部分成交"
ORDER_STATUS_CANCELLED = "已撤销"
ORDER_STATUS_REJECTED = "已拒绝"

# 持仓状态
POSITION_STATUS_OPEN = "持仓中"
POSITION_STATUS_CLOSED = "已平仓"
POSITION_STATUS_PENDING = "待买入"

# 信号方向
SIGNAL_UP = "up"
SIGNAL_DOWN = "down"
SIGNAL_NEUTRAL = "neutral"

# 信号类型
SIGNAL_TYPE_BREAKOUT = "突破"
SIGNAL_TYPE_TREND = "趋势"
SIGNAL_TYPE_REVERSAL = "反转"
SIGNAL_TYPE_VOLUME = "放量"
SIGNAL_TYPE_MOMENTUM = "动量"

# 因子类型
FACTOR_TYPE_TREND = "trend"
FACTOR_TYPE_VOLUME = "volume"
FACTOR_TYPE_MOMENTUM = "momentum"
FACTOR_TYPE_VOLATILITY = "volatility"
FACTOR_TYPE_STRENGTH = "strength"

# 时间周期
PERIOD_DAILY = "daily"
PERIOD_WEEKLY = "weekly"
PERIOD_MONTHLY = "monthly"

# 板块分类
SECTORS = [
    "AI",
    "半导体",
    "新能源",
    "消费",
    "金融",
    "医药",
    "军工",
    "周期",
    "房地产",
    "基建",
]

# 数据源优先级
DATA_SOURCE_PRIORITY = {
    "memory": 1,   # 最高
    "csv": 2,
    "ashare": 3,
    "yfinance": 4,
}

# 评分权重
DEFAULT_SCORE_WEIGHTS = {
    "trend": 0.3,
    "momentum": 0.2,
    "volume": 0.2,
    "volatility": 0.15,
    "strength": 0.15,
}

# 风控参数
RISK_STOP_LOSS = 0.05       # 止损5%
RISK_TAKE_PROFIT = 0.15     # 止盈15%
RISK_MAX_POSITION = 0.3     # 单只最大仓位30%
RISK_MAX_DRAWDOWN = 0.15    # 最大回撤15%
RISK_MAX_POSITIONS = 10     # 最大持仓数量

# 交易费用
COMMISSION_RATE = 0.0003    # 手续费万3
STAMP_TAX_RATE = 0.001      # 印花税千1
SLIPPAGE_RATE = 0.001       # 滑点千1
