# AI 股票复盘系统 V7（多市场 + 本地日线数据中心）

> 基于 DeepSeek + AkShare/yfinance + 多Agent协同的智能交易分析系统

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
- **本地数据利用**：充分利用已保存的大量历史数据记录

### V8.7.1 统一分析管线 + 系统内核化
> **核心升级**：从「Streamlit项目」转变为「分析引擎」，实现业务逻辑与UI分离
- **AnalysisPipeline**：统一分析总线，全系统唯一分析入口
  - 数据加载 → 因子计算 → 信号生成 → 龙头识别 → 市场记忆 → Agent分析 → 综合评分
- **Dataclass化**：结构化数据模型替代字典，提升代码可维护性
- **统一日志系统**：全局logging配置，自动生成日志文件
- **共享UI组件**：Tab1和Tab2共用股票选择器（市场选择 + 刷新按钮）
- **系统内核化**：支持不启动UI直接运行分析（`python test_pipeline.py`）
- **数据获取策略**：本地CSV优先，网络获取兜底

---

## � 完整系统架构

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
│                                                                              │
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

---

## 🤖 各Agent职责

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
├── signals/                     # V8 信号系统（待实现）
│   ├── breakout_signal.py      # 突破信号
│   ├── trend_signal.py         # 趋势信号
│   ├── reversal_signal.py      # 反转信号
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
│   ├── auth.py                 # 认证核心逻辑（登录/注册/权限检查）
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

## 🧠 核心架构设计

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

### Tab 6: 📊 A股日线数据中心
- **数据目录结构**：按市场板块分组存储（sh_main/sh_star/sz_main/sz_sme/sz_gem）
- **数据查看**：选择股票代码查看历史日线，支持股票名称显示
- **统计面板**：基本统计（最新价、涨跌、最高/最低、成交量、成交额、换手率）
- **增量更新**：日期选择器选择目标日期，点击更新按钮只获取缺失数据
- **自动去重**：相同日期数据自动去重，保留最新数据

---

## 📊 本地日线数据中心使用

### 数据同步命令（统一脚本）

**核心脚本：**
- `data_sync/data_sync_manager.py` - 统一数据同步引擎
- `data_sync/sync_full.py` - 全量同步脚本
- `data_sync/update_cn_daily.py` - 增量更新脚本

**默认数据起点：** 2023-01-13

### Tab6 界面操作（推荐）
```
1. 选择股票 → 点击「🔄 增量更新当前股」
2. 点击「📥 全量更新所有股」一键同步
```

### 命令行操作

```bash
# 全量同步所有股票（从2023-01-13开始）
python data_sync/sync_full.py

# 单只股票全量同步
python data_sync/sync_full.py --code 000001

# 指定起点日期全量同步
python data_sync/sync_full.py --start-date 20230101

# 增量更新所有已有文件
python data_sync/update_cn_daily.py

# 单只股票增量更新
python data_sync/update_cn_daily.py --code 000001

# 指定目标日期增量更新
python data_sync/update_cn_daily.py --target-date 2026-05-10
```

### Tab6 界面功能
- **📥 全量更新所有股**：从2023-01-13开始，同步所有缺失的股票文件
- **🔄 增量更新当前股**：从当前股票的最新日期更新到选定的目标日期
- **自动去重**：相同日期数据自动去重，保留最新数据

### Agent读取数据
```python
from core.csv_provider import CSVProvider

df = CSVProvider().get_stock_daily("000002")
```

---

## 🔧 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **前端框架** | Streamlit | 快速构建Web应用 |
| **AI引擎** | DeepSeek API | deepseek-chat模型 |
| **A股数据** | AkShare | 免费A股行情数据 |
| **港股/美股** | yfinance | Yahoo Finance API |
| **数据存储** | CSV | 本地日线数据 |
| **数据库** | SQLite | 轻量级嵌入式数据库 |
| **语言** | Python 3.9+ | 核心开发语言 |

---

## 🚀 启动方式

```bash
cd stock_ai
python3 -m streamlit run app.py --server.headless=true
```

访问：**http://localhost:8501**

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

---

## 🔐 用户认证系统（V8.7新增）

### 功能特性

| 功能 | 说明 |
|------|------|
| **用户登录** | 用户名/密码登录，支持记住我 |
| **用户注册** | 支持用户名、邮箱、姓名注册 |
| **密码安全** | 使用 bcrypt 进行密码哈希 |
| **会话管理** | Streamlit Session 会话管理 |
| **退出登录** | 一键退出，清除会话 |

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

### 管理员后台功能

- **仪表盘统计**：用户数、分析次数、活跃度统计
- **用户管理**：用户列表、封禁/解封、会员等级调整
- **分析记录**：查看所有用户的分析记录
- **操作日志**：记录用户登录、分析等操作

### 启动方式

```bash
cd stock_ai
python3 -m streamlit run app.py --server.headless=true
```

访问：**http://localhost:8501**

**首次使用**：使用注册功能创建账户，或联系管理员获取测试账户。

---

## 🧠 市场记忆系统（V8.6）

### 核心架构

```
每日收盘
    ↓
生成市场快照
    ↓
存入历史数据库 (SQLite)
    ↓
下一次分析时读取
    ↓
AI结合历史上下文分析
```

### 市场快照结构

```json
{
    "date": "2026-05-12",
    "market_sentiment": "高潮",
    "emotion_score": 82,
    "top_sectors": ["机器人", "AI", "军工"],
    "leaders": ["XXX", "YYY"],
    "highest_board": 6,
    "limit_up_count": 78,
    "limit_down_count": 3,
    "volume": "放量",
    "north_money": "+52亿",
    "risk_level": "中",
    "hot_theme": "机器人",
    "dragon_rotation": true,
    "market_cycle": "主升期"
}
```

### MarketStateEngine 核心能力

| 方法 | 功能 | 输出 |
|------|------|------|
| `analyze_market_cycle()` | 分析市场周期 | 冰点/修复/高潮/分歧/退潮 |
| `analyze_emotion_trend()` | 分析情绪趋势 | 上升/下降/震荡 |
| `analyze_sector_rotation()` | 分析板块轮动 | 板块切换描述 |
| `analyze_leader_rotation()` | 分析龙头切换 | 龙头变化描述 |
| `analyze_risk_change()` | 分析风险变化 | 风险等级变化 |

### 时间序列推理示例

**普通系统：**
```text
今天涨停70家
```

**高级系统（市场记忆）：**
```text
涨停家数：32 → 45 → 61 → 78

连续4天提升

说明：
情绪持续加强
资金风险偏好提升
市场进入主升周期
```

### 自动化快照服务

**服务管理命令：**

| 命令 | 说明 |
|------|------|
| `python3 auto_snapshot.py --run-now` | 立即执行一次快照生成 |
| `python3 auto_snapshot.py --start-service` | 启动定时服务（前台） |
| `python3 auto_snapshot.py --show-log` | 查看日志 |
| `python3 service_manager.py start` | 启动服务（后台） |
| `python3 service_manager.py stop` | 停止服务 |
| `python3 service_manager.py status` | 查看服务状态 |
| `python3 service_manager.py enable` | 设置开机自启 |
| `python3 service_manager.py disable` | 移除开机自启 |

**定时任务配置：**
- **执行时间**：每天下午 15:30（A股收盘后）
- **日志文件**：`logs/auto_snapshot.log`

---

## 📝 后续升级方向

### V8.0 Factor + Signal + Leader 系统（已完成）
> **核心升级**：从"AI聊天"到"市场结构识别系统"
- **Factor Engine（V8.1）**：趋势/成交量/动量/波动率/强度5大因子
- **Signal Engine（V8.2）**：突破/趋势/反转/成交量信号
- **Leader Engine（V8.3）**：龙头识别、板块龙头、涨停信号、龙头排名
- **Validation Engine（V8.4）**：回测框架、信号验证、因子分析、模拟交易

### V8.5 多数据源自动降级 + 全量数据中心（当前版本）
> **核心升级**：完善数据稳定性和数据同步机制
- **API Fallback Manager**：多数据源自动降级（AkShare → 雪球 → 本地CSV → 模拟数据）
- **全量A股数据同步**：5372只A股近3年日线数据，按市场板块分组存储
- **增量更新功能**：Tab6新增日期选择器和增量更新按钮，只获取缺失数据
- **热门概念板块修复**：完善模拟数据和错误处理，美化显示
- **股票选择统一**：Tab1和Tab6保持一致的股票选择控件
- **优化数据目录**：data/cn/daily/下按市场板块分子目录存储（sh_main/sh_star/sz_main/sz_sme/sz_gem）

#### 数据流架构
```
OHLCV → Factor Engine → Signal Engine → Leader Engine → AI总结
```

#### V8.1 已完成：Factor Engine（第1周）
- [x] `base_factor.py` - 基础因子类
- [x] `trend_factor.py` - 趋势因子（MA5/10/20/60、多头排列、新高检测）
- [x] `volume_factor.py` - 成交量因子（量比、放量突破、缩量）
- [x] `momentum_factor.py` - 动量因子（5/10/20/60日涨幅、动量排名）
- [x] `volatility_factor.py` - 波动率因子（ATR、振幅、日波动率）
- [x] `strength_factor.py` - 强度因子（价格强度、成交量强度）
- [x] `factor_engine.py` - 因子引擎（统一调度、生成综合评分）

#### V8.2 已完成：Signal Engine（第2周）
- [x] `base_signal.py` - 基础信号类
- [x] `breakout_signal.py` - 突破信号（20日/60日新高、放量突破）
- [x] `trend_signal.py` - 趋势信号（均线排列、金叉死叉）
- [x] `reversal_signal.py` - 反转信号（底部反弹、长上下影线）
- [x] `volume_signal.py` - 成交量信号（量价齐升、缩量盘整）
- [x] `signal_engine.py` - 信号引擎（统一调度、综合信号）

#### V8.3 已完成：Leader Engine（第3周）
- [x] `base_leader.py` - 基础龙头类
- [x] `leader_detector.py` - 龙头识别（评分系统、连板检测）
- [x] `limitup_signal.py` - 涨停信号（连续涨停、逼近涨跌停）
- [x] `sector_leader.py` - 板块龙头（板块分析、龙头对比）
- [x] `dragon_ranker.py` - 龙头排名（多股票排名、龙头汇总）
- [x] `leader_engine.py` - 龙头引擎（统一调度、综合分析）

### V9: AI整合与自动化
- [ ] AI分析整合因子信号
- [ ] 自动选股功能
- [ ] 回测系统
- [ ] 每日交易建议推送

---

## 📊 V8 架构理解报告

### 1. 系统数据流架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据源层                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │  CSV本地日线数据      │  │  AkShare实时数据     │  │ yfinance海外数据  │  │
│  │  data/cn/daily/*.csv │  │  A股实时行情         │  │ 港股/美股         │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CSVProvider 数据访问层                             │
│  统一接口读取本地CSV文件，返回DataFrame                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Factor Engine 因子层                                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ Trend   │ │ Volume  │ │Momentum │ │Volatility│ │ Strength│              │
│  │ 趋势因子 │ │ 成交量  │ │ 动量因子 │ │ 波动率  │ │ 强度因子 │              │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘              │
│  输出：标准化市场特征 {ma5, volume_ratio, momentum_score, ...}             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Signal Engine 信号层                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                          │
│  │ Breakout│ │ Trend   │ │ Reversal│ │ Volume  │                          │
│  │ 突破信号 │ │ 趋势信号 │ │ 反转信号 │ │ 成交量  │                          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                          │
│  输出：买卖逻辑 {signal: "breakout", direction: "bullish", strength: 80}    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Leader Engine 龙头层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                          │
│  │ Leader      │ │ LimitUp     │ │ Sector      │                          │
│  │ 龙头识别     │ │ 涨停信号    │ │ 板块龙头    │                          │
│  └─────────────┘ └─────────────┘ └─────────────┘                          │
│  ┌─────────────────────────────────────────────┐                          │
│  │ DragonRanker 龙头排名                       │                          │
│  └─────────────────────────────────────────────┘                          │
│  输出：龙头股 {is_leader: True, leader_score: 85, type: "龙头"}            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI Agent 层（待实现）                               │
│  基于因子+信号+龙头进行AI综合分析，生成交易建议                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. 核心模块依赖关系

```
CSVProvider (数据源)
    │
    ├──因子计算─┬─→ FactorEngine ─→ 因子输出
    │           │
    │           └─→ SignalEngine ─→ 信号输出
    │                          │
    │                          └─→ LeaderEngine ─→ 龙头输出
    │                                         │
    │                                         └─→ AI Agent (待实现)
    │
    └─────────→ 直接读取 ─→ CSVProvider.get_stock_daily()
```

### 3. 各模块输入输出规范

| 模块 | 输入 | 输出 | 功能 |
|------|------|------|------|
| **CSVProvider** | stock_code | DataFrame(OHLCV) | 数据访问 |
| **FactorEngine** | DataFrame | {trend, volume, momentum, volatility, strength} | 市场特征标准化 |
| **SignalEngine** | DataFrame + Factors | {breakout, trend, reversal, volume, summary} | 买卖逻辑判断 |
| **LeaderEngine** | DataFrame + Factors + Signals | {is_leader, leader_score, leader_type} | 龙头识别 |

### 4. 龙头评分算法

```python
leader_score = (
    limit_up_score * 0.30 +   # 涨停相关（连板次数）
    momentum_score * 0.25 +   # 动量相关（涨幅、MA距离）
    volume_score * 0.20 +     # 成交量相关
    turnover_score * 0.15 +   # 换手率
    strength_score * 0.10     # 综合强度
)
```

### 5. 龙头类型判定

| 类型 | 条件 | 说明 |
|------|------|------|
| **龙头** | 评分≥85 且 连板≥2 | 市场核心领涨股 |
| **强势股** | 评分≥75 且 动量≥70 | 板块强势股 |
| **活跃股** | 评分≥65 且 涨停≥1 | 高活跃度股票 |
| **潜力股** | 评分≥60 | 具备龙头潜力 |
| **普通** | 评分<60 | 非龙头股票 |

### 6. 关键实现细节

**CSV存储结构**:
```csv
date,open,high,low,close,volume,amount,amplitude,price_change_pct,turnover_rate
2024-01-02,12.10,12.50,11.90,12.30,1000000,210000000,3.2,2.5,1.2
```

**因子输出示例**:
```python
factors = {
    "trend": {"ma5": 14.5, "ma20": 15.2, "ma_bullish": True, "trend_strength": 72},
    "volume": {"volume_ratio": 2.3, "volume_breakout": True, "volume_score": 75},
    "momentum": {"return_5d": 5.2, "momentum_score": 68},
    "summary": {"overall_score": 70, "bullish_signals": 3}
}
```

**信号输出示例**:
```python
signals = {
    "breakout": {"signal": "breakout_20d", "direction": "bullish", "strength": 78},
    "summary": {"overall_direction": "bullish", "overall_strength": 75}
}
```

**龙头输出示例**:
```python
leader = {
    "is_leader": True,
    "leader_score": 85,
    "leader_type": "龙头",
    "reason": ["连续涨停3天", "超强动量", "成交额异常放大"],
    "metadata": {"limit_up_count": 3, "momentum_score": 90}
}
```

---

## 🧐 架构分析与改进建议

### 当前架构的不合理之处

| 问题 | 说明 | 影响 |
|------|------|------|
| **1. data_sync/ 脚本过多且重复** | 存在11个数据同步脚本，功能重叠严重（sync_cn_daily.py, sync_all_a_stocks.py, sync_full.py, batch_sync_daily.py等） | 维护困难，用户不知道该用哪个脚本 |
| **2. 增量更新功能重复** | app.py中的Tab6实现了一套增量更新，data_sync/update_cn_daily.py是另一套 | 逻辑不一致，代码冗余 |
| **3. API Fallback 未完全集成** | core/api_fallback/已实现，但多数代码还在直接使用 modules/market_data.py | 降级机制未发挥作用 |
| **4. V8 Factor/Signal/Leader 未集成到主流程** | 完整的Factor+Signal+Leader系统已实现，但app.py中并未集成使用 | 核心功能未落地，用户体验不到 |
| **5. 配置管理分散** | 环境变量、市场配置、数据路径等分散在多个文件中 | 修改困难，易出错 |
| **6. 缺少统一的日志系统** | 各个脚本使用print输出，缺少统一的日志格式和管理 | 问题排查困难 |
| **7. 缺少单元测试** | 没有测试覆盖，重构风险高 | 维护成本高，质量难以保证 |
| **8. 数据存储冗余** | 既有CSV又有SQLite(stocks_cn.db, stock_history.db)，职责不清 | 数据一致性难保证 |

### 改进建议（优先级排序）

#### 🔥 高优先级（立即改进）

**1. 统一数据同步脚本**
```
重构方向：
- 保留 sync_full.py（全量同步）
- 保留 update_cn_daily.py（增量更新）
- 其他脚本归档到 deprecated/ 目录
- 在 app.py 中提供数据同步 UI 入口，复用同一套逻辑
```

**2. 集成 V8 Factor/Signal/Leader 到 app.py**
```
实现方向：
- Tab7: 因子分析（展示FactorEngine计算结果）
- Tab8: 信号检测（展示SignalEngine生成的信号）
- Tab9: 龙头识别（展示LeaderEngine分析结果）
- 或整合到现有的分析流程中
```

**3. 统一增量更新逻辑**
```
实现方向：
- 创建统一的 DataSyncManager 类
- app.py和data_sync脚本都复用这个类
- 支持：全量同步、增量更新、单只股票更新
```

#### ⚡ 中优先级（近期改进）

**4. 完善 API Fallback 集成**
```
实现方向：
- 所有数据获取通过 DataService 统一入口
- 确保 AkShare → 雪球 → 本地CSV → 模拟数据 降级链路完整
- 添加降级日志和统计
```

**5. 统一配置管理**
```
实现方向：
- 创建 config.py 集中管理所有配置
- 支持环境变量覆盖
- 配置项：数据路径、API密钥、市场配置、默认参数
```

**6. 统一日志系统**
```
实现方向：
- 使用 Python logging 模块
- 统一日志格式：[时间] [级别] [模块] 消息
- 日志输出到文件和控制台
```

#### 📝 低优先级（长期优化）

**7. 添加单元测试**
```
实现方向：
- tests/ 目录结构
- pytest 框架
- 核心模块测试覆盖率 ≥ 80%
```

**8. 数据存储优化**
```
实现方向：
- CSV 用于历史数据（只读为主）
- SQLite 用于分析结果、历史记录
- 明确职责边界，避免重复存储
```

**9. 代码质量提升**
```
实现方向：
- 类型提示 (type hints)
- 代码格式化 (black, isort)
- 静态代码检查 (mypy, pylint)
```

### 推荐的架构演进方向

```
┌─────────────────────────────────────────────────────────────────────┐
│                         应用层 (app.py)                              │
│  Tab1-6: 现有功能 + Tab7-9: Factor/Signal/Leader + Tab10: 数据同步   │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        业务逻辑层                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ DataSyncManager │  │ AnalysisManager │  │  AgentCoordinator│      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        核心服务层                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ DataService     │  │ FactorEngine    │  │ SignalEngine    │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│  ┌─────────────────┐  ┌─────────────────┐                          │
│  │ LeaderEngine    │  │ ValidationEngine│                          │
│  └─────────────────┘  └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        数据访问层                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ CSVProvider     │  │ API Fallback    │  │ Storage (SQLite)│      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        数据源层                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  CSV本地数据    │  │  AkShare API    │  │ yfinance API    │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📥 历史快照拉取器使用说明

### 功能概述
`HistoricalSnapshotFetcher` 提供按日期范围获取历史市场数据的能力，**优先从本地数据库获取真实数据**，确保数据的真实性和可靠性。

### API降级策略（优先级从高到低）

| 优先级 | 数据源 | 说明 |
|--------|--------|------|
| 1 | `market_sentiment` 表 | 本地真实历史情绪数据 |
| 2 | `market_snapshots` 表 | 本地真实市场快照 |
| 3 | `akshare` API | 降级方案（多种API尝试） |

### 使用方法

#### 通过Python代码
```python
from core.market_memory import MarketMemory

memory = MarketMemory()

# 拉取指定日期范围的真实数据
result = memory.fetch_date_range("2026-05-01", "2026-05-10")
print(f"成功: {result['success']}, 失败: {result['failed']}")

# 增量更新最近30天
result = memory.update_missing_snapshots(days=30)
print(f"缺失: {result['total_missing']}, 成功: {result['success']}")
```

#### 通过命令行
```bash
# 单日期拉取
python3 core/market_memory/historical_fetcher.py fetch --date 2026-05-08

# 日期范围拉取
python3 core/market_memory/historical_fetcher.py range --start-date 2026-05-01 --end-date 2026-05-10

# 增量更新最近30天
python3 core/market_memory/historical_fetcher.py update --days 30
```

#### 通过Tab5界面
进入 **Tab5: 情绪周期**，滚动到底部找到「📥 历史快照拉取」模块：
- 选择日期范围
- 点击「拉取」按钮获取真实历史数据

### 验证示例
```python
from core.market_memory import HistoricalSnapshotFetcher

fetcher = HistoricalSnapshotFetcher()
data = fetcher.fetch_historical_market_data('2026-05-08')
if data:
    print(f"✅ 获取成功!")
    print(f"   上涨家数: {data.get('rising_count')}")
    print(f"   下跌家数: {data.get('falling_count')}")
    print(f"   涨停家数: {data.get('limit_up_count')}")
    print(f"   跌停家数: {data.get('limit_down_count')}")
    print(f"   上涨比例: {data.get('rise_ratio')}%")
```

### 关键特性
- **真实数据优先**：优先从本地数据库获取，不使用模拟数据
- **多级降级**：本地数据不可用时自动尝试akshare API
- **日期范围支持**：支持按日期范围批量拉取历史数据
- **增量更新**：自动识别缺失日期，只拉取需要的数据
- **周末跳过**：自动跳过非交易日（周六、周日）

---

*系统版本：V8.6.1 真实数据优先策略*
*最后更新：2026-05-12*
