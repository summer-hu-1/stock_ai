# AI Quant OS - AI原生量化平台 V10.1（简洁架构版）

> 基于 DeepSeek + AkShare/yfinance + 5层简洁架构的智能交易分析系统

**V10.1 核心原则**：
1. **5层简洁架构** - 数据/量化/策略/服务/界面
2. **数据唯一入口** - DataHub 是系统唯一数据源
3. **计算唯一入口** - QuantCore 是系统唯一计算引擎
4. **认知与计算分离** - 服务层做解释，量化层做计算
5. **策略统一调度** - StrategyOS 统一管理仓位、风控、执行

---

## 📌 版本迭代记录

### V1.0 - V5.0 基础功能
- V1.0: DeepSeek API 基础接入
- V2.0: AkShare 真实行情数据
- V3.0: 市场情绪分析
- V4.0: SQLite 历史记录系统
- V5.0: Markdown 报告 + 下载功能

### V6.0 多Agent架构
- **5个专业Agent**：行情Agent、情绪Agent、板块Agent、资金Agent、风险Agent
- **统一数据层**：MarketContext + DataProvider 架构

### V7.0 多市场路由 + 本地日线数据中心
- **多市场支持**：A股、港股、美股自动路由
- **本地A股日线数据中心**：自动拉取3年日线、CSV永久存储、增量更新

### V8.x 市场记忆系统
- **MarketStateEngine**：核心大脑（分析市场周期、情绪趋势、板块轮动、龙头切换）
- **MarketSnapshotGenerator**：每日市场快照生成器

### V9.x 信号中心 + 离线计算
- **SignalScanner**：全市场信号扫描器
- **signals.db**：SQLite数据库，存储 signals、leaders、watchlist、sector_strength

### V10.0 AI Quant OS 核心平台
- **6大中台架构**：DataHub / QuantCore / AgentOS / StrategyOS / ExecutionOS / App
- **分层清晰**：核心/数据/量化/Agent/服务/界面/执行/策略 八层分离

### V10.1 简洁架构（当前版本）✅
> **核心升级**：从「8层复杂架构」简化为「5层简洁架构」，职责更清晰
>
> **5层架构**：
> - **数据层** - 数据获取 + 缓存 + 基础设施
> - **量化层** - 因子 + 信号 + 状态 + 评分
> - **策略层** - 策略调度 + 风控 + 模拟执行
> - **服务层** - 业务聚合 + AI解释
> - **界面层** - 用户交互 + 数据展示

---

## 🏗️ V10.1 简洁架构

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

## 📊 核心数据流

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

## 📁 完整代码结构 (V10.1)

```
stock_ai/
│
├── app.py                      # 主界面（Streamlit入口）
│
├── data/                       # 数据层（第1层）
│   ├── __init__.py
│   ├── hub.py                  # DataHub - 数据总线
│   ├── cache.py                # 数据缓存
│   ├── models.py               # 数据模型
│   ├── config.py               # 配置管理
│   ├── constants.py            # 系统常量
│   ├── exceptions.py           # 异常定义
│   ├── utils.py                # 工具函数
│   └── adapters/               # 数据适配器
│       ├── csv_adapter.py
│       └── ashare_adapter.py
│
├── quant/                      # 量化层（第2层）
│   ├── __init__.py
│   ├── engine.py               # QuantCore - 主引擎
│   ├── factor/                 # 因子计算
│   │   └── engine.py
│   ├── signal/                 # 信号生成
│   │   └── engine.py
│   ├── state/                  # 市场状态
│   │   └── engine.py
│   └── score/                  # 综合评分
│       └── engine.py
│
├── strategy/                   # 策略层（第3层）
│   ├── __init__.py
│   ├── engine.py               # StrategyOS - 策略引擎
│   ├── models.py               # 策略模型
│   ├── position_manager.py     # 仓位管理
│   ├── risk_manager.py          # 风险管理
│   ├── simulation.py           # 模拟交易
│   └── execution_os/           # 执行引擎
│       ├── models.py
│       ├── order_manager.py
│       ├── position_tracker.py
│       └── simulation_engine.py
│
├── services/                   # 服务层（第4层）
│   ├── __init__.py
│   ├── analysis_service.py     # 分析服务
│   ├── market_service.py       # 市场服务
│   ├── signal_service.py       # 信号服务
│   ├── report_service.py       # 报告服务
│   └── agent/                  # Agent解释
│       ├── __init__.py
│       ├── interpreter.py      # 解释器
│       └── models.py
│
├── ui/                         # 界面层（第5层）
│   ├── __init__.py
│   ├── components.py           # UI组件
│   └── pages/                  # 页面
│
├── auth/                       # 认证模块
├── database/                   # 数据库
├── modules/                    # 业务模块
├── scheduler/                  # 调度器
├── signal_center/              # 信号中心
└── templates/                  # 前端模板
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

## 📈 核心 API

### 数据层 (Data)

| 方法 | 说明 |
|------|------|
| `get_datahub().get_ohlcv_dataframe(code, market)` | 获取K线数据 |
| `get_datahub().get_market_state()` | 获取市场状态 |
| `get_datahub().get_sector_data()` | 获取板块数据 |

### 量化层 (Quant)

| 方法 | 说明 |
|------|------|
| `get_quant_core().analyze(code, market)` | 综合量化分析 |
| `get_quant_core().calculate_factors(df)` | 计算因子 |
| `get_quant_core().generate_signals(df)` | 生成信号 |
| `get_quant_core().analyze_market_state(df)` | 分析市场状态 |
| `get_quant_core().calculate_score(factors, signals, state)` | 综合评分 |

### 策略层 (Strategy)

| 方法 | 说明 |
|------|------|
| `get_strategy_os().generate_trade_decision(quant_result)` | 生成交易决策 |
| `get_strategy_os().calculate_position(quant_result)` | 计算目标仓位 |
| `get_strategy_os().apply_risk_control(decision)` | 应用风控规则 |
| `get_strategy_os().execute_buy(code, quantity, price)` | 执行买入 |
| `get_strategy_os().execute_sell(code, quantity, price)` | 执行卖出 |
| `get_strategy_os().get_account()` | 获取账户信息 |

### 服务层 (Services)

| 方法 | 说明 |
|------|------|
| `get_analysis_service().analyze_stock(code, market, with_report=True)` | 分析股票 |
| `get_market_service().get_market_context(days=5)` | 获取市场上下文 |
| `get_agent_os().analyze_stock(code, market)` | AI分析个股 |
| `get_agent_os().generate_report(quant_result)` | 生成分析报告 |

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

## 🎯 V10.1 架构优势

| 优势 | 说明 |
|------|------|
| **简洁** | 5层架构，清晰易懂 |
| **独立** | 每层职责单一，边界明确 |
| **可维护** | 修改一层不影响其他层 |
| **可测试** | 每层可独立单元测试 |
| **可扩展** | 新增功能只需扩展对应层 |

---

## 🔮 未来规划

- [ ] 实盘对接（券商接口）
- [ ] 回测系统
- [ ] 多策略组合
- [ ] 实时行情
- [ ] 分布式架构

---

## 📚 相关文档

- [架构文档](ARCHITECTURE.md) - V10.1 架构详细说明
- [使用指南](GUIDE.md) - 使用指南和最佳实践
- [市场记忆](MARKET_MEMORY_SUMMARY.md) - 市场记忆系统说明

---

**AI Quant OS V10.1 - 简洁架构，清晰职责** 🚀
