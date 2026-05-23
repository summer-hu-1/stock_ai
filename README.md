# AI 股票复盘系统

> 基于 DeepSeek + AkShare + 多 Agent 协同 + 量化因子引擎的 AI 市场状态终端

---

## 系统架构总览

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         UI 层 · AI 驾驶舱终端                              │
│                                                                          │
│    ◉ 市场状态  │  ◎ 个股状态  │  ▲ 今日进攻  │  ◌ 市场时间线  │  ▣ 数据中心  │
│   (Terminal 风格胶囊导航 + 深色科技风 Bloomberg/TradingView 质感)            │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐ ┌──────────────────────────────────────────────────┐
│   结构引擎层          │ │              AI Agent 层 (6 Agent 协同)            │
│                      │ │                                                  │
│ ┌──────────────────┐ │ │  行情Agent  情绪Agent  板块Agent  资金Agent  风险Agent │
│ │ShortTermState    │ │ │            └──────── Controller Agent ────────┘      │
│ │Engine            │ │ │                                                  │
│ │短线状态引擎       │ │ │  按需调用 → 每个 Agent 用独立 System Prompt，         │
│ │7 种统一状态       │ │ │  从 MarketContext 中取数据做专项分析                   │
│ └──────────────────┘ │ └──────────────────────────────────────────────────┘
│ ┌──────────────────┐ │
│ │AttackOpportunity │ │
│ │Engine            │ │
│ │今日进攻引擎       │ │
│ │5 因子加权扫描     │ │
│ └──────────────────┘ │
└──────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      核心分析管线 (AnalysisPipeline)                       │
│                                                                          │
│   CSV/Parquet → Factor Engine → Signal Engine → Leader Engine            │
│        │              │                │                │                │
│        │         5 大因子 ×        4 类信号 ×        龙头识别 ×           │
│        │       (趋势/量能/动量/    (突破/趋势/反转/   (龙头检测/涨停信号/    │
│        │        波动/强度)         成交量)          板块龙头/排名)          │
│        │              │                │                │                │
│        └──────────────┴────────────────┴────────────────┘                │
│                                    │                                     │
│                            MarketContext                                │
│                    (统一数据结构，Agent 共享上下文)                        │
│                                    │                                     │
│                          multi_agent_review()                            │
│                              综合评分 + 报告                              │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          数据层 (多源融合 + 6 级降级)                      │
│                                                                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐   │
│  │ AkShare  │ │   新浪   │ │东方财富直连│ │   雪球    │ │ 本地缓存 │   │
│  │(东方财富) │ │ (腾讯)   │ │(eastmoney)│ │ (估算)    │ │ (SQLite) │   │
│  └──────────┘ └──────────┘ └───────────┘ └───────────┘ └──────────┘   │
│                       ↓ 6 级自动降级 ↓                                   │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │             本地数据湖 (Parquet 日线 + CSV 日线 + SQLite 缓存)      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │              市场记忆系统 (MarketMemory · 4 引擎)                   │ │
│  │  MarketStateEngine  │  SnapshotGenerator  │  NarrativeEngine       │ │
│  │       · 周期分析      │      · 每日快照       │      · 趋势叙事       │ │
│  │       · 情绪趋势      │      · 自动持久化     │      · 转折识别       │ │
│  │       · 板块轮动      │                      │                      │ │
│  │  ────────────────────┴──────────────────────┴──────────────────    │ │
│  │  HistoricalSnapshotFetcher  ·  历史拉取  ·  增量/全量               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 数据流全景

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户点击「分析」按钮                           │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ 个股日线数据  │    │ 市场情绪数据  │    │  板块数据    │
   │ CSV/Parquet │    │ (6级降级获取) │    │ (AkShare)  │
   └─────────────┘    └─────────────┘    └─────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  MarketContext  │  ← 统一数据结构
                    │   (dataclass)   │     所有 Agent 共享上下文
                    └─────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ FactorEngine │    │ SignalEngine │    │ LeaderEngine │
   │  趋势/量能/   │    │  突破/趋势/   │    │  龙头/涨停/   │
   │  动量/波动/   │    │  反转/成交量  │    │  板块龙头     │
   │  强度        │    │              │    │              │
   └─────────────┘    └─────────────┘    └─────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
          ┌─────────────────────────────────────┐
          │       multi_agent_review()          │
          │  行情 + 情绪 + 板块 + 资金 + 风险    │
          │         Controller Agent            │
          │           综合评分 + 报告            │
          └─────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  UI 展示 + 存储  │
                    │  (Streamlit)    │
                    └─────────────────┘
```

---

## 核心设计思路

### 1. AI 驾驶舱式 UI

区别于传统数据后台，本项目采用 **Bloomberg/TradingView 风格的深色科技终端**。

UI 样式集中定义在 [ui/theme.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/ui/theme.py)，通过 `inject_theme()` 注入全局 CSS：

| 特性 | 实现 |
|------|------|
| 胶囊式导航 | 5 个页面通过顶部胶囊按钮切换，每个页面有独立 Terminal View 编号和信号标签 |
| 超大市场状态卡片 | `market-cockpit` + `terminal-hero` 样式，56px 大字显示情绪周期 |
| 呼吸灯动画 | `terminal-pulse-anim` keyframes，市场周期旁脉冲动画 |
| 风险颜色系统 | CSS 自定义属性 `--tone-rgb`：主升=绿、分歧=黄、退潮=红、修复=青 |
| 暗色背景 | 多层径向渐变 + 线性渐变，模拟终端质感 |
| 输入框发光 | `:focus-within` 蓝色边框 + 外发光，不使用位移动画 |

### 2. 核心分析管线 (`AnalysisPipeline`)

[analysis_pipeline.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/core/analysis_pipeline.py) 是整个系统的分析总线，采用 **Pipeline 驱动架构**（非 UI 驱动），将各个模块串联：

```
CSV/Parquet 日线 → Factor Engine → Signal Engine → Leader Engine → Agent → 综合评分
```

#### 2.1 因子引擎 (`FactorEngine`)

| 因子 | 计算内容 |
|------|----------|
| **趋势因子** | MA 多头排列、均线距离、趋势强度 |
| **成交量因子** | 量比、放量突破、缩量盘整 |
| **动量因子** | 多周期涨幅、相对强度 |
| **波动率因子** | ATR、振幅、历史波动率 |
| **强度因子** | 价格强度、成交量强度 |

#### 2.2 信号引擎 (`SignalEngine`)

| 信号 | 触发条件 |
|------|----------|
| **突破信号** | 20日/60日新高、放量突破 |
| **趋势信号** | 金叉死叉、均线排列 |
| **反转信号** | 底部反弹、长上下影线 |
| **成交量信号** | 量价齐升、缩量盘整 |

#### 2.3 龙头引擎 (`LeaderEngine`)

| 模块 | 功能 |
|------|------|
| **龙头检测** | 评分系统、连板检测 |
| **涨停信号** | 连续涨停、逼近涨跌停 |
| **板块龙头** | 板块内排名 |
| **龙头排名** | 多股票综合排名 |

#### 2.4 MarketContext — 统一上下文

[context.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/core/context.py) 定义了 `MarketContext` 数据类，是所有 Agent 共享的统一输入：

```python
@dataclass
class MarketContext:
    stock_code: str
    stock_name: str
    stock_data: Dict       # 个股行情
    market_sentiment: Dict  # 市场情绪
    sectors: List[Dict]     # 板块数据
    market_volume: float    # 市场成交额
    risk_level: str         # 风险等级
    market_memory_context: Dict  # 市场记忆（周期、趋势、轮动）
```

#### 2.5 多 Agent 协同（6 Agent）

每个 Agent 使用独立的 System Prompt 从 MarketContext 取数据做专项分析，Controller Agent 负责协调和汇总：

| Agent | 职责 |
|-------|------|
| **行情 Agent** | 个股技术面分析、趋势判断 |
| **情绪 Agent** | 市场情绪周期、赚钱效应 |
| **板块 Agent** | 板块轮动、主线板块 |
| **资金 Agent** | 北向资金、成交量分析 |
| **风险 Agent** | 风险等级评估、回撤预警 |
| **总控 Agent** | 协调所有 Agent、生成综合报告 |

### 3. 结构引擎层（规则驱动，杜绝 AI 胡编）

在 AI Agent 之上新增两个纯规则驱动的结构引擎，输出确定性的结构化结果。

#### 3.1 短线状态引擎 (`ShortTermStateEngine`)

[short_term_state.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/engines/structure_engine/short_term_state.py)

基于最近 5 日 K 线数据，输出**统一的 7 种短线状态**：

| 状态 | 含义 | 双向剧本 |
|------|------|----------|
| 🚀 强势主升 | 连续放量加速 | 高开高走延续 / 冲高回落分歧 |
| 📈 平台突破 | 放量突破压力位 | 站稳支撑有效 / 假突破回落 |
| 🔄 弱转强 | 底部反转信号 | 放量确认转强 / 再次转弱 |
| 🆘 恐慌抛售 | 放量杀跌恐慌盘 | 长下影止跌 / 退潮延续 |
| 📉 缩量阴跌 | 缩量持续下跌 | 倍量阳线止跌 / 继续观望 |
| 📈 趋势上行 | 沿均线健康上行 | 5日线持有 / 跌破转弱 |
| ⏸️ 横盘整理 | 窄幅震荡方向选择 | 放量突破试多 / 跌破观望 |

每个状态附带：**双向剧本模板** + **风险提示文案** + **得分组件**（趋势/量能/动量/风险 四项 0-100 分）。

#### 3.2 今日进攻引擎 (`AttackOpportunityEngine`)

[attack_opportunity_engine.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/engines/attack_opportunity_engine.py)

扫描本地 CSV 日线数据，通过 5 因子加权评分选出 **TOP5 进攻目标**：

| 因子 | 权重 | 说明 |
|------|------|------|
| 趋势强度 | 25% | 均线排列、趋势方向、趋势健康度 |
| 量能爆发 | 20% | 量比、放量突破信号 |
| 龙头/突破 | 20% | 新高突破、涨停历史 |
| 短线状态 | 15% | ShortTermStateEngine 得分 |
| 情绪适配 | 20% | 与市场周期的匹配度 |

每只进攻目标输出：**综合评分**、**当前状态**、**所属主题**、**风险等级**、**进攻理由**、**进攻/防守双向剧本**。

### 4. 市场情绪引擎

[market_engine.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/modules/market_engine.py) — 独立的纯规则量化分析模块，四大核心：

| 能力 | 函数 | 说明 |
|------|------|------|
| 情绪周期判定 | `get_emotion_cycle()` | 基于涨停数/连板高度/炸板率/溢价，判定 8 个周期阶段 |
| 危险信号检测 | `detect_danger_signals()` | 6 大危险信号自动扫描 |
| 明日观测点 | `generate_observation_points()` | 固定 3 个关键观测指标 + 判定标准 + 双向预案 |
| AI 市场剧本 | `build_market_script_prompt()` | 构建结构化 Prompt 发给 DeepSeek 生成 JSON 剧本 |

**8 个情绪周期阶段**：冰点期 → 试错期 → 发酵期 → 主升期 → 高潮期 → 分歧期 → 退潮期 → 修复期

**6 大危险信号**：高位炸板、中位 A 杀、板块成交过热、炸板率飙升、核按钮重现、高位放量滞涨

### 5. 市场记忆系统

[core/market_memory/](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/core/market_memory/) — 赋予系统"时间记忆能力"，从单日分析升级为趋势叙事。

`MarketMemory` ([api.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/core/market_memory/api.py)) 是统一入口，内部组合 4 个引擎：

| 引擎 | 文件 | 功能 |
|------|------|------|
| `MarketStateEngine` | engine.py | **核心大脑**：周期分析、情绪趋势、板块轮动、龙头切换、风险变化 |
| `MarketSnapshotGenerator` | snapshot_generator.py | 每日 15:30 收盘后自动生成完整快照（情绪、涨跌停、龙头、板块、北向资金）并持久化到 SQLite |
| `NarrativeEngine` + `MarketInsightEngine` | insight_engine.py | 历史数据 → 结构化摘要 → 市场故事 → 关键转折点识别 |
| `HistoricalSnapshotFetcher` | historical_fetcher.py | 优先本地数据库获取真实历史，不足时从 akshare 拉取，支持增量/全量 |

### 6. 多源数据降级策略

[market_sentiment.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/modules/market_sentiment.py) — 市场情绪数据采用 **6 级自动降级**：

| 优先级 | 数据源 | 函数 | 特点 |
|--------|--------|------|------|
| 1 | AkShare（东方财富） | `_from_akshare_eastmoney()` | 最快，数据最全 |
| 2 | AkShare（新浪/腾讯） | `_from_akshare_sina()` | 较慢 ~20s，但网络更稳定 |
| 3 | 东方财富直连 API | `_from_eastmoney_direct()` | 备用直接访问 |
| 4 | 雪球指数估算 | `_from_xueqiu()` | 仅指数数据，估算涨跌停 |
| 5 | 数据库缓存 | SQLite 读取 | 之前成功获取的历史数据 |
| 6 | 内存缓存兜底 | 5 分钟 TTL | 所有 API 都失败时的最后保障 |

每种数据源都会**明确标注来源和可靠性**（✅真实数据 / ⚠️估算数据 / 📦缓存数据 / 🧪模拟数据）。

### 7. 用户体系

| 角色 | 权限 | 每日配额 |
|------|------|----------|
| 游客 | 未登录可用 | 5 次免费分析 |
| free | 注册用户 | 3 次/天 |
| pro | 专业用户 | 10 次/天 |
| vip | VIP 用户 | 无限 |
| admin | 管理员 | 后台管理面板 |

- 邮箱作为核心身份标识
- bcrypt 密码哈希
- [登录弹窗](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/auth/modal.py) + Cookie 自动登录（30 天记住我）
- [管理员后台](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/admin_auth/dashboard.py)：用户管理、分析统计、操作日志

### 8. AI 模型配置

[model_config.py](file:///Users/alittle/Documents/repo/ai/review_your_life/stock_ai/core/model_config.py) — 支持动态切换 3 个 DeepSeek 模型：

| 模型 | 用途 | Max Tokens |
|------|------|------------|
| `deepseek-chat` | 标准模型，平衡性能与速度（推荐） | 4096 |
| `deepseek-v4-pro` | V4 Pro，最强推理能力 | 8192 |
| `deepseek-v4-flash` | V4 Flash，更快更便宜 | 8192 |

---

## 📁 代码结构

```
stock_ai/
│
├── app.py                          # Streamlit 主入口 · AI 驾驶舱终端 · 5 页胶囊导航
├── deepseek.py                     # DeepSeek API 封装（余额检查、流式/缓存调用）
│
├── core/                           # ══ 核心架构层 ══
│   ├── context.py                  # MarketContext — 统一数据结构，Agent 共享上下文
│   ├── data_service.py             # 统一数据服务入口
│   ├── base_provider.py            # 基础数据提供者抽象类
│   ├── data_provider.py            # DataProvider — 多市场数据源封装
│   ├── provider_factory.py         # ProviderFactory — 按市场自动创建 Provider
│   ├── market_registry.py          # MarketRegistry — 市场配置注册表（cn/hk/us）
│   ├── symbol_resolver.py          # SymbolResolver — 股票代码解析（多格式统一）
│   ├── csv_provider.py             # 本地日线数据访问（Parquet + CSV）
│   ├── analysis_pipeline.py        # ★ 统一分析管线 · Factor→Signal→Leader→Agent
│   ├── model_config.py             # AI 模型配置（3 个 DeepSeek 模型可切换）
│   ├── logging_config.py           # 统一日志配置
│   │
│   ├── market_memory/              # ★ 市场记忆系统（4 引擎）
│   │   ├── __init__.py
│   │   ├── api.py                  # MarketMemory — 统一 API 入口
│   │   ├── engine.py               # MarketStateEngine — 周期/趋势/轮动/切换/风险
│   │   ├── models.py               # MarketSnapshot / MarketTrend / MarketInsight
│   │   ├── snapshot_generator.py   # MarketSnapshotGenerator — 每日快照生成
│   │   ├── insight_engine.py       # NarrativeEngine + MarketInsightEngine
│   │   └── historical_fetcher.py   # HistoricalSnapshotFetcher — 历史拉取
│   │
│   ├── api_fallback/               # API 降级系统
│   │   ├── manager.py              # 降级策略管理中心
│   │   └── registry.py             # API 端点注册
│   │
│   └── models/                     # 分析结果数据模型
│       ├── factor_result.py        # FactorResult
│       ├── signal_result.py        # SignalResult
│       ├── leader_result.py        # LeaderResult
│       └── analysis_result.py      # AnalysisResult
│
├── engines/                        # ══ 结构引擎层 · 规则驱动 ══
│   ├── __init__.py
│   ├── attack_opportunity_engine.py # ★ AttackOpportunityEngine · 5因子加权扫描
│   └── structure_engine/
│       ├── __init__.py
│       └── short_term_state.py     # ★ ShortTermStateEngine · 7种短线状态
│
├── factors/                        # ══ 因子引擎 ══
│   ├── base_factor.py              # 基础因子类
│   ├── factor_engine.py            # FactorEngine 统一调度
│   ├── trend_factor.py             # 趋势因子
│   ├── volume_factor.py            # 成交量因子
│   ├── momentum_factor.py          # 动量因子
│   ├── volatility_factor.py        # 波动率因子
│   └── strength_factor.py          # 强度因子
│
├── signals/                        # ══ 信号系统 ══
│   ├── base_signal.py              # 基础信号类
│   ├── signal_engine.py            # SignalEngine 统一调度
│   ├── breakout_signal.py          # 突破信号
│   ├── trend_signal.py             # 趋势信号
│   ├── reversal_signal.py          # 反转信号
│   └── volume_signal.py            # 成交量信号
│
├── leaders/                        # ══ 龙头识别 ══
│   ├── base_leader.py              # 基础龙头类
│   ├── leader_engine.py            # LeaderEngine 统一调度
│   ├── leader_detector.py          # 龙头检测
│   ├── limitup_signal.py           # 涨停信号
│   ├── sector_leader.py            # 板块龙头
│   └── dragon_ranker.py            # 龙头排名
│
├── agents/                         # ══ 多 Agent 协同 ══
│   ├── market_agent.py             # 行情 Agent · 技术面分析
│   ├── sentiment_agent.py          # 情绪 Agent · 赚钱效应
│   ├── sector_agent.py             # 板块 Agent · 轮动/主线
│   ├── flow_agent.py               # 资金 Agent · 北向/成交量
│   ├── risk_agent.py               # 风险 Agent · 等级评估/回撤预警
│   └── controller_agent.py         # 总控 Agent · 协调汇总 + 最终报告
│
├── providers/                      # ══ 多市场数据源 Provider ══
│   ├── ashare_provider.py          # A股 Provider (AkShare)
│   ├── hk_provider.py              # 港股 Provider (yfinance)
│   └── us_provider.py              # 美股 Provider (yfinance)
│
├── modules/                        # ══ 功能模块 ══
│   ├── market_data.py              # 个股行情数据获取
│   ├── market_sentiment.py         # ★ 市场情绪数据 · 6级降级
│   ├── market_engine.py            # ★ 市场情绪引擎 · 周期+危险+观测+剧本
│   ├── morning_analyzer.py         # 早盘市场分析
│   └── storage.py                  # SQLite 存储（分析记录 + 情绪 + 快照）
│
├── models/                         # ══ 通用数据模型 ══
│   └── analysis_result.py          # AnalysisResult
│
├── ui/                             # ══ UI 组件 ══
│   ├── theme.py                    # ★ 深色科技风 CSS · 1200+ 行样式
│   └── components.py               # 股票选择器、市场选择器
│
├── auth/                           # ══ 用户认证 ══
│   ├── auth.py                     # 认证核心（登录/注册/权限/配额）
│   ├── modal.py                    # ★ 登录弹窗 + Cookie 自动登录
│   └── pages.py                    # 独立登录/注册页面
│
├── admin_auth/                     # ══ 管理员系统 ══
│   ├── db.py                       # 数据库 + SQLAlchemy 模型
│   ├── models.py                   # User / Log 数据模型
│   ├── repository.py               # 数据访问层
│   ├── service.py                  # 业务逻辑层
│   └── dashboard.py                # 管理员仪表盘
│
├── database/                       # ══ 数据库基础设施 ══
│   └── db.py                       # SQLite + SQLAlchemy
│
├── validation/                     # ══ 验证系统（开发中）══
│   ├── validation_engine.py        # 验证引擎
│   ├── backtester.py               # 回测框架
│   ├── signal_validator.py         # 信号验证
│   ├── factor_analyzer.py          # 因子分析
│   └── simulator.py                # 模拟交易
│
├── data_sync/                      # ══ 数据同步 ══
│   ├── data_sync_manager.py        # 统一同步引擎
│   ├── sync_full.py                # 全量同步（2023-01-13 起）
│   └── update_cn_daily.py          # 增量更新
│
├── scripts/                        # ══ 工具脚本 ══
│   ├── init_auth.py                # 初始化认证数据库
│   └── init_stocks.py              # 初始化股票列表
│
├── auto_snapshot.py                # 自动化市场快照定时任务
├── service_manager.py              # 服务管理器（启动/停止/自启）
├── test_pipeline.py                # 分析管线测试脚本
├── create_users.py                 # 批量创建用户脚本
│
├── datalake/cn/daily/SZ/           # 本地数据湖（Parquet 日线）
├── data/cn/stocks_cn.db            # A 股股票列表数据库
├── core/stock_history.db           # 市场记忆 SQLite 数据库
├── modules/stock_analysis.db       # 分析记录数据库
├── admin_auth/admin_auth.db        # 管理员/用户认证数据库
├── database/user_db.sqlite         # 用户认证 SQLite
│
├── GUIDE.md                        # 开发指南与指令记录
├── MARKET_MEMORY_SUMMARY.md        # 市场记忆系统设计文档
└── requirements.txt                # 依赖列表
```

---

## 🎨 5 大页面（AI 驾驶舱终端导航）

采用 **TradingView/Bloomberg 风格胶囊导航**，每个页面有独立的 Terminal View 编号和信号标签。

### Page 01 · ◉ 市场状态（Market State）
- **超大 cockpit 卡片**：56px 大字显示情绪周期（主升期/分歧期/退潮期…），带呼吸灯脉冲动画
- **核心指标**：主线板块 + 次主线、风险等级（低/中/高）、涨停/跌停/连板/炸板率
- **一句话 AI 市场剧本**：基于结构化 JSON 生成的市场预判
- **危险信号内联展示**：6 大危险信号自动检测，标注严重程度
- **TOP3 热点板块**：带涨跌幅进度条 + 成交额 + 领涨股
- 进入页面自动调用市场情绪引擎，缓存 AI 解析结果

### Page 02 · ◎ 个股状态（Stock State）
- **短线状态卡片**（ShortTermStateEngine）：7 种规则化短线状态 + 双向剧本 + 四项得分
- **三种分析模式**：极速（仅个股）、标准（个股+情绪）、完整（个股+情绪+板块）
- **智能搜索**：输入代码或名称自动匹配
- **AI 深度分析**：基于 DeepSeek 的多 Agent 综合评分与建议
- **报告下载**：TXT 格式，分析记录自动保存到数据库

### Page 03 · ▲ 今日进攻（Attack Board）
- **AttackOpportunityEngine** 全市场扫描：5 因子 × 500 只股票
- **TOP5 进攻目标池**：综合评分 + 当前状态 + 所属主题 + 风险等级 + 进攻理由 + 双向剧本
- 从本地 CSV 日线数据批量计算因子，按评分排序

### Page 04 · ◌ 市场时间线（Market Timeline）
- **市场情绪日志**：按日期展开历史情绪快照（涨停/跌停/涨跌比例/情绪周期）
- **个股看盘记录**：按时间倒序，按股票筛选，展开查看详细 AI 复盘
- 每条记录支持 TXT 下载

### Page 05 · ▣ 数据中心（Data Center）
- **本地数据湖**：Parquet 日线 + CSV 日线副本
- **数据查看**：选择股票查看历史日线 + 统计面板
- **全量/增量更新**：一键同步或指定日期更新，自动去重

---

## 🔧 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| 前端框架 | **Streamlit** | 快速构建 Web 应用 |
| AI 引擎 | **DeepSeek API** | 3 模型可切换（chat/v4-pro/v4-flash） |
| A 股数据 | **AkShare** | 东方财富 + 新浪双源，6 级自动降级 |
| 数据存储 | **Parquet + SQLite** | 本地数据湖 + 嵌入式数据库 |
| 认证 | **bcrypt + SQLAlchemy** | 密码哈希 + ORM |
| 跨市场 | **yfinance** | 港股/美股行情数据 |
| Cookie | **extra-streamlit-components** | CookieManager 自动登录 |
| 语言 | **Python 3.9+** | |

---

## 🚀 启动方式

```bash
cd stock_ai

# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化认证数据库（创建默认管理员）
python scripts/init_auth.py

# 3. 启动应用
streamlit run app.py

# 或指定端口启动
python3 -m streamlit run app.py --server.port 8501
```

访问：**http://localhost:8501**

---

## ⚙️ 配置

### 环境变量（.env）

```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 默认管理员

| 项目 | 值 |
|------|-----|
| 邮箱 | admin@stockai.com |
| 密码 | 123456 |

### 数据同步

```bash
# 全量同步所有股票（从 2023-01-13 开始）
python data_sync/sync_full.py

# 增量更新所有已有文件
python data_sync/update_cn_daily.py

# 单只股票增量更新
python data_sync/update_cn_daily.py --code 000001

# 指定目标日期增量更新
python data_sync/update_cn_daily.py --target-date 2026-05-20
```

或在 Page 05 数据中心界面中使用可视化按钮操作。

---

## 📊 功能清单

| 功能 | 说明 | 状态 |
|------|------|------|
| **AI 驾驶舱终端** | Bloomberg/TradingView 深色科技风 + 胶囊导航 | ✅ |
| **市场状态 cockpit** | 56px 情绪周期 + 主线 + 风险 + AI 剧本 | ✅ |
| **个股短线状态** | ShortTermStateEngine 7 种规则化状态 | ✅ |
| **今日进攻 TOP5** | AttackOpportunityEngine 5 因子加权扫描 | ✅ |
| **游客模式** | 默认进入，5 次免费分析 | ✅ |
| **登录弹窗** | 弹窗式登录/注册 + Cookie 记住我 | ✅ |
| **会员等级** | free / pro / vip 三级配额 | ✅ |
| **管理员后台** | 用户管理、分析记录、操作日志 | ✅ |
| **个股分析** | 极速/标准/完整 三种模式 | ✅ |
| **看盘记录** | 历史分析查看、筛选、下载 | ✅ |
| **市场情绪引擎** | 周期判定 + 6 大危险检测 + 观测点 + AI 剧本 | ✅ |
| **市场记忆系统** | 4 引擎：State + Snapshot + Narrative + Fetcher | ✅ |
| **行情数据湖** | Parquet + CSV，全量/增量同步 | ✅ |
| **早盘分析** | 独立 Streamlit 页面 | ✅ |
| **6 级数据降级** | akshare→新浪→东财→雪球→缓存→兜底 | ✅ |
| **数据来源标识** | 真实/估算/缓存/模拟 清晰标注 | ✅ |
| **5 大因子引擎** | 趋势/成交量/动量/波动率/强度 | ✅ |
| **4 类信号系统** | 突破/趋势/反转/成交量 | ✅ |
| **龙头识别** | 龙头检测 + 板块龙头 + 涨停信号 + 排名 | ✅ |
| **6 Agent 协同** | 行情/情绪/板块/资金/风险 + 总控 | ✅ |
| **AI 模型切换** | deepseek-chat / v4-pro / v4-flash | ✅ |
| **报告下载** | TXT 格式 | ✅ |
| **多市场支持** | A 股 + 港股 + 美股 Provider | ✅ |
| **回测验证** | 信号验证 / 因子分析 / 模拟交易 | ⏳ 开发中 |