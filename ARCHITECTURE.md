# V10 架构文档（简化版）

> AI Quant OS 核心架构 - 5层简洁架构

---

## 核心原则

1. **分层清晰** - 数据/量化/策略/服务/界面 5层分离
2. **单向依赖** - 上层依赖下层，禁止反向依赖
3. **单一职责** - 每层只做一件事，做好一件事
4. **认知与计算分离** - 服务层做解释，量化层做计算

---

## 5层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      界面层 (UI)                                │
│  • 用户交互                                                     │
│  • 数据展示                                                     │
│  • 组件复用                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    服务层 (Services)                            │
│  • 业务逻辑聚合                                                 │
│  • AI解释（Agent）                                              │
│  • 数据服务                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    策略层 (Strategy)                            │
│  • 策略调度                                                     │
│  • 风险控制                                                     │
│  • 模拟执行                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    量化层 (Quant)                                │
│  • 因子计算                                                     │
│  • 信号生成                                                     │
│  • 市场状态                                                     │
│  • 综合评分                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据层 (Data)                                │
│  • 数据获取                                                     │
│  • 数据缓存                                                     │
│  • 基础设施（配置/常量/异常/工具）                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
stock_ai/
│
├── data/                    # 数据层（第1层）
│   ├── __init__.py
│   ├── hub.py              # DataHub - 数据总线
│   ├── cache.py            # 数据缓存
│   ├── models.py           # 数据模型
│   ├── config.py           # 配置管理
│   ├── constants.py        # 系统常量
│   ├── exceptions.py       # 异常定义
│   ├── utils.py            # 工具函数
│   └── adapters/           # 数据适配器
│       ├── csv_adapter.py
│       └── ashare_adapter.py
│
├── quant/                   # 量化层（第2层）
│   ├── __init__.py
│   ├── engine.py           # QuantCore - 主引擎
│   ├── factor/             # 因子计算
│   │   └── engine.py
│   ├── signal/             # 信号生成
│   │   └── engine.py
│   ├── state/              # 市场状态
│   │   └── engine.py
│   └── score/              # 综合评分
│       └── engine.py
│
├── strategy/               # 策略层（第3层）
│   ├── __init__.py
│   ├── engine.py           # StrategyOS - 策略引擎
│   ├── models.py           # 策略模型
│   ├── position_manager.py # 仓位管理
│   ├── risk_manager.py      # 风险管理
│   └── simulation.py       # 模拟交易
│
├── services/               # 服务层（第4层）
│   ├── __init__.py
│   ├── analysis_service.py # 分析服务
│   ├── market_service.py   # 市场服务
│   ├── signal_service.py   # 信号服务
│   ├── agent/              # Agent解释
│   │   ├── __init__.py
│   │   ├── interpreter.py  # 解释器
│   │   └── models.py
│   └── report_service.py   # 报告服务
│
├── ui/                     # 界面层（第5层）
│   ├── __init__.py
│   ├── components.py       # UI组件
│   └── pages/              # 页面
│
├── app.py                  # 主入口
├── auth/                   # 认证模块
├── database/               # 数据库
└── modules/                # 业务模块
```

---

## 各层职责

### 第1层：数据层 (Data)

**职责**：数据获取、缓存、基础设施

**核心模块**：
- `DataHub` - 数据总线，统一数据入口
- `Cache` - 数据缓存，提升性能
- `Adapters` - 数据适配器，支持多数据源
- `Config/Constants/Exceptions/Utils` - 基础设施

**关键方法**：
```python
get_datahub().get_ohlcv_dataframe(code, market)
get_datahub().get_market_state()
get_datahub().get_sector_data()
```

**约束**：
- 只负责数据获取和缓存
- 不做任何计算
- 不依赖任何上层

---

### 第2层：量化层 (Quant)

**职责**：量化计算、因子、信号、评分

**核心模块**：
- `QuantCore` - 量化主引擎
- `FactorEngine` - 因子计算（趋势、量能、动量、波动、强度）
- `SignalEngine` - 信号生成（突破、趋势、反转、量能）
- `StateEngine` - 市场状态（冰点、修复、主升、高潮、退潮）
- `ScoreEngine` - 综合评分

**关键方法**：
```python
get_quant_core().analyze(code, market)
get_quant_core().calculate_factors(df)
get_quant_core().generate_signals(df)
get_quant_core().analyze_market_state(df)
get_quant_core().calculate_score(factors, signals, state)
```

**约束**：
- 只做数学计算
- 不使用AI
- 不做解释

---

### 第3层：策略层 (Strategy)

**职责**：策略调度、风控、模拟执行

**核心模块**：
- `StrategyOS` - 策略引擎
- `PositionManager` - 仓位管理
- `RiskManager` - 风险控制
- `SimulationEngine` - 模拟交易

**关键方法**：
```python
get_strategy_os().generate_trade_decision(quant_result)
get_strategy_os().calculate_position(quant_result)
get_strategy_os().apply_risk_control(decision)
get_strategy_os().execute_buy(code, quantity, price)
get_strategy_os().execute_sell(code, quantity, price)
```

**约束**：
- 只做策略决策和执行
- 不做量化计算
- 不做AI解释

---

### 第4层：服务层 (Services)

**职责**：业务逻辑聚合、AI解释

**核心模块**：
- `AnalysisService` - 分析服务
- `MarketService` - 市场服务
- `SignalService` - 信号服务
- `AgentOS` - AI解释器
- `ReportService` - 报告服务

**关键方法**：
```python
get_analysis_service().analyze_stock(code, market, with_report=True)
get_market_service().get_market_context(days=5)
get_agent_os().analyze_stock(code, market)
get_agent_os().generate_report(quant_result)
```

**约束**：
- 聚合下层能力
- 提供业务接口
- AI只做解释，不做计算

---

### 第5层：界面层 (UI)

**职责**：用户交互、数据展示

**核心模块**：
- `Components` - UI组件
- `Pages` - 页面
- `app.py` - 主入口

**关键方法**：
```python
ui.stock_selector_with_market()
ui.display_analysis_result(result)
ui.display_chart(data)
```

**约束**：
- 只做展示和交互
- 不做业务逻辑
- 不做数据处理

---

## 数据流

```
1. 数据获取 (数据层)
   DataHub.get_ohlcv_dataframe(code, market) → pd.DataFrame

2. 量化计算 (量化层)
   QuantCore.analyze(code, market) → QuantResult
   {
       "factors": {...},
       "signals": {...},
       "state": {...},
       "score": 0.75
   }

3. 策略决策 (策略层)
   StrategyOS.generate_trade_decision(quant_result) → TradeDecision
   {
       "action": "买入",
       "target_position": 0.3,
       "stop_loss": 0.95,
       "take_profit": 1.15
   }

4. AI解释 (服务层)
   AgentOS.analyze_stock(code, market) → str (报告)
   AgentOS.generate_report(quant_result) → str (洞察)

5. 模拟执行 (策略层)
   StrategyOS.execute_buy(code, quantity, price) → ExecutionResult

6. 用户展示 (界面层)
   UI.display_analysis_result(result)
```

---

## 使用示例

```python
# V10 简化架构使用示例

from data import get_datahub
from quant import get_quant_core
from strategy import get_strategy_os
from services import get_analysis_service, get_agent_os

# 1. 数据获取
datahub = get_datahub()
df = datahub.get_ohlcv_dataframe("000002", "cn")

# 2. 量化分析
quant = get_quant_core()
result = quant.analyze("000002", "cn")

# 3. 策略决策
strategy = get_strategy_os()
decision = strategy.generate_trade_decision(result)

# 4. AI解释
agent = get_agent_os()
report = agent.analyze_stock("000002", "cn")

# 5. 模拟执行
if decision.action == "买入":
    strategy.execute_buy(
        code="000002",
        quantity=1000,
        price=25.5
    )

# 6. 查看账户
account = strategy.get_account()
print(f"总资产: {account.total_assets:.2f}")
print(f"收益: {account.profit_loss_pct:+.2f}%")
```

---

## 架构优势

| 优势 | 说明 |
|------|------|
| **简洁** | 5层架构，清晰易懂 |
| **独立** | 每层职责单一，边界明确 |
| **可维护** | 修改一层不影响其他层 |
| **可测试** | 每层可独立单元测试 |
| **可扩展** | 新增功能只需扩展对应层 |

---

## 核心约束

1. **禁止在量化层使用AI** - 只做数学计算
2. **禁止在服务层做计算** - 只做解释和聚合
3. **禁止跨层直接调用** - 必须通过相邻层
4. **禁止循环依赖** - 数据层不能依赖任何上层

---

## 版本历史

| 版本 | 架构 | 说明 |
|------|------|------|
| V9 | 6层 | Pipeline + Service + Agent |
| V10 | 8层 | 核心/数据/量化/Agent/服务/界面/执行/策略 |
| V10.1 | 5层 | 数据/量化/策略/服务/界面（当前） |

---

**V10.1 - 简洁架构，清晰职责** 🚀
