# AI 股票复盘系统 V6（多Agent架构版）

> 基于 DeepSeek + AkShare + 多Agent协同的智能交易分析系统

---

## 📌 版本迭代记录

### V1.0 - V5.0 基础功能
- V1.0: DeepSeek API 基础接入
- V2.0: AkShare 真实行情数据
- V3.0: 市场情绪分析
- V4.0: SQLite 历史记录系统
- V5.0: Markdown 报告 + 下载功能

### V6.0 多Agent架构（当前版本）
> **核心升级**：从「单Prompt AI」到「多Agent协同系统」
- **5个专业Agent**：行情Agent、情绪Agent、板块Agent、资金Agent、风险Agent
- **统一数据层**：MarketContext + DataProvider 架构
- **统一Agent输出**：score/signal/risk/reason 标准格式
- **完整真实数据展示**：个股行情、市场情绪、热门板块
- **新增功能**：模拟数据模式、网络检测、历史记录删除

---

## 🎯 两种分析模式

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **⚡ 单Prompt分析（快速）** | 速度快、一次DeepSeek调用、原有功能完全保留 | 日常快速复盘、仅需简单分析 |
| **🧠 多Agent分析（完整）** | 5个Agent分工协作、更全面分析、结构化输出 | 深度分析、需要多维度判断 |

---

## 🏗 多Agent系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Controller Agent                        │
│                    （总控决策）                             │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    MarketContext                            │
│   统一数据层：股票数据 + 市场情绪 + 板块数据 + 资金数据     │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────┐     ┌───────────────────┐
│    DataProvider   │────▶│  AkShare API      │
│    （数据提供者）   │     │  （数据源）       │
└───────────────────┘     └───────────────────┘
         │
         │ 构建
         ▼
┌──────────┬─────────────┬─────────────┬──────────┐
│ 行情     │ │ 情绪     │ │  板块      │ │  资金    │ │  风险   │
│ Agent    │ │ Agent    │ │  Agent     │ │  Agent   │ │ Agent   │
└──────────┴─────────────┴─────────────┴──────────┘
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

## 📁 代码结构

```
stock_ai/
│
├── app.py                      # 主界面（Streamlit入口）
│
├── core/                        # 核心架构层（新增）
│   ├── context.py              # MarketContext 统一数据结构
│   └── data_provider.py        # DataProvider 统一数据提供者
│
├── agents/                     # 多Agent系统（重构）
│   ├── __init__.py
│   ├── market_agent.py         # 行情Agent - 从Context读取数据
│   ├── sentiment_agent.py       # 情绪Agent - 从Context读取数据
│   ├── sector_agent.py          # 板块Agent - 从Context读取数据
│   ├── flow_agent.py           # 资金Agent - 从Context读取数据
│   ├── risk_agent.py           # 风险Agent - 从Context读取数据
│   └── controller_agent.py      # 总控Agent - 统一调度
│
├── modules/                    # 原有模块（保留兼容）
│   ├── market_data.py          # 行情数据获取（含模拟数据模式）
│   ├── market_sentiment.py     # 市场情绪数据
│   └── storage.py              # SQLite数据存储
│
├── deepseek.py                 # DeepSeek API封装
├── .env                        # 环境变量（API密钥）
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

---

## 🎨 5个Tab功能

### Tab 1: ⚡ 单Prompt分析（快速）
- 股票代码输入（支持自动补全）
- API余额检查
- **真实数据展示**：个股行情、市场情绪、热门板块（可折叠JSON）
- AI分析结果（Markdown格式）
- 报告下载功能

### Tab 2: 🧠 多Agent分析（完整）
- 股票代码输入
- **真实数据展示**：个股行情、市场情绪、热门板块
- 5个Agent协同分析流程
- 快速摘要面板
- AI综合报告（更深度分析）
- 完整报告下载

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

---

## 🔧 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| **前端框架** | Streamlit | 快速构建Web应用 |
| **AI引擎** | DeepSeek API | deepseek-chat模型 |
| **数据来源** | AkShare | 免费A股行情数据 |
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

## � 功能特性总结

| 功能 | 说明 | 状态 |
|------|------|------|
| ✅ 多Agent协同分析 | 5个专业Agent分工协作 | 已实现 |
| ✅ 统一数据层 | MarketContext + DataProvider | 已实现 |
| ✅ 统一Agent输出 | score/signal/risk/reason 标准格式 | 已实现 |
| ✅ 真实行情数据 | AkShare实时数据接入 | 已实现 |
| ✅ 历史记录系统 | SQLite持久化存储 | 已实现 |
| ✅ 报告下载 | Markdown格式导出 | 已实现 |
| ✅ 模拟数据模式 | 无网络时可测试 | 已实现 |
| ✅ 网络检测 | API连接诊断 | 已实现 |
| ✅ 记录删除 | 历史记录管理 | 已实现 |

---

## 📝 后续升级方向

- [ ] V7: 龙头识别系统
- [ ] V7: 自动选股功能
- [ ] V7: 交易计划生成
- [ ] V7: 加权评分与自动决策
- [ ] V8: 每日交易建议推送
- [ ] V8: 回测与强化学习

---

*系统版本：V6.0 多Agent架构版*
*最后更新：2026-05-08*
