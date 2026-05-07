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
- **两种分析模式**：单Prompt快速分析、多Agent完整分析
- **完整真实数据展示**：个股行情、市场情绪、热门板块

---

## 🎯 两种分析模式

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **⚡ 单Prompt分析（快速）** | 速度快、一次DeepSeek调用、原有功能完全保留 | 日常快速复盘、仅需简单分析 |
| **🧠 多Agent分析（完整）** | 5个Agent分工协作、更全面分析、结构化输出 | 深度分析、需要多维度判断 |

---

## 🏗 多Agent系统架构

```
                    ┌───────────────────┐
                    │  Controller Agent │
                    │   （总控决策）     │
                    └─────────┬─────────┘
                              │
    ┌──────────┬─────────────┼─────────────┬──────────┐
    ▼          ▼             ▼             ▼          ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐
│ 行情   │ │ 情绪   │ │  板块    │ │  资金    │ │  风险  │
│ Agent  │ │ Agent  │ │  Agent   │ │  Agent   │ │ Agent  │
└────────┘ └────────┘ └──────────┘ └──────────┘ └────────┘
```

---

## 🤖 各Agent职责

| Agent | 核心能力 | 输出内容 |
|-------|----------|----------|
| **📊 行情Agent** | 个股状态分析 | 价格/涨跌幅/换手率/异动信号/强势度 |
| **📉 情绪Agent** | 市场周期判断 | 情绪周期/涨停家数/上涨比例/操作信号 |
| **🧭 板块Agent** | 主线方向识别 | 主线板块/热门板块/资金流向 |
| **💰 资金Agent** | 活跃度分析 | 流动性/投机热度/全市场成交额 |
| **⚠️ 风险Agent** | 风险评估 | 风险等级/操作建议/短线可操作性 |

---

## 📁 代码结构

```
stock_ai/
│
├── app.py                      # 主界面（5个Tab）
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
├── modules/                    # 原有模块（保留）
│   ├── market_data.py          # 行情数据
│   ├── market_sentiment.py     # 情绪数据
│   └── storage.py              # 数据存储
│
├── deepseek.py                 # DeepSeek API
├── .env                        # API密钥
└── stock_history.db            # SQLite数据库
```

---

## 🎨 5个Tab功能

### Tab 1: ⚡ 单Prompt分析（快速）
- 股票代码输入
- API余额检查
- **真实数据展示**：个股行情、市场情绪、热门板块（可折叠JSON）
- AI分析结果（Markdown）
- 报告下载

### Tab 2: 🧠 多Agent分析（完整）
- 股票代码输入
- **真实数据展示**：个股行情、市场情绪、热门板块（可折叠JSON）
- 5个Agent协同分析
- 快速摘要面板
- AI综合报告（更深度）
- 完整报告下载

### Tab 3: 📊 各Agent详情
- 行情Agent输出
- 情绪Agent输出
- 板块Agent输出
- 资金Agent输出
- 风险Agent输出

### Tab 4: 📈 历史记录
- 按股票查看历史
- 完整报告展示
- 历史报告下载

### Tab 5: 📅 情绪周期
- 当前市场情绪
- 一键保存情绪
- 历史情绪记录

---

## 🔧 技术栈

- **前端**：Streamlit
- **AI**：DeepSeek API (deepseek-chat)
- **数据源**：AkShare (免费)
- **数据库**：SQLite
- **语言**：Python 3.9+

---

## 🚀 启动方式

```bash
cd stock_ai
python3 -m streamlit run app.py --server.headless=true
```

访问：**http://localhost:8501**

---

## 📌 后续升级方向

- [ ] V7: 龙头识别系统
- [ ] V7: 自动选股功能
- [ ] V7: 交易计划生成
- [ ] V8: 每日交易建议推送
- [ ] V8: 邮件/消息通知

---

*系统版本：V6.0 多Agent架构版*
*最后更新：2026-05-08*
