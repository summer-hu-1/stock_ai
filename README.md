# AI Market Operating System V9（信号中心 + 离线计算）

> 基于 DeepSeek + AkShare/yfinance + 多Agent协同的智能交易分析系统
>
> **V9 核心原则**：
> 1. 系统收敛 - UI → Service → Pipeline → Engine → Storage
> 2. 离线计算 - 指标由确定性代码预先计算
> 3. 在线消费 - 分析优先使用预计算数据
> 4. UI与业务分离 - Service Layer 隔离
> 5. AI不负责算指标 - 指标由 OfflineCalculator 计算
> 6. AI负责理解市场结构 - MarketStructureEngine + LLM

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
- **新增功能**：模拟数据模式、网络检测、历史记录删除

### V7.0 多市场路由 + 本地日线数据中心
> **核心升级**：从「单市场」到「多市场数据路由」，同时建立「本地数据底座」
- **多市场支持**：A股、港股、美股自动路由
- **Market Registry**：市场配置注册表
- **Symbol Resolver**：股票名称/代码解析器
- **Provider Factory**：数据源自动选择工厂
- **本地A股日线数据中心**：自动拉取3年日线、CSV永久存储、增量更新
- **CSV Provider**：统一本地数据访问接口
- **新增功能**：网络检测优化、友好错误提示

### V8.6 市场记忆系统（当前版本）
> **核心升级**：从「单日分析」到「市场叙事分析」，赋予系统「时间记忆能力」
- **Market Memory Layer**：市场记忆层架构
- **MarketStateEngine**：核心大脑（分析市场周期、情绪趋势、板块轮动、龙头切换）
- **MarketSnapshotGenerator**：每日市场快照生成器
- **历史趋势分析**：支持最近N天市场状态、情绪变化、龙头切换分析
- **时间序列推理**：从单点数据升级为趋势分析（如：涨停家数 32→45→61→78）
- **自动化快照生成**：每天下午3:30自动生成市场快照
- **UI升级**：Tab5新增市场记忆展示和趋势图表

### V8.6.1 真实数据优先策略
> **核心升级**：确保拉取的市场信息均为真实数据，不使用模拟数据
- **统一API降级策略**：本地数据库优先，多级数据获取机制
  - 优先级1：本地 `market_sentiment` 表（真实历史情绪数据）
  - 优先级2：本地 `market_snapshots` 表（真实市场快照）
  - 优先级3：akshare API（降级方案）
- **HistoricalSnapshotFetcher**：历史快照拉取器，支持按日期范围获取
- **移除模拟数据**：取消所有模拟数据生成功能

### V9.0 信号中心 + 离线计算
> **核心升级**：从「输入股票 -> 临时分析」升级为「全市场扫描 -> 结果入库 -> 用户查询」
> 
> **第一阶段：系统收敛**
> - **Service Layer**：统一服务层，隔离 UI 和业务逻辑
>   - AnalysisService、SignalService、MarketService、SyncService、UserService
> - **UI重构**：Tab5、Tab6 通过 Service 访问，不再直接调用 Engine
> - **多市场支持**：修复市场检测错误，支持 A股/港股/美股数据路由
> 
> **第二阶段：Signal Center（核心）✅ 已实现**
> - **SignalScanner**：全市场信号扫描器，扫描股票计算因子和信号
> - **LeaderScanner**：龙头识别扫描器，识别总龙头、板块龙头、补涨龙
> - **WatchlistBuilder**：关注列表构建器，自动构建高强度信号股票列表
> - **SectorStrength**：板块强度分析器，识别主线板块和轮动趋势
> - **signals.db**：SQLite数据库，存储 signals、leaders、watchlist、sector_strength
> - **每日扫描调度**：`scheduler/daily_scan.py` 自动执行全市场扫描
> 
> **每日扫描流程**：
> ```
> 全市场股票 → 读取本地OHLCV → FactorEngine → SignalEngine → LeaderEngine → 结果存入SQLite
> ```
- **本地数据利用**：充分利用已保存的大量历史数据记录

### V9.2 Signal Center 完整实现 ✅ 已实现
> **核心升级**：完善信号中心四大核心组件
> 
> **信号扫描器 (SignalScanner)**
> - 扫描股票生成突破/趋势/量能/动量/支撑信号
> - 支持信号强度计算 (0-1) 和方向判断 (up/down/neutral)
> - 自动保存到 signals.db

> **龙头扫描器 (LeaderScanner)**
> - 识别总龙头、板块龙头、补涨龙、强势股
> - 龙头评分体系 (0-1)，排名机制
> - 按板块分类，支持龙头梯队分析

> **关注列表构建器 (WatchlistBuilder)**
> - 基于信号强度自动构建关注列表
> - 优先级分级 (1-5)，标签系统
> - 支持手动添加/移除/更新

> **板块强度分析器 (SectorStrength)**
> - AI、半导体、新能源、消费、金融、医药、军工、周期八大板块
> - 板块强度计算和趋势判断 (up/down/sideways)
> - 主线板块识别和轮动趋势分析
> - 市场状态判断（牛市/震荡市/熊市）

### V8.7.1 统一分析管线 + 系统内核化
> **核心升级**：从「Streamlit项目」转变为「分析引擎」，实现业务逻辑与UI分离
- **AnalysisPipeline**：统一分析总线，全系统唯一分析入口
  - 数据加载 → 因子计算 → 信号生成 → 龙头识别 → 市场记忆 → Agent分析 → 综合评分
- **Dataclass化**：结构化数据模型替代字典，提升代码可维护性
- **统一日志系统**：全局logging配置，自动生成日志文件
- **共享UI组件**：Tab1和Tab2共用股票选择器（市场选择 + 刷新按钮）
- **系统内核化**：支持不启动UI直接运行分析（`python test_pipeline.py`）
- **数据获取策略**：本地CSV优先，网络获取兜底

### V9.1 登录会话持久化
> **核心升级**：修复刷新页面后自动退出登录的问题
- **URL会话持久化**：登录成功后将用户数据编码存储到URL参数（`?s=xxx`）
- **自动会话恢复**：刷新页面时从URL恢复登录状态，无需重新登录
- **安全退出**：退出登录时同时清除URL中的会话数据，防止自动恢复
- **新增 SyncService**：提供数据同步功能（`sync_stock_data`、`sync_all_stocks`、`get_sync_status`）
- **修复服务导入**：新增 `MarketService.get_recent_insights()` 方法，修复 `SyncService` 导入问题

---

## 📊 完整系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              UI 层 (Streamlit)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Tab1 单  │ │ Tab2 多  │ │ Tab3 Agent│ │ Tab4 历史 │ │ Tab5 情绪 │ │ Tab6 日线 │  │
│  │ Prompt   │ │ Agent    │ │ 详情      │ │ 记录      │ │ 周期      │ │ 数据中心  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Agent 层 (多Agent协同)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 行情     │ │ 情绪     │ │ 板块     │ │ 资金     │ │ 风险     │           │
│  │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │ │ Agent    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                              │                                              │
│                              ▼                                              │
│                     ┌──────────────────┐                                   │
│                     │ Controller Agent │ (总控决策)                          │
│                     └──────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Context 层 (统一数据)                                │
│                    ┌──────────────────────────┐                              │
│                    │      MarketContext       │ (个股+市场+板块+资金)        │
│                    └──────────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Provider + Cache + Context 三层隔离                      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          Data Service                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Provider Factory                               │  │
│  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐     │  │
│  │  │ AShare Provider  │ │ HK Provider      │ │ US Provider      │     │  │
│  │  │ (AkShare)        │ │ (yfinance)       │ │ (yfinance)       │     │  │
│  │  └──────────────────┘ └──────────────────┘ └──────────────────┘     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Symbol Resolver                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Market Registry                                   │  │
│  │  市场配置注册表 (A股/港股/美股)                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     本地日线数据中心 (CSV Provider)                    │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │ │
│  │  │ data/cn/daily/000001.csv, 000002.csv, ...                     │  │ │
│  │  │ 增量更新 → 只获取最新交易日                                    │  │ │
│  │  └────────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 模块职责划分

| Agent | 核心能力 | 输出格式 |
|-------|----------|----------|
| **📊 行情Agent** | 个股状态分析 | score/signal/risk/reason |
| **📉 情绪Agent** | 市场周期判断 | score/signal/risk/reason |
| **🧭 板块Agent** | 主线方向识别 | score/signal/risk/reason |
| **💰 资金Agent** | 活跃度分析 | score/signal/risk/reason |
| **⚠️ 风险Agent** | 风险评估 | score/signal/risk/reason |

---

## 📁 完整代码结构

```
stock_ai/
│
├── app.py                      # 主界面（Streamlit入口，6个Tab）
│
├── core/                        # 核心架构层
│   ├── context.py              # MarketContext 统一数据结构
│   ├── base_provider.py        # BaseProvider 基础数据提供者
│   ├── data_provider.py        # DataProvider 数据提供者
│   ├── provider_factory.py     # ProviderFactory 数据源工厂
│   ├── market_registry.py      # MarketRegistry 市场配置注册表
│   ├── symbol_resolver.py      # SymbolResolver 股票解析器
│   ├── data_service.py         # DataService 统一数据服务入口
│   ├── csv_provider.py         # CSVProvider 本地日线数据访问
│   ├── cache.py                # Cache 缓存层（内存+SQLite）
│   ├── logging_config.py       # 统一日志配置（V8.7.1新增）
│   ├── analysis_pipeline.py    # 统一分析管线（V8.7.1新增）
│   ├── models/                 # 数据模型（V8.7.1新增）
│   │   ├── __init__.py
│   │   ├── factor_result.py    # 因子结果模型
│   │   ├── signal_result.py    # 信号结果模型
│   │   ├── leader_result.py    # 龙头结果模型
│   │   └── analysis_result.py  # 分析结果模型
│   └── market_memory/          # 市场记忆系统（V8.6新增）
│       ├── __init__.py
│       ├── models.py           # 数据模型（MarketSnapshot/MarketTrend/MarketInsight）
│       ├── engine.py           # MarketStateEngine 核心大脑
│       ├── snapshot_generator.py # 市场快照生成器
│       └── api.py              # 统一API接口
│
├── factors/                     # V8 因子系统（新）
│   ├── __init__.py
│   ├── base_factor.py          # 基础因子类
│   ├── factor_engine.py         # 因子引擎（统一调度）
│   ├── trend_factor.py         # 趋势因子
│   ├── volume_factor.py        # 成交量因子
│   ├── momentum_factor.py      # 动量因子
│   ├── volatility_factor.py    # 波动率因子
│   └── strength_factor.py       # 强度因子
│
├── signals/                     # V8 信号系统（已完成）
│   ├── __init__.py
│   ├── base_signal.py           # 基础信号类
│   ├── breakout_signal.py      # 突破信号
│   ├── trend_signal.py         # 趋势信号
│   ├── reversal_signal.py      # 反转信号
│   ├── volume_signal.py        # 量能信号
│   └── signal_engine.py        # 信号引擎
│
├── leaders/                     # V8 龙头系统（已完成）
│   ├── __init__.py
│   ├── base_leader.py          # 基础龙头类
│   ├── leader_detector.py      # 龙头识别
│   ├── limitup_signal.py       # 涨停信号
│   ├── sector_leader.py        # 板块龙头
│   ├── dragon_ranker.py        # 龙头排名
│   └── leader_engine.py       # 龙头引擎
│
├── signal_center/               # V9 信号中心（核心模块）
│   ├── __init__.py
│   ├── signal_scanner.py       # 信号扫描器
│   ├── leader_scanner.py       # 龙头识别扫描器
│   ├── watchlist_builder.py    # 关注列表构建器
│   └── sector_strength.py      # 板块强度分析器
│
├── scheduler/                   # V9 调度器
│   ├── __init__.py
│   └── daily_scan.py           # 每日扫描任务
│
├── providers/                   # 各市场数据源
│   ├── ashare_provider.py      # A股 Provider (AkShare)
│   ├── hk_provider.py          # 港股 Provider (yfinance)
│   └── us_provider.py          # 美股 Provider (yfinance)
│
├── data_sync/                   # 数据同步脚本（V8.5统一）
│   ├── data_sync_manager.py     # 统一数据同步引擎
│   ├── sync_full.py            # 全量同步脚本
│   └── update_cn_daily.py      # 增量更新脚本

├── core/api_fallback/          # API降级系统（V8.5新增）
│   ├── __init__.py
│   ├── manager.py              # API降级管理器
│   └── registry.py             # API端点注册
│
├── validation/                  # 系统有效性验证（已完成）
│   ├── __init__.py
│   ├── backtester.py           # 回测框架
│   ├── signal_validator.py     # 信号验证
│   ├── factor_analyzer.py      # 因子分析
│   ├── simulator.py            # 模拟交易
│   └── validation_engine.py    # 验证引擎
│
├── agents/                     # 多Agent系统
│   ├── __init__.py
│   ├── market_agent.py         # 行情Agent
│   ├── sentiment_agent.py       # 情绪Agent
│   ├── sector_agent.py          # 板块Agent
│   ├── flow_agent.py           # 资金Agent
│   ├── risk_agent.py           # 风险Agent
│   └── controller_agent.py      # 总控Agent
│
├── modules/                    # 原有模块（保留兼容）
│   ├── market_data.py          # 行情数据获取
│   ├── market_sentiment.py     # 市场情绪数据
│   └── storage.py              # SQLite数据存储
│
├── auth/                       # 用户认证模块（V8.7新增）
│   ├── auth.py                 # 认证核心逻辑（登录/注册/权限检查/会话持久化）
│   └── pages.py                # 登录/注册页面组件
│
├── ui/                         # UI组件（V8.7.1新增）
│   └── components.py           # 共享UI组件（股票选择器、市场选择器）
│
├── admin/                      # 管理员后台（V8.7新增）
│   └── dashboard.py            # 管理员仪表盘（用户管理/分析记录/操作日志）
│
├── database/                   # 认证数据库（V8.7新增）
│   └── db.py                   # SQLite数据库 + SQLAlchemy模型
│
├── services/                   # 服务层（V9新增）
│   ├── __init__.py
│   ├── market_service.py       # 市场服务（市场周期、情绪趋势、板块轮动、市场洞察）
│   ├── signal_service.py       # 信号服务（信号查询、摘要统计）
│   └── sync_service.py         # 同步服务（数据同步、状态查询）
│
├── data/                       # 本地数据目录
│   └── cn/
│       ├── stock_list.csv      # A股股票列表
│       └── daily/              # A股日线数据（约5000个CSV，不提交git）
│           ├── 000001.csv
│           ├── 000002.csv
│           └── ...
│
├── scripts/                     # 工具脚本
│   └── init_stocks.py          # 初始化股票列表
│
├── test_pipeline.py             # Pipeline测试脚本（V8.7.1新增）
├── auto_snapshot.py             # 自动化快照定时任务脚本（V8.6新增）
├── service_manager.py           # 服务管理器（启动/停止/状态/开机自启）（V8.6新增）
│
├── deepseek.py                 # DeepSeek API封装
├── .env                        # 环境变量（API密钥）
├── .gitignore                  # Git忽略文件（忽略日线数据）
├── requirements.txt            # 依赖列表
├── stock_history.db            # SQLite数据库文件
└── README.md                   # 项目文档
```

---

## 🎯 V9 调用规范（强制）

### MarketContext 统一数据结构

```python
@dataclass
class MarketContext:
    stock_code: str                    # 股票代码
    stock_name: str                    # 股票名称
    market: str                        # 市场 (cn/hk/us)
    stock_data: Dict[str, Any]         # 个股行情数据
    market_sentiment: Dict[str, Any]   # 市场情绪数据
    sectors: List[Dict[str, Any]]      # 板块数据
    market_volume: float               # 全市场成交额
    risk_level: str                    # 风险等级
```

### Agent 统一输出格式

```python
{
    "score": int,      # 0-100 评分
    "signal": str,     # 看多/看空/观望
    "risk": str,       # 高/中/低
    "reason": list,    # 分析理由列表
    "data": dict       # 详细数据
}
```

### 本地日线数据存储

```csv
date,open,high,low,close,volume,amount,amplitude,price_change_pct,turnover_rate
2024-01-02,12.10,12.50,11.90,12.30,1000000,210000000,3.2,2.5,1.2
```

---

## 🎨 6个Tab功能

### Tab 1: ⚡ 单Prompt分析（快速）
- **市场选择**：A股/港股/美股
- **股票搜索**：下拉选择 + 手动输入
- API余额检查
- **真实数据展示**：个股行情、市场情绪、热门板块
- AI分析结果（Markdown格式）
- 报告下载功能

### Tab 2: 🧠 统一Pipeline分析（完整）
- **市场选择**：A股/港股/美股（与Tab1共用组件）
- **股票搜索**：下拉选择 + 手动输入（与Tab1共用组件）
- **统一分析管线**：数据加载 → 因子计算 → 信号生成 → 龙头识别 → 市场记忆 → Agent分析 → 综合评分
- **分析结果展示**：综合评分、风险等级、信号、各模块详细结果
- AI综合报告（深度分析）

### Tab 3: 📊 各Agent详情
- 行情Agent详细输出（含评分）
- 情绪Agent详细输出（含评分）
- 板块Agent详细输出（含评分）
- 资金Agent详细输出（含评分）
- 风险Agent详细输出（含评分）

### Tab 4: 📈 历史记录
- 按股票筛选历史记录
- 完整报告展示
- 历史报告下载
- **删除记录功能**：每条记录后可删除

### Tab 5: 📅 情绪周期
- 当前市场情绪状态
- 一键保存情绪记录
- 历史情绪记录查询
- **历史快照拉取**：支持按日期范围获取历史市场数据（优先从本地数据库获取真实数据）
- **市场洞察展示**：通过 MarketService 获取市场周期、情绪趋势、板块轮动、龙头切换分析

### Tab 6: 📊 A股日线数据中心
- **数据目录结构**：按市场板块分组存储（sh_main/sh_star/sz_main/sz_sme/sz_gem）
- **数据查看**：选择股票代码查看历史日线，支持股票名称显示
- **统计面板**：基本统计（最新价、涨跌、最高/最低、成交量、成交额、换手率）
- **增量更新**：日期选择器选择目标日期，点击更新按钮只获取缺失数据
- **自动去重**：相同日期数据自动去重，保留最新数据
- **同步服务**：通过 SyncService 进行数据同步和状态查询

---

## 📊 服务层说明（V9新增）

### MarketService - 市场服务

| 方法 | 功能 | 输出 |
|------|------|------|
| `get_market_cycle()` | 获取市场周期 | 周期阶段、描述、情绪得分 |
| `get_emotion_trend()` | 获取情绪趋势 | 趋势方向、变化率 |
| `get_sector_rotation()` | 获取板块轮动 | 主线板块、轮动趋势 |
| `get_leader_rotation()` | 获取龙头轮动 | 龙头梯队、切换状态 |
| `get_latest_insight()` | 获取最新市场洞察 | 综合分析报告 |
| `get_recent_insights()` | 获取最近洞察列表 | 洞察列表（含日期、状态、情绪得分） |

### SignalService - 信号服务

| 方法 | 功能 | 输出 |
|------|------|------|
| `get_signals()` | 获取信号数据 | DataFrame |
| `get_today_signals()` | 获取今日信号 | DataFrame |
| `get_stock_signals()` | 获取股票信号 | DataFrame |
| `get_top_signals()` | 获取高强度信号 | DataFrame |
| `get_leaders()` | 获取龙头股列表 | DataFrame |
| `get_watchlist()` | 获取关注列表 | DataFrame |
| `get_signal_summary()` | 获取信号统计摘要 | 统计信息 |

### SyncService - 同步服务

| 方法 | 功能 | 输出 |
|------|------|------|
| `sync_stock_data()` | 同步单只股票数据 | 同步结果 |
| `sync_all_stocks()` | 同步所有股票数据 | 同步结果 |
| `get_sync_status()` | 获取同步状态 | 状态信息 |

---

## 🚀 启动方式

### 本地开发
```bash
cd stock_ai
python3 -m streamlit run app.py --server.headless=true
```

访问：**http://localhost:8501**

### Streamlit Cloud 部署

**1. 配置 Secrets**

在 Streamlit Cloud 的 `Advanced settings` → `Secrets` 中配置：

```toml
# DeepSeek API Key（必需）
DEEPSEEK_API_KEY = "sk-38b8056ff6bb44f6b6847be48b598c88"

# 管理员账号（可选，用于初始化）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"
```

**2. 部署注意事项**

| 项目 | 说明 |
|------|------|
| **数据库** | Streamlit Cloud 使用内存数据库，部署后会重置 |
| **数据文件** | 股票日线数据（`data/cn/daily/`）不会上传，Cloud 环境下会通过网络获取 |
| **认证** | 用户注册功能正常可用，但数据不会持久化 |
| **会话持久化** | 登录状态通过 URL 参数持久化，刷新页面自动恢复 |

---

## ⚙️ 配置说明

### 环境变量（.env）
```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 模拟数据模式
- 当网络不可用或周末服务器维护时，可启用模拟数据模式
- 内置5只热门股票数据：000002、600519、000020、000858、601318
- 在界面右上角点击「🎭 模拟数据模式」开关启用

### 网络检测功能
- 点击「🔍 检测网络连接」按钮测试API连接状态
- 检测东方财富K线API、实时行情API、akshare接口
- 显示响应时间和连接状态

---

## 📊 功能特性总结

| 功能 | 说明 | 状态 |
|------|------|------|
| ✅ 多Agent协同分析 | 5个专业Agent分工协作 | 已实现 |
| ✅ 统一数据层 | MarketContext + DataProvider | 已实现 |
| ✅ 统一Agent输出 | score/signal/risk/reason 标准格式 | 已实现 |
| ✅ 多市场支持 | A股/港股/美股自动路由 | 已实现 |
| ✅ 本地日线数据中心 | 5372只A股近3年日线数据 | 已实现 |
| ✅ CSV Provider | 统一本地数据访问 | 已实现 |
| ✅ API Fallback Manager | 多数据源自动降级机制 | 已实现 |
| ✅ 真实行情数据 | AkShare/yfinance实时数据 | 已实现 |
| ✅ 历史记录系统 | SQLite持久化存储 | 已实现 |
| ✅ 报告下载 | Markdown格式导出 | 已实现 |
| ✅ 模拟数据模式 | 无网络时可测试 | 已实现 |
| ✅ 网络检测 | API连接诊断 | 已实现 |
| ✅ 记录删除 | 历史记录管理 | 已实现 |
| ✅ 增量更新功能 | Tab6按日期增量更新数据 | 已实现 |
| ✅ 热门概念板块 | 美化显示+模拟数据兜底 | 已实现 |
| ✅ 市场板块分组 | 数据按sh_main/sh_star等分组 | 已实现 |
| ✅ 市场记忆系统 | 市场快照、历史趋势分析、时间序列推理 | 已实现 |
| ✅ 自动化快照生成 | 每天下午3:30自动生成市场快照 | 已实现 |
| ✅ 趋势图表展示 | 情绪得分、涨停家数折线图 | 已实现 |
| ✅ 用户认证系统 | 登录/注册、密码哈希、会话管理 | 已实现 |
| ✅ 会员等级体系 | free/pro/vip三级会员 | 已实现 |
| ✅ 管理员后台 | 用户管理、分析记录、操作日志 | 已实现 |
| ✅ 统一分析管线 | AnalysisPipeline统一入口 | 已实现 |
| ✅ Dataclass化 | 结构化数据模型替代字典 | 已实现 |
| ✅ 统一日志系统 | 全局logging配置 | 已实现 |
| ✅ 共享UI组件 | Tab1/Tab2共用股票选择器 | 已实现 |
| ✅ 系统内核化 | 支持不启动UI直接分析 | 已实现 |
| ✅ 每日分析限制 | 基于会员等级的分析次数限制 | 已实现 |
| ✅ 服务层架构 | MarketService、SignalService、SyncService | 已实现 |
| ✅ 登录会话持久化 | URL参数存储，刷新自动恢复 | 已实现 |
| ✅ 信号中心 | SignalScanner、LeaderScanner、WatchlistBuilder、SectorStrength | 已实现 |
| ✅ 每日扫描调度 | scheduler/daily_scan.py 自动执行全市场扫描 | 已实现 |
| ✅ 龙头识别系统 | 总龙头、板块龙头、补涨龙识别 | 已实现 |
| ✅ 板块强度分析 | 八大板块强度计算、主线板块识别、轮动趋势分析 | 已实现 |

---

## 🔐 用户认证系统（V8.7新增）

### 功能特性

| 功能 | 说明 |
|------|------|
| **用户登录** | 用户名/密码登录，支持会话持久化 |
| **用户注册** | 支持用户名、邮箱、姓名注册 |
| **密码安全** | 使用 bcrypt 进行密码哈希 |
| **会话管理** | URL参数持久化，刷新自动恢复 |
| **安全退出** | 一键退出，清除会话数据 |

### 会员等级体系

| 等级 | 每日分析次数 | 说明 |
|------|-------------|------|
| **free** | 3次/天 | 免费用户 |
| **pro** | 10次/天 | 专业用户 |
| **vip** | 无限 | VIP用户 |

### 权限体系

| 角色 | 权限 |
|------|------|
| **guest** | 未登录，无法使用分析功能 |
| **member** | 普通用户，可进行股票分析 |
| **vip** | VIP用户，无限分析次数 |
| **admin** | 管理员，可访问后台管理 |

### 会话持久化机制（V9.1新增）

登录成功后，用户数据会被编码并存储到URL参数中：
- **登录时**：用户数据 → JSON → Base64 → URL参数（`?s=xxx`）
- **刷新时**：URL参数 → Base64解码 → JSON → 恢复会话
- **退出时**：同时清除 `session_state` 和 URL 参数

### 启动方式

```bash
cd stock_ai
python3 -m streamlit run app.py --server.headless=true
```

访问：**http://localhost:8501**

**首次使用**：运行时自动创建默认管理员账户（admin/123456）

---

## 📌 依赖说明

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
akshare>=1.12.0
yfinance>=0.2.0
sqlite3 (内置)
```

---

> **详细架构设计见**：[V9_ARCHITECTURE.md](V9_ARCHITECTURE.md)
> **市场记忆设计见**：[MARKET_MEMORY_SUMMARY.md](MARKET_MEMORY_SUMMARY.md)
