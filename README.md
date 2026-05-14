# AI Quant OS - AI原生量化平台 V10（核心平台）

> 基于 DeepSeek + AkShare/yfinance + 六大核心中台的智能交易分析系统
>
> **V10 核心原则**：
> 1. **六大核心中台** - DataHub / QuantCore / AgentOS / StrategyOS / ExecutionOS / App
> 2. **数据唯一入口** - DataHub 是系统唯一数据源，禁止直接读取 CSV/SQLite
> 3. **计算唯一入口** - QuantCore 是系统唯一计算引擎，禁止 AI 参与计算
> 4. **认知与计算分离** - AgentOS 只做解释，QuantCore 只做计算
> 5. **策略统一调度** - StrategyOS 统一管理仓位、风控、策略
> 6. **执行模拟化** - ExecutionOS 提供模拟交易执行

---

## 📌 版本迭代记录

### V1.0 - V5.0 基础功能
- V1.0: DeepSeek API 基础接入
- V2.0: AkShare 真实行情数据
- V3.0: 市场情绪分析
- V4.0: SQLite 历史记录系统
- V5.0: Markdown 报告 + 下载功能

### V6.0 多Agent架构
> **核心升级**：从「单Prompt AI」到「多Agent协同系统」
- **5个专业Agent**：行情Agent、情绪Agent、板块Agent、资金Agent、风险Agent
- **统一数据层**：MarketContext + DataProvider 架构
- **统一Agent输出**：score/signal/risk/reason 标准格式

### V7.0 多市场路由 + 本地日线数据中心
> **核心升级**：从「单市场」到「多市场数据路由」，同时建立「本地数据底座」
- **多市场支持**：A股、港股、美股自动路由
- **本地A股日线数据中心**：自动拉取3年日线、CSV永久存储、增量更新

### V8.x 市场记忆系统
> **核心升级**：从「单日分析」到「市场叙事分析」，赋予系统「时间记忆能力」
- **MarketStateEngine**：核心大脑（分析市场周期、情绪趋势、板块轮动、龙头切换）
- **MarketSnapshotGenerator**：每日市场快照生成器

### V9.x 信号中心 + 离线计算
> **核心升级**：从「输入股票 -> 临时分析」升级为「全市场扫描 -> 结果入库 -> 用户查询」
- **SignalScanner**：全市场信号扫描器
- **signals.db**：SQLite数据库，存储 signals、leaders、watchlist、sector_strength

### V10.0 AI Quant OS 核心平台（当前版本）✅
> **核心升级**：从「功能集合」到「统一核心平台」，建立六大核心中台架构
>
> **五大中台已完成**：
> - **DataHub（数据中台）** - 统一数据访问入口
> - **QuantCore（量化核心）** - 统一量化计算引擎
> - **AgentOS（Agent认知层）** - 统一AI解释层
> - **StrategyOS（策略中台）** - 统一策略调度层
> - **ExecutionOS（执行层）** - 统一模拟交易执行层

---

## 🏗️ V10 核心架构（六大中台）

```
                    ┌─────────────────┐
                    │   App/UI/展示层  │
                    │  (展示与交互)   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  StrategyOS     │  <- 策略中台
                    │  (策略调度)     │
                    │  • 仓位管理     │
                    │  • 风控规则     │
                    │  • 策略调度     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   AgentOS       │  <- Agent认知层
                    │  (AI解释层)     │
                    │  • 理解解释     │
                    │  • 总结生成     │
                    │  • 认知推理     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   QuantCore     │  <- 量化核心
                    │  (计算引擎)     │
                    │  • 因子引擎     │
                    │  • 信号引擎     │
                    │  • 状态引擎     │
                    │  • 评分引擎     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    DataHub      │  <- 数据中台
                    │  (数据总线)     │
                    │  • 数据获取     │
                    │  • 数据缓存     │
                    │  • 数据适配     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  ExecutionOS    │  <- 执行层
                    │  (模拟交易)     │
                    │  • 订单管理     │
                    │  • 持仓同步     │
                    │  • 账户管理     │
                    └─────────────────┘
```

### 中台职责详解

| 中台 | 英文名 | 核心职责 | 输入 | 输出 |
|------|--------|----------|------|------|
| **DataHub** | 数据中台 | 统一数据访问 | 无 | MarketData/FactorData/MarketState/SignalData |
| **QuantCore** | 量化核心 | 统一量化计算 | MarketData | FactorResult/SignalResult/StateResult/ScoreResult |
| **AgentOS** | Agent认知层 | AI解释理解 | QuantResult | AnalysisReport/TradingInsight |
| **StrategyOS** | 策略中台 | 策略调度风控 | QuantResult/AgentReport | TradeDecision |
| **ExecutionOS** | 执行层 | 模拟交易执行 | TradeDecision | ExecutionResult/AccountStatus |
| **App** | 展示层 | 用户交互展示 | 各中台输出 | UI展示 |

---

## 📊 核心数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流向图                                      │
└─────────────────────────────────────────────────────────────────────────────┘

1. 数据获取 (DataHub)
   ├── get_ohlcv_dataframe()     → 获取K线数据
   ├── get_market_state()        → 获取市场状态
   ├── get_sector_data()         → 获取板块数据
   └── get_news_data()           → 获取新闻数据

2. 量化计算 (QuantCore)
   ├── calculate_factors()       → 计算因子
   ├── generate_signals()        → 生成信号
   ├── analyze_market_state()    → 分析市场状态
   └── calculate_score()         → 综合评分

3. AI解释 (AgentOS)
   ├── analyze_stock()           → AI分析个股
   └── generate_report()         → 生成分析报告

4. 策略调度 (StrategyOS)
   ├── generate_trade_decision() → 生成交易决策
   ├── calculate_position()       → 计算仓位
   └── apply_risk_control()      → 应用风控

5. 模拟执行 (ExecutionOS)
   ├── execute_buy()             → 执行买入
   ├── execute_sell()            → 执行卖出
   └── execute_from_strategy()   → 执行策略信号
```

---

## 📁 完整代码结构 (V10)

```
stock_ai/
│
├── app.py                      # 主界面（Streamlit入口）
│
├── core/                        # 核心架构层（V10六大中台）
│   │
│   ├── datahub/                 # 数据中台（V10新增）
│   │   ├── __init__.py         # 统一入口 get_datahub()
│   │   ├── models.py           # 数据模型
│   │   ├── hub.py              # 数据总线
│   │   ├── cache.py            # 缓存层
│   │   └── adapters/           # 数据适配器
│   │       ├── __init__.py
│   │       ├── ashare_adapter.py  # A股适配器
│   │       ├── csv_adapter.py     # CSV适配器
│   │       └── memory_adapter.py  # 内存适配器
│   │
│   ├── quant_core/              # 量化核心（V10重构）
│   │   ├── __init__.py         # 统一入口 get_quant_core()
│   │   ├── models.py           # 量化模型
│   │   ├── factor_engine.py    # 因子引擎
│   │   ├── signal_engine.py    # 信号引擎
│   │   ├── state_engine.py     # 状态引擎
│   │   └── score_engine.py     # 评分引擎
│   │
│   ├── agent_os/                # Agent认知层（V10重构）
│   │   ├── __init__.py         # 统一入口 get_agent_os()
│   │   ├── models.py           # Agent模型
│   │   ├── interpreter.py      # 解释器
│   │   └── report_generator.py # 报告生成器
│   │
│   ├── strategy_os/             # 策略中台（V10新增）
│   │   ├── __init__.py         # 统一入口 get_strategy_os()
│   │   ├── models.py           # 策略模型
│   │   ├── position_manager.py # 仓位管理
│   │   ├── risk_control.py     # 风险管理
│   │   └── strategy_scheduler.py # 策略调度
│   │
│   ├── execution_os/            # 执行层（V10新增）
│   │   ├── __init__.py         # 统一入口 get_execution_os()
│   │   ├── models.py           # 执行模型
│   │   ├── order_manager.py    # 订单管理
│   │   ├── position_tracker.py # 持仓同步
│   │   └── simulation_engine.py # 模拟交易引擎
│   │
│   └── ...                      # 其他核心模块
│
├── factors/                     # 因子系统
├── signals/                     # 信号系统
├── leaders/                     # 龙头系统
├── providers/                   # 数据源
├── database/                    # 数据库
├── auth/                        # 认证
├── modules/                     # 业务模块
├── scheduler/                   # 调度器
├── signal_center/               # 信号中心
└── templates/                   # 前端模板
```

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY
```

### 3. 启动应用
```bash
cd stock_ai
streamlit run app.py
```

### 4. 使用示例

```python
from core.datahub import get_datahub
from core.quant_core import get_quant_core
from core.agent_os import get_agent_os
from core.strategy_os import get_strategy_os
from core.execution_os import get_execution_os

# 1. 数据获取
datahub = get_datahub()
market_data = datahub.get_stock("000002", "cn")

# 2. 量化分析
quant_core = get_quant_core()
quant_result = quant_core.analyze("000002", "cn")

# 3. AI 解释
agent_os = get_agent_os()
report = agent_os.analyze_stock("000002", "cn")

# 4. 策略决策
strategy_os = get_strategy_os()
decision = strategy_os.generate_trade_decision(quant_result)

# 5. 模拟执行
execution_os = get_execution_os()
result = execution_os.execute_from_strategy(decision, current_price=10.5)

# 6. 查看账户
account = execution_os.get_account()
print(f"总资产: {account.total_assets:.2f}")
print(f"累计收益: {account.profit_loss_pct:+.2f}%")
```

---

## 📈 核心 API

### DataHub（数据中台）

| 方法 | 说明 |
|------|------|
| `get_stock(code, market)` | 获取单只股票数据 |
| `get_ohlcv_dataframe(code, market)` | 获取K线DataFrame |
| `get_market_state()` | 获取市场状态 |
| `get_sector_data()` | 获取板块数据 |
| `get_news_data()` | 获取新闻数据 |

### QuantCore（量化核心）

| 方法 | 说明 |
|------|------|
| `analyze(code, market)` | 综合量化分析 |
| `calculate_factors()` | 计算因子 |
| `generate_signals()` | 生成信号 |
| `analyze_market_state()` | 分析市场状态 |
| `calculate_score()` | 综合评分 |

### AgentOS（Agent认知层）

| 方法 | 说明 |
|------|------|
| `analyze_stock(code, market)` | AI分析个股 |
| `generate_report(quant_result)` | 生成分析报告 |

### StrategyOS（策略中台）

| 方法 | 说明 |
|------|------|
| `generate_trade_decision(quant_result)` | 生成交易决策 |
| `calculate_position(quant_result)` | 计算目标仓位 |
| `apply_risk_control(trade_decision)` | 应用风控规则 |

### ExecutionOS（执行层）

| 方法 | 说明 |
|------|------|
| `execute_buy(code, quantity, price)` | 执行买入 |
| `execute_sell(code, quantity, price)` | 执行卖出 |
| `execute_from_strategy(decision, price)` | 执行策略信号 |
| `get_account()` | 获取账户信息 |
| `get_positions()` | 获取持仓信息 |

---

## ⚙️ 配置说明

### 数据源配置
```python
# 支持的数据源
- AShare: AkShare API
- CSV: 本地CSV文件
- Memory: 内存缓存
```

### 模拟交易配置
```python
# 初始资金: 100000.0
# 手续费: 万分之3
# 印花税: 千分之1（仅卖出）
# 滑点: 千分之1
```

---

## 🎯 V10 架构优势

| 优势 | 说明 |
|------|------|
| **统一性** | 所有数据必须通过 DataHub，杜绝散乱读取 |
| **独立性** | QuantCore 与 AgentOS 分离，计算与认知分离 |
| **可维护性** | 各中台职责清晰，边界明确 |
| **可扩展性** | 新增数据源只需适配 DataHub |
| **可测试性** | 各中台可独立单元测试 |
| **可复用性** | 中台可在不同场景复用 |

---

## 🔮 未来规划

- [ ] 实盘对接（券商接口）
- [ ] 回测系统
- [ ] 多策略组合
- [ ] 实时行情
- [ ] 分布式架构

---

**AI Quant OS V10 - 从「功能集合」到「统一核心平台」的蜕变** 🚀
