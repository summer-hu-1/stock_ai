# AI Quant OS - AI原生量化平台 V10.2（数据中台版）

> 基于 DeepSeek + AkShare/yfinance + 5层简洁架构 + 数据中台的智能交易分析系统

**V10.2 核心原则**：
1. **5层简洁架构** - 数据/量化/策略/服务/界面
2. **数据唯一入口** - DataHub 是系统唯一数据源
3. **计算唯一入口** - QuantCore 是系统唯一计算引擎
4. **认知与计算分离** - 服务层做解释，量化层做计算
5. **策略统一调度** - StrategyOS 统一管理仓位、风控、执行
6. **数据中台** - DataLake + FeatureStore + 离线计算引擎

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

### V10.1 简洁架构
> **核心升级**：从「8层复杂架构」简化为「5层简洁架构」，职责更清晰
>
> **5层架构**：
> - **数据层** - 数据获取 + 缓存 + 基础设施
> - **量化层** - 因子 + 信号 + 状态 + 评分
> - **策略层** - 策略调度 + 风控 + 模拟执行
> - **服务层** - 业务聚合 + AI解释
> - **界面层** - 用户交互 + 数据展示

### V10.2 数据中台（当前版本）✅
> **核心升级**：在 V10.1 基础上，建立真正的数据中台：
> - **DataLake** - Parquet格式，海量K线高效存储
> - **FeatureStore** - SQLite特征库，量化结果固化
> - **SnapshotEngine** - 离线计算引擎，每晚定时执行
> - **Scheduler** - 定时调度器

---

## 🏗️ V10.2 数据中台架构

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
│  • SnapshotEngine（离线计算）                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据中台 (Data)                              │
│  • DataLake - Parquet K线存储                                  │
│  • FeatureStore - SQLite特征存储                               │
│  • 配置/常量/工具                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 核心数据流

### 传统流程（V10.1）
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

### 优化流程（V10.2）
```
每晚离线执行 (Schedule):
├─ 18:00 更新行情 → DataLake (Parquet)
├─ 18:30 计算因子 → factor_snapshot
├─ 19:00 生成信号 → signal_snapshot
├─ 20:00 市场状态 → market_state
└─ 20:30 完整快照 → 所有FeatureStore表

用户实时查询:
└─ 直接读取 FeatureStore 快照 → 无需重新计算
```

---

## 📁 完整代码结构 (V10.2)

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
├── data_lake/                  # 数据湖（新增核心）
│   ├── __init__.py             # DataLake 核心类
│   ├── cn/daily/               # A股日线
│   ├── cn/minute/              # A股分钟线
│   ├── hk/                     # 港股
│   └── us/                     # 美股
│
├── database/                   # 数据库
│   ├── __init__.py
│   ├── db.py                   # 旧版认证数据库
│   └── market_db.py            # 新版统一数据库（新增核心）
│
├── quant/                      # 量化层（第2层）
│   ├── __init__.py
│   ├── engine.py               # QuantCore - 主引擎
│   ├── snapshot_engine.py      # 快照引擎（新增核心）
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
├── scheduler/                  # 调度器（新增）
│   ├── __init__.py
│   └── quant_scheduler.py      # 定时任务调度
│
├── ui/                         # 界面层（第5层）
│   ├── __init__.py
│   ├── components.py           # UI组件
│   └── pages/                  # 页面
│
├── auth/                       # 认证模块
├── modules/                    # 业务模块
├── signal_center/              # 信号中心
└── templates/                  # 前端模板
```

---

## 🗄️ 数据中台详解

### 1. DataLake（数据湖）- Parquet存储

```
data_lake/
├── cn/
│   ├── daily/              # 日线数据
│   │   ├── 000001.parquet
│   │   └── ...
│   └── minute/             # 分钟数据
├── hk/
└── us/
```

**优势**：
| 特性 | 说明 |
|------|------|
| 超轻量 | 比CSV小50%+ |
| 超快查询 | 列式存储，支持谓词下推 |
| pandas原生 | pyarrow直接读取 |
| AI友好 | 机器学习天然支持 |

### 2. FeatureStore（特征存储）- SQLite

| 表名 | 层级 | 用途 |
|------|------|------|
| `daily_bars` | 事实层 | 原始每日K线 |
| `factor_snapshot` | 计算层 | 因子得分（趋势/动量/量能/波动率） |
| `signal_snapshot` | 计算层 | 信号（突破/反转/主升/放量） |
| `market_state` | 计算层 | 市场周期/情绪/热点/风险 |
| `sector_strength` | 计算层 | 板块强度 |
| `leader_snapshot` | 计算层 | 龙头股识别 |
| `stock_score` | 计算层 | 综合评分/交易信号 |
| `positions` | 行为层 | 持仓记录 |
| `orders` | 行为层 | 订单记录 |
| `trades` | 行为层 | 交易记录 |
| `watchlist` | 行为层 | 自选股 |

### 3. 核心表结构

#### daily_bars（事实层）
```sql
CREATE TABLE daily_bars (
    code TEXT,
    market TEXT,
    date TEXT,
    open REAL, high REAL, low REAL, close REAL,
    volume REAL, amount REAL,
    PRIMARY KEY(code, date)
)
```

#### factor_snapshot（计算层）
```sql
CREATE TABLE factor_snapshot (
    code TEXT,
    date TEXT,
    trend_score REAL,
    momentum_score REAL,
    volume_score REAL,
    volatility_score REAL,
    strength_score REAL,
    total_score REAL,
    PRIMARY KEY(code, date)
)
```

#### market_state（AI大脑）
```sql
CREATE TABLE market_state (
    date TEXT PRIMARY KEY,
    market_cycle TEXT,
    sentiment_score REAL,
    risk_level TEXT,
    hot_sector TEXT,
    limit_up_count INTEGER,
    limit_down_count INTEGER
)
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

### 4. 启动调度器（离线计算）
```bash
python -m scheduler.quant_scheduler --start
```

### 5. 手动运行一次快照（测试）
```bash
python -m scheduler.quant_scheduler --run-once
```

### 6. 功能标签页说明

系统提供 **9个功能标签页**，充分展示5层架构能力：

| 序号 | 标签页 | 核心功能 | 对应层级 |
|------|--------|----------|----------|
| 1 | ⚡ 单Prompt分析 | 快速股票分析入口 | Services |
| 2 | 🧠 多Agent分析 | 多角度完整分析 | Services |
| 3 | 📊 量化分析 | QuantCore因子/信号/评分 | **Quant** |
| 4 | 🤖 AI分析 | AgentOS智能报告生成 | **Services** |
| 5 | ⚙️ 策略执行 | 模拟买卖/持仓管理 | **Strategy** |
| 6 | 📡 信号扫描 | 全市场信号扫描 | Services |
| 7 | 📊 各Agent详情 | 各Agent分析结果 | Services |
| 8 | 📈 历史记录 | 历史分析记录 | UI |
| 9 | 📅 情绪周期 | 市场情绪趋势 | Services |

### 7. 核心使用示例

```python
from data import get_datahub
from quant import get_quant_core
from strategy import get_strategy_os
from services import get_analysis_service, get_agent_os
from data_lake import get_data_lake
from quant.snapshot_engine import get_snapshot_engine

# 1. DataLake 数据获取 (V10.2 新增)
data_lake = get_data_lake()
df = data_lake.load_daily_data("000002", "cn")

# 2. 读取量化快照 (V10.2 新增，无需实时计算)
snapshot = get_snapshot_engine()
factor_data = snapshot.get_latest_factor_snapshot("000002")
market_state = snapshot.get_latest_market_state()

# 3. QuantCore 量化分析 (兼容V10.1)
quant = get_quant_core()
result = quant.analyze("000002", "cn")

# 4. 策略决策
strategy = get_strategy_os()
decision = strategy.generate_trade_decision(result)

# 5. AI解释
agent = get_agent_os()
report = agent.analyze_stock("000002", "cn")

# 6. 模拟执行
if decision.action == "买入":
    strategy.execute_buy(
        code="000002",
        quantity=1000,
        price=25.5
    )

# 7. 查看账户
account = strategy.get_account()
print(f"总资产: {account.total_assets:.2f}")
print(f"收益: {account.profit_loss_pct:+.2f}%")
```

---

## ⏰ 离线计算调度

| 时间 | 任务 | 输出 |
|------|------|------|
| 18:00 | `update_market_data()` | DataLake |
| 18:30 | `calculate_factors()` | factor_snapshot |
| 19:00 | `generate_signals()` | signal_snapshot |
| 20:00 | `generate_market_state()` | market_state |
| 20:30 | `generate_complete_snapshot()` | 所有表 |
| 00:00 | `reset_daily_quota()` | 用户配额重置 |

---

## 🎯 QuantCore 量化能力

QuantCore 是系统唯一计算引擎，负责所有数学计算：

### 因子计算
- **趋势得分**：判断股票趋势方向
- **动量得分**：衡量价格上涨/下跌的加速度
- **量能得分**：分析成交量变化
- **波动率得分**：评估价格波动程度
- **强度得分**：相对强弱指标
- **龙头加分**：是否为龙头股
- **市场调整**：根据市场状态调整评分

### 信号生成
- 突破信号、反转信号、主升信号、放量信号

### 市场状态
- 市场周期分析（上升/下降/震荡）
- 情绪得分、情绪趋势
- 涨停/跌停家数统计
- 热门板块识别

---

## 🤖 AgentOS AI认知能力

AgentOS 是系统的AI认知层，负责理解和解释QuantCore的量化结果：

- 接收 QuantResult 原始数据
- 生成专业分析报告
- 提供具体操作建议
- 风险收益分析
- 明日走势预测

---

## ⚙️ StrategyOS 策略执行能力

StrategyOS 负责策略调度和模拟交易执行：

- **账户管理**：初始资金 ¥100,000，支持实时盈亏计算
- **持仓管理**：买入/卖出/持仓查询
- **交易记录**：完整交易历史追溯
- **费用计算**：手续费（万分之3）+ 印花税（千分之1）+ 滑点（千分之1）

---

## 📈 核心 API

### 数据层 (Data)

| 方法 | 说明 |
|------|------|
| `get_datahub().get_ohlcv_dataframe(code, market)` | 获取K线数据 |
| `get_datahub().get_market_state()` | 获取市场状态 |
| `get_datahub().get_sector_data()` | 获取板块数据 |

### DataLake (V10.2 新增)

| 方法 | 说明 |
|------|------|
| `get_data_lake().save_daily_data(code, market, df)` | 保存日线到Parquet |
| `get_data_lake().load_daily_data(code, market, start, end)` | 从Parquet加载日线 |
| `get_data_lake().list_stocks(market, freq)` | 列出市场股票 |

### SnapshotEngine (V10.2 新增)

| 方法 | 说明 |
|------|------|
| `get_snapshot_engine().generate_daily_snapshot(date)` | 生成每日量化快照 |
| `get_snapshot_engine().get_latest_factor_snapshot(code)` | 读取最新因子快照 |
| `get_snapshot_engine().get_latest_market_state()` | 读取最新市场状态 |
| `get_snapshot_engine().get_top_stocks_by_score(date, limit)` | 获取高分股票列表 |

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
- Parquet: DataLake (V10.2 新增)
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

## 🎯 V10.2 架构优势

| 优势 | 说明 |
|------|------|
| **简洁** | 5层架构，清晰易懂 |
| **独立** | 每层职责单一，边界明确 |
| **可维护** | 修改一层不影响其他层 |
| **可测试** | 每层可独立单元测试 |
| **可扩展** | 新增功能只需扩展对应层 |
| **职责清晰** | 数据/计算/行为三层分离 |
| **可重算** | 因子可重新计算，历史结果不污染 |
| **高性能** | Parquet + SQLite 轻量化方案 |
| **无重复计算** | 用户访问直接读快照 |

---

## 🔮 未来规划

- [x] 数据中台搭建（DataLake + FeatureStore）
- [x] 离线计算引擎（SnapshotEngine）
- [x] 定时调度器
- [ ] 回测系统
- [ ] 多策略组合
- [ ] 实时行情
- [ ] 实盘对接（券商接口）
- [ ] 分布式架构

---

## 📚 相关文档

- [架构文档](ARCHITECTURE.md) - V10.1 架构详细说明
- [数据中台说明](DATA_LAKE.md) - DataLake + FeatureStore 架构说明
- [使用指南](GUIDE.md) - 使用指南和最佳实践
- [市场记忆](MARKET_MEMORY_SUMMARY.md) - 市场记忆系统说明

---

**AI Quant OS V10.2 - 数据中台架构，量化核心** 🚀