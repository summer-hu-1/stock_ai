# AI Quant OS - 数据中台架构说明

> 本文档说明 V10.1 向 V10.2 数据中台架构的升级内容

---

## 📌 数据中台核心升级说明

### V10.2 数据中台（待集成）

> **核心升级**：在 V10.1 简洁架构基础上，建立真正的数据中台，实现：
> - DataLake（Parquet K线存储）
> - FeatureStore（SQLite特征存储）
> - 离线计算引擎（每晚定时执行）

---

## 🗄️ 数据中台架构

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

## 📁 新增代码文件

```
stock_ai/
│
├── data_lake/                  # 数据湖（新增核心）
│   ├── __init__.py             # DataLake 核心类
│   ├── cn/daily/               # A股日线
│   ├── cn/minute/              # A股分钟线
│   ├── hk/                     # 港股
│   └── us/                     # 美股
│
├── database/
│   └── market_db.py            # 新版统一数据库（新增）
│
├── quant/
│   └── snapshot_engine.py      # 快照引擎（新增核心）
│
└── scheduler/                  # 调度器（新增）
    └── quant_scheduler.py      # 定时任务调度
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

## 🚀 使用方式

### 启动调度器（离线计算）
```bash
python -m scheduler.quant_scheduler --start
```

### 手动运行一次快照
```bash
python -m scheduler.quant_scheduler --run-once
```

---

## 📊 数据流对比

### V10.1 实时计算（现状）
```
用户请求 → 拉取数据 → 实时计算因子 → 实时生成信号 → 返回结果
                              ↑
                         每次重新计算
```

### V10.2 离线计算（目标）
```
每晚定时: 数据 → 因子 → 信号 → 快照 (写入数据库)
用户请求: 直接读取快照 → 返回结果 (无需计算)
```

---

## 🎯 数据中台优势

| 优势 | 说明 |
|------|------|
| **职责清晰** | 数据/计算/行为三层分离 |
| **可重算** | 因子可重新计算，历史结果不污染 |
| **高性能** | Parquet + SQLite 轻量化方案 |
| **无重复计算** | 用户访问直接读快照 |
| **可扩展** | 轻松支持回测/策略组合/Signal Center |
| **稳定** | 计算结果固化，不受实时数据波动影响 |

---

## 🔧 集成状态

- [x] `database/market_db.py` - 统一数据库（已创建）
- [x] `data_lake/__init__.py` - DataLake核心类（已创建）
- [x] `quant/snapshot_engine.py` - 快照引擎（已创建）
- [x] `scheduler/quant_scheduler.py` - 调度器（已创建）
- [ ] DataHub 集成 DataLake
- [ ] QuantCore 集成 SnapshotEngine
- [ ] SignalService 集成 FeatureStore

---

**AI Quant OS - 数据中台架构** 🚀