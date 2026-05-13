# V9 Clean Architecture - 工程重构指南

> **核心原则**：
> - Pipeline 负责"算"
> - Service 负责"用"
> - Agent 负责"解释"

---

## ① 当前架构问题诊断

### ❌ 问题1：三个"大脑"职责重叠

| 组件 | 当前职责 | 问题 |
|------|----------|------|
| `AnalysisPipeline` | 数据→因子→信号→龙头→Agent→评分 | 同时做计算和协调 |
| `SignalCenter` | 全市场扫描 | 与 Pipeline 职责部分重叠 |
| `ControllerAgent` | 运行所有子Agent + DeepSeek报告 | 既算又解释 |

### ❌ 问题2：调用关系混乱

```
Pipeline → Agent.multi_agent_review()
Service → Pipeline.analyze()
App → Service.analyze_stock()
```

**问题**：Pipeline 调用 Agent，但 Agent 又做完整分析，形成循环。

### ❌ 问题3：Engine 层边界不清

- `factors/` - 算指标
- `signals/` - 生成信号
- `leaders/` - 识别龙头
- `signal_center/` - 又做扫描

---

## ② V9 Clean Architecture（目标架构）

### 🏗️ 系统分层（严格单向依赖）

```
┌─────────────────────────────────────────────────────────────┐
│                      UI 层 (Streamlit)                      │
│                   app.py → services/*                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (V9核心)                    │
│        market_service.py / signal_service.py                │
│        sync_service.py / analysis_service.py                 │
│                                                             │
│         ✅ 唯一业务入口                                     │
│         ✅ 聚合 Core Engine                                │
│         ✅ 屏蔽复杂度                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Engine Layer                         │
│                 analysis_pipeline.py                         │
│                                                             │
│         ⭐ 唯一计算入口                                     │
│         ✅ 数据加载 → 因子 → 信号 → 龙头 → 评分              │
│         ❌ 不直接调用 Agent                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Quant Engine Layer                        │
│         factors/    signals/    leaders/    market_memory/   │
│                                                             │
│         ✅ 纯计算                                            │
│         ✅ 无业务逻辑                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│         providers/  csv_provider/  market_registry/          │
│                                                             │
│         ✅ 数据获取                                          │
│         ✅ 市场路由                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                              │
│         signals.db  stock_history.db  data/cn/daily/        │
└─────────────────────────────────────────────────────────────┘
```

### 🧭 模块职责重划

#### 🟦 UI层（纯展示）
```
app.py
ui/components.py
auth/pages.py
admin/dashboard.py
```
**职责**：
- 只做展示
- 不做计算
- 通过 Service 访问数据

#### 🟨 Service层（V9核心入口）
```
services/
    market_service.py      # 市场服务
    signal_service.py      # 信号服务
    sync_service.py        # 同步服务
    analysis_service.py    # 分析服务 ⭐新增统一入口
```
**职责**：
- 唯一业务入口
- 聚合 Core Engine
- 返回格式化数据给 UI

#### 🟥 Core Engine层（唯一计算入口）
```
core/
    analysis_pipeline.py   # ⭐ 唯一分析入口（不含Agent）
    context.py
    cache.py
    logging_config.py
```
**职责**：
- 数据加载 → 因子 → 信号 → 龙头 → 评分
- **不调用 Agent**
- **不生成报告**

#### 🟪 Quant Engine层（纯计算）
```
factors/          # 指标计算
signals/          # 信号生成
leaders/          # 龙头识别
market_memory/    # 市场记忆
```
**职责**：
- 纯数学计算
- 无业务逻辑
- 接收数据，返回结果

#### 🟩 Agent Layer（解释层，V9重构）
```
agents/
    market_agent.py        # 只解释行情
    sentiment_agent.py     # 只解释情绪
    sector_agent.py        # 只解释板块
    flow_agent.py         # 只解释资金
    risk_agent.py         # 只解释风险
    report_agent.py        # ⭐ 新增：统一报告生成
```
**职责变更**：
- ❌ 不再算指标
- ✅ 只负责"解释市场结构"
- ✅ 生成人类可读的分析报告

#### 🟫 Data Layer
```
providers/
core/
    csv_provider.py
    market_registry.py
    symbol_resolver.py
```
**职责**：
- 数据获取（AkShare / yfinance / CSV）
- 市场路由
- 本地数据优先

#### 🟧 Storage Layer
```
storage/sqlite/
    signals.db
stock_history.db
data/cn/daily/
```
**职责**：
- 信号存储
- 市场快照
- 历史行情

#### ⬛ Scheduler Layer
```
scheduler/
    daily_scan.py
```
**职责**：
- 每日收盘后自动扫描
- 更新信号和龙头数据

---

## ③ V9 调用规范（强制）

### ✅ 正确调用路径

```python
# 1. UI 层
from services import get_analysis_service
service = get_analysis_service()
result = service.analyze_stock("000001")

# 2. Service 层
from core.analysis_pipeline import get_pipeline
pipeline = get_pipeline()
result = pipeline.analyze(stock_code)

# 3. Core Engine（单向）
from factors.factor_engine import FactorEngine
factors = FactorEngine().calculate(df)

# 4. Agent（仅用于解释）
from agents.report_agent import generate_report
report = generate_report(factors, signals, leaders, context)
```

### ❌ 禁止的调用路径

```python
# 禁止：Pipeline 直接调用 Agent
# pipeline.py 不应 import multi_agent_review

# 禁止：Service 直接操作 Engine 内部
# service.py 不应直接调用 FactorEngine.calculate()

# 禁止：UI 直接调用 Engine
# app.py 不应 import FactorEngine
```

---

## ④ 重构实施计划

### Phase 1：职责分离
1. 从 `AnalysisPipeline` 移除 `multi_agent_review` 调用
2. 创建 `ReportAgent` 专门负责报告生成
3. Pipeline 输出结构化数据，Agent 负责解释

### Phase 2：Service 收敛
1. 统一所有 UI 入口到 Service
2. 移除直接 Engine 调用
3. 添加 `analysis_service.py` 统一入口

### Phase 3：清理重复
1. 合并 `signal_center` 和 `leaders` 重复逻辑
2. 统一因子/信号/龙头计算入口
3. 移除冗余模块

---

## ⑤ 关键文件变更

### 需要修改
| 文件 | 变更 |
|------|------|
| `core/analysis_pipeline.py` | 移除 Agent 调用，专注计算 |
| `services/analysis_service.py` | 添加 analyze_stock 统一入口 |
| `agents/controller_agent.py` | 重构为 ReportAgent |
| `app.py` | 统一通过 Service 访问 |

### 需要新增
| 文件 | 职责 |
|------|------|
| `services/report_service.py` | 专门处理报告生成 |

### 需要清理
| 文件 | 原因 |
|------|------|
| `signal_center/signal_scanner.py` | 合并到 Pipeline |
| `leaders/leader_engine.py` | 合并到 Quant Engine |

---

## ⑥ 验证标准

重构完成后，系统应满足：

1. **单向依赖**：UI → Service → Pipeline → Engine → Data → Storage
2. **无循环调用**：Pipeline 不调用 Agent，Agent 不调用 Pipeline
3. **职责清晰**：每个模块只有单一职责
4. **可测试**：每层可以独立测试
