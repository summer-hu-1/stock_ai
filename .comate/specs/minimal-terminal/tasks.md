# AI 股票信息终端 - 任务计划

## 任务概览

1. 创建语言翻译层 `trader_lang.py`
2. 创建异动时间线 `hot_timeline.py`
3. 创建 AI 蒸馏引擎 `minimal_analysis.py`
4. 更新 UI 主题 `ui/theme.py`
5. 重构主应用 `app.py`（删除旧 Tab，构建两个新页面）

---

- [x] Task 1: 创建交易语言翻译层 `core/trader_lang.py`
    - 1.1: 定义个股状态 → 交易语言映射表（STATE_TO_TRADER_CN）
    - 1.2: 实现市场情绪翻译 `translate_market_status()` — 输入 sentiment 数据，输出 🟢🔴🟡 动态状态 + trader 文案
    - 1.3: 实现危险信号翻译 `translate_danger_signals()` — 输入 detect_danger_signals 结果，输出交易语言风险列表
    - 1.4: 实现主线提取 `extract_main_line()` — 从 hot_sectors 提取前两名板块组合
    - 1.5: 实现风险等级翻译 `translate_risk_level()` — risk key → 交易语言

- [x] Task 2: 创建异动时间线 `modules/hot_timeline.py`
    - 2.1: 实现 `generate_hot_timeline(hot_sectors, sentiment)` — 基于板块涨速模拟异动时间点
    - 2.2: 每条时间线包含 time、event、importance 字段
    - 2.3: 降级处理：数据不足时生成通用市场动态文本

- [x] Task 3: 创建 AI 蒸馏引擎 `core/minimal_analysis.py`
    - 3.1: 实现 `distill_market_brief(sentiment, hot_sectors, trader_status)` — 调用 DeepSeek 蒸馏 80-120 字市场理解
    - 3.2: 实现 `distill_main_line_memory(history_5d)` — 调用 DeepSeek 生成过去 5 日市场主线叙事
    - 3.3: 实现 `distill_next_day_scenario(stock_data, state, sector_info)` — 调用 DeepSeek 生成次日剧本（高开/平开/低开 三档）
    - 3.4: 实现 `distill_main_force_attitude(volume_data)` — 基于量价数据分析主力态度

- [x] Task 4: 更新 UI 主题 `ui/theme.py`
    - 4.1: 新增 `.pulse-hero-bar` — 动态状态条 CSS
    - 4.2: 新增 `.main-line-memory` — 主线记忆组件 CSS
    - 4.3: 新增 `.next-day-scenario` — 次日剧本卡片 CSS
    - 4.4: 新增 `.trader-card` — 通用终端卡片 CSS
    - 4.5: 新增 `.risk-item` — 风险项简洁样式
    - 4.6: 确保所有新样式与现有深色主题兼容

- [x] Task 5: 重构主应用 `app.py`
    - 5.1: 删除旧 NAV_ITEMS 和 5 个旧 Tab 渲染代码
    - 5.2: 定义新导航（市场脉搏 + AI 个股）
    - 5.3: 构建首页渲染 `render_market_pulse()` — 市场脉搏完整页面
    - 5.4: 构建 AI 个股页渲染 `render_ai_stock()` — AI 个股完整页面（暂不加入付费门控，两个 Tab 均可免费访问）
    - 5.5: 清理不再需要的 imports 和函数引用
    - 5.6: 删除侧边栏多余组件，保留登录入口
