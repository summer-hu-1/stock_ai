# AI 股票复盘系统

> 基于 DeepSeek + AkShare + 多Agent协同 + 量化因子引擎的智能股票分析系统

---

## 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UI 层 (Streamlit)                               │
│  市场早知道 │ 个股快评 │ 看盘记录 │ 市场情绪 │ 行情数据                     │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      AI Agent 层 (多Agent协同)                           │
│     行情Agent  │  情绪Agent  │  板块Agent  │  资金Agent  │  风险Agent     │
│                      └────── Controller Agent ──────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Analysis Pipeline 分析管线                          │
│    Factor Engine → Signal Engine → Leader Engine → Agent → 综合评分     │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据层 (多源融合)                                │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐  │
│  │ AkShare  │ │ 新浪财经   │ │ 东方财富直连│ │ 雪球API    │ │ 本地缓存  │  │
│  │ (东方财富)│ │ (腾讯)    │ │ (eastmoney)│ │ (估算)     │ │ (SQLite) │  │
│  └──────────┘ └───────────┘ └───────────┘ └───────────┘ └──────────┘  │
│                         ↓ 6级自动降级 ↓                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              本地数据湖 (Parquet 日线 + SQLite 缓存)               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 核心设计思路

### 1. 多源数据降级策略

市场情绪数据采用 **6级自动降级**，确保任何网络环境下都能获取数据：

| 优先级 | 数据源 | 说明 |
|--------|--------|------|
| 1 | AkShare（东方财富） | 最快，数据最全 |
| 2 | AkShare（新浪/腾讯） | 较慢(~20s)，但网络更稳定 |
| 3 | 东方财富直连 API | 备用直接访问 |
| 4 | 雪球指数估算 | 仅指数数据，估算涨跌停 |
| 5 | 数据库缓存 | 之前成功获取的历史数据 |
| 6 | 内存缓存兜底 | 5分钟 TTL 内存缓存 |

每种数据源都会明确标注来源和可靠性（真实数据 / 估算数据 / 缓存数据）。

### 2. 量化分析管线

```
本地日线数据 (Parquet)
       │
       ▼
Factor Engine (5大因子)
  ├── 趋势因子：MA多头排列、均线距离、趋势强度
  ├── 成交量因子：量比、放量突破、缩量盘整
  ├── 动量因子：多周期涨幅、相对强度
  ├── 波动率因子：ATR、振幅、历史波动率
  └── 强度因子：价格强度、成交量强度
       │
       ▼
Signal Engine (4类信号)
  ├── 突破信号：20日/60日新高、放量突破
  ├── 趋势信号：金叉死叉、均线排列
  ├── 反转信号：底部反弹、长上下影线
  └── 成交量信号：量价齐升、缩量盘整
       │
       ▼
Leader Engine (龙头识别)
  ├── 龙头检测：评分系统、连板检测
  ├── 涨停信号：连续涨停、逼近涨跌停
  ├── 板块龙头：板块内排名
  └── 龙头排名：多股票综合排名
       │
       ▼
   AI Agent 综合分析 → 最终评分
```

### 3. 市场情绪引擎

独立的市场情绪量化分析模块，包含四大核心能力：

- **情绪周期判定**：冰点期 → 试错期 → 发酵期 → 主升期 → 高潮期 → 分歧期 → 退潮期 → 修复期
- **6大危险信号检测**：炸板率异常、跌停潮、连板断层、成交量萎缩、高标崩塌、情绪背离
- **明日观测点生成**：固定3个关键观测指标
- **AI每日市场剧本**：结构化JSON格式的市场预判

### 4. 市场记忆系统

赋予系统"时间记忆能力"，从单日分析升级为趋势叙事：

- **MarketStateEngine**：分析市场周期、情绪趋势、板块轮动、龙头切换
- **MarketSnapshotGenerator**：每日15:30收盘后自动生成市场快照
- **时间序列推理**：涨停家数 32→45→61→78，识别情绪加强趋势
- **历史数据存储**：SQLite持久化，支持跨天对比分析

### 5. 用户体系

| 角色 | 权限 |
|------|------|
| 游客 | 未登录可用，5次免费分析 |
| free | 注册用户，3次/天 |
| pro | 专业用户，10次/天 |
| vip | VIP用户，无限次数 |
| admin | 管理员，后台管理面板 |

- 邮箱作为核心身份标识
- bcrypt 密码哈希
- 登录弹窗 + Cookie自动登录（30天记住我）
- 管理员后台：用户管理、分析统计、操作日志

---

## 📁 代码结构

```
stock_ai/
│
├── app.py                          # Streamlit 主入口（5个Tab）
├── deepseek.py                     # DeepSeek API 封装（余额检查、缓存）
│
├── core/                           # 核心架构层
│   ├── context.py                  # MarketContext 统一数据结构
│   ├── data_service.py             # 统一数据服务入口
│   ├── base_provider.py            # 基础数据提供者抽象
│   ├── data_provider.py            # DataProvider 数据提供者
│   ├── provider_factory.py         # ProviderFactory 多市场数据源工厂
│   ├── market_registry.py          # MarketRegistry 市场配置注册表
│   ├── symbol_resolver.py          # SymbolResolver 股票代码解析器
│   ├── csv_provider.py             # 本地日线数据访问（Parquet/CSV）
│   ├── analysis_pipeline.py        # 统一分析管线（Factor→Signal→Leader→Agent）
│   ├── model_config.py             # AI模型配置（多个DeepSeek模型可切换）
│   ├── logging_config.py           # 统一日志配置
│   │
│   ├── market_memory/              # 市场记忆系统
│   │   ├── models.py               # MarketSnapshot/Trend/Insight 数据模型
│   │   ├── engine.py               # MarketStateEngine 核心大脑
│   │   └── api.py                  # 统一API接口
│   │
│   ├── api_fallback/               # API降级系统
│   │   ├── manager.py              # 降级策略管理中心
│   │   └── registry.py             # API端点注册
│   │
│   └── models/                     # 分析结果数据模型
│       ├── factor_result.py
│       ├── signal_result.py
│       ├── leader_result.py
│       └── analysis_result.py
│
├── factors/                        # 因子引擎
│   ├── base_factor.py              # 基础因子类
│   ├── factor_engine.py            # 因子引擎统一调度
│   ├── trend_factor.py             # 趋势因子
│   ├── volume_factor.py            # 成交量因子
│   ├── momentum_factor.py          # 动量因子
│   ├── volatility_factor.py        # 波动率因子
│   └── strength_factor.py          # 强度因子
│
├── signals/                        # 信号系统
│   ├── base_signal.py              # 基础信号类
│   ├── signal_engine.py            # 信号引擎统一调度
│   ├── breakout_signal.py          # 突破信号
│   ├── trend_signal.py             # 趋势信号
│   ├── reversal_signal.py          # 反转信号
│   └── volume_signal.py            # 成交量信号
│
├── leaders/                        # 龙头识别系统
│   ├── base_leader.py              # 基础龙头类
│   ├── leader_engine.py            # 龙头引擎统一调度
│   ├── leader_detector.py          # 龙头检测
│   ├── limitup_signal.py           # 涨停信号
│   ├── sector_leader.py            # 板块龙头
│   └── dragon_ranker.py            # 龙头排名
│
├── providers/                      # 多市场数据源
│   ├── ashare_provider.py          # A股 Provider (AkShare)
│   ├── hk_provider.py              # 港股 Provider (yfinance)
│   └── us_provider.py              # 美股 Provider (yfinance)
│
├── agents/                         # 多Agent系统
│   ├── market_agent.py             # 行情Agent
│   ├── sentiment_agent.py           # 情绪Agent
│   ├── sector_agent.py             # 板块Agent
│   ├── flow_agent.py               # 资金Agent
│   ├── risk_agent.py               # 风险Agent
│   └── controller_agent.py         # 总控Agent（协调+汇总）
│
├── modules/                        # 功能模块
│   ├── market_data.py              # 个股行情数据获取
│   ├── market_sentiment.py         # 市场情绪数据（6级降级）
│   ├── market_engine.py            # 市场情绪引擎（周期+危险+观测+剧本）
│   ├── morning_analyzer.py         # 早盘市场分析
│   └── storage.py                  # SQLite 数据存储（分析记录+情绪+快照）
│
├── auth/                           # 用户认证
│   ├── auth.py                     # 认证核心（登录/注册/权限/配额）
│   ├── modal.py                    # 登录弹窗 + Cookie自动登录
│   └── pages.py                    # 登录/注册页面组件
│
├── admin_auth/                     # 管理员系统
│   ├── db.py                       # 数据库 + SQLAlchemy模型
│   ├── models.py                   # 用户/日志数据模型
│   ├── repository.py               # 数据访问层
│   ├── service.py                  # 业务逻辑层
│   └── dashboard.py                # 管理员仪表盘
│
├── ui/                             # UI组件
│   └── components.py               # 股票选择器、市场选择器
│
├── validation/                     # 验证系统（开发中）
│   ├── backtester.py               # 回测框架
│   ├── signal_validator.py         # 信号验证
│   ├── factor_analyzer.py          # 因子分析
│   ├── simulator.py                # 模拟交易
│   └── validation_engine.py        # 验证引擎
│
├── data_sync/                      # 数据同步脚本
│   ├── data_sync_manager.py        # 统一数据同步引擎
│   ├── sync_full.py                # 全量同步
│   └── update_cn_daily.py          # 增量更新
│
├── scripts/                        # 工具脚本
│   ├── init_auth.py                # 初始化认证数据库
│   └── init_stocks.py              # 初始化股票列表
│
├── auto_snapshot.py                # 自动化市场快照定时任务
├── service_manager.py              # 服务管理器（启动/停止/自启）
│
├── datalake/cn/daily/SZ/           # 本地数据湖（Parquet格式日线）
├── data/cn/stocks_cn.db            # A股股票列表数据库
├── database/user_db.sqlite         # 用户认证数据库
├── core/stock_history.db           # SQLite 历史数据库
├── modules/stock_analysis.db       # 分析记录数据库
├── test_pipeline.py                # 分析管线测试脚本
├── GUIDE.md                        # 开发指南与指令记录
├── MARKET_MEMORY_SUMMARY.md        # 市场记忆系统总结
└── requirements.txt                # 依赖列表
```

---

## 🎨 5个Tab功能

### Tab 1: 📊 市场早知道
- **一键早盘分析**：开盘几分钟内获取市场强弱判断
- **大盘指数**：上证、深证、创业板、科创50、沪深300实时行情
- **市场情绪**：涨停/跌停、强势/弱势股、平均涨跌、炸板率、情绪周期
- **热门板块 TOP10**：当日最强板块排行
- **热点新闻**：东方财富/新浪财经实时资讯
- **AI早盘报告**：市场强弱、热点主线、风险提示、短线建议

### Tab 2: ⚡ 个股快评
- **三种分析模式**：极速（仅个股）、标准（个股+情绪）、完整（个股+情绪+板块）
- **智能搜索**：输入股票代码或名称自动匹配
- **市场情绪面板**：涨停/跌停、强势/弱势股、市场情绪状态
- **AI深度分析**：基于DeepSeek的个股综合评分与建议
- **报告下载**：支持TXT格式下载
- **分析记录**：自动保存到数据库

### Tab 3: 📋 看盘记录
- 按时间倒序展示历史分析记录
- 按股票筛选、展开查看详细报告
- 支持单条删除

### Tab 4: 📊 市场情绪
- **当前情绪数据**：涨停/跌停、涨跌家数、炸板率、平均涨跌
- **情绪引擎**：一键量化分析（周期判定、危险信号、观测点、AI剧本）
- **数据来源标识**：清晰标注 akshare/新浪/东方财富/雪球/缓存
- **历史记录**：情绪趋势图表、历史快照查看
- **市场记忆**：周期分析、情绪趋势、板块轮动、龙头切换

### Tab 5: 📈 行情数据
- **本地数据湖**：Parquet 格式存储的 A 股日线数据
- **数据查看**：选择股票查看历史日线 + 统计面板
- **全量更新**：一键同步所有股票日线数据（自2023-01-13起）
- **增量更新**：指定日期，只获取缺失数据
- **自动去重**：相同日期数据自动去重

---

## 🔧 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Streamlit | 快速构建Web应用 |
| AI引擎 | DeepSeek API | deepseek-chat / v4-pro / v4-flash 多模型可切换 |
| A股数据 | AkShare | 东方财富+新浪多数据源自动降级 |
| 数据存储 | Parquet + SQLite | 本地数据湖 + 嵌入式数据库 |
| 认证 | bcrypt + SQLAlchemy | 密码哈希 + ORM |
| 语言 | Python 3.9+ | 核心开发语言 |

---

## 🚀 启动方式

```bash
cd stock_ai

# 首次使用：初始化认证数据库（创建默认管理员）
python scripts/init_auth.py

# 启动应用
python3 -m streamlit run app.py --server.headless=true
```

访问：**http://localhost:8501**

---

## ⚙️ 配置说明

### 环境变量（.env）

```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 默认管理员账号

| 项目 | 值 |
|------|-----|
| 邮箱 | admin@stockai.com |
| 密码 | 123456 |

### 数据同步

```bash
# 全量同步所有股票（从2023-01-13开始）
python data_sync/sync_full.py

# 增量更新所有已有文件
python data_sync/update_cn_daily.py

# 单只股票增量更新
python data_sync/update_cn_daily.py --code 000001

# 指定目标日期增量更新
python data_sync/update_cn_daily.py --target-date 2026-05-20
```

或在 Tab5 行情数据界面中使用可视化按钮操作。

---

## 📊 功能清单

| 功能 | 说明 | 状态 |
|------|------|------|
| 游客模式 | 默认进入，5次免费分析 | ✅ |
| 登录弹窗 | 弹窗式登录/注册 + Cookie记住我 | ✅ |
| 会员等级 | free/pro/vip 三级 + 每日配额 | ✅ |
| 管理员后台 | 用户管理、分析记录、操作日志 | ✅ |
| 市场早知道 | 早盘分析（指数+情绪+板块+新闻+AI） | ✅ |
| 个股快评 | 三种分析模式（极速/标准/完整） | ✅ |
| 看盘记录 | 历史分析查看、筛选、删除 | ✅ |
| 市场情绪 | 情绪数据+情绪引擎+历史趋势 | ✅ |
| 行情数据 | Parquet数据湖，全量/增量同步 | ✅ |
| 6级数据降级 | akshare→新浪→东财直连→雪球→缓存→兜底 | ✅ |
| 数据来源标识 | 真实数据/估算数据/缓存数据清晰标注 | ✅ |
| 5大因子引擎 | 趋势/成交量/动量/波动率/强度 | ✅ |
| 4类信号系统 | 突破/趋势/反转/成交量 | ✅ |
| 龙头识别 | 龙头检测、板块龙头、涨停信号、龙头排名 | ✅ |
| 多Agent协同 | 行情/情绪/板块/资金/风险+总控 | ✅ |
| 统一分析管线 | 数据→因子→信号→龙头→Agent→评分 | ✅ |
| 市场情绪引擎 | 周期判定+危险检测+观测点+AI剧本 | ✅ |
| 市场记忆系统 | 历史趋势+周期+轮动+自动快照 | ✅ |
| AI模型切换 | deepseek-chat / v4-pro / v4-flash | ✅ |
| 报告下载 | TXT格式下载 | ✅ |
| 回测验证 | 信号验证/因子分析/模拟交易 | ⏳ 开发中 |