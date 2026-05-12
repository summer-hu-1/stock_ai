# 市场记忆功能实现总结

## 🎯 核心目标

实现"市场记忆能力"，让系统不仅看"今天"，还能理解：
- 昨天怎么样
- 前天怎么样
- 上周怎么样
- 趋势怎么演化
- 情绪怎么变化
- 龙头怎么切换

## 📦 核心模块

### 1. 数据模型（`core/market_memory/models.py`）

#### MarketSnapshot
市场快照数据模型，每天收盘后生成，保存完整的市场状态：
- 市场情绪（冰点/修复/高潮/分歧/退潮）
- 情绪得分（0-100）
- 涨跌停统计
- 龙头股
- 热点板块
- 成交量
- 北向资金
- 风险指标
- 板块轮动
- 市场周期（冰点期/修复期/主升期/分歧期/退潮期）

#### MarketTrend
市场趋势分析结果：
- 情绪趋势
- 涨停家数趋势
- 板块轮动历史
- 龙头切换历史
- 市场周期变化历史

#### MarketInsight
市场洞察（AI生成的分析结论）

### 2. 市场状态引擎（`core/market_memory/engine.py`）

#### MarketStateEngine
核心大脑，负责：
- **analyze_market_cycle()**: 分析市场周期（冰点→修复→高潮→分歧→退潮）
- **analyze_emotion_trend()**: 分析情绪趋势（上升/下降/震荡）
- **analyze_sector_rotation()**: 分析板块轮动
- **analyze_leader_rotation()**: 分析龙头切换
- **analyze_risk_change()**: 分析风险变化
- **save_snapshot()**: 保存市场快照
- **get_recent_snapshots()**: 获取最近N天的市场快照
- **generate_market_trend()**: 生成市场趋势分析

### 3. 市场快照生成器（`core/market_memory/snapshot_generator.py`）

#### MarketSnapshotGenerator
每天收盘后生成完整的市场快照：
- 计算情绪得分（0-100）
- 判断市场情绪
- 获取最高连板
- 获取龙头股
- 获取热门板块
- 判断成交量趋势
- 获取北向资金
- 判断风险等级
- 检测龙头切换
- 获取指数涨跌
- 判断市场周期

### 4. 统一API（`core/market_memory/api.py`）

#### MarketMemory
提供便捷的接口：
- `create_snapshot()`: 创建市场快照
- `save_snapshot()`: 创建并保存市场快照
- `get_recent_snapshots()`: 获取最近N天的市场快照
- `get_latest_snapshot()`: 获取最新的市场快照
- `analyze_market_cycle()`: 分析市场周期
- `analyze_emotion_trend()`: 分析情绪趋势
- `analyze_sector_rotation()`: 分析板块轮动
- `analyze_leader_rotation()`: 分析龙头切换
- `analyze_risk_change()`: 分析风险变化
- `generate_market_trend()`: 生成市场趋势分析
- `get_market_context()`: 获取市场上下文（用于Agent分析）
- `format_market_context()`: 格式化市场上下文为易读字符串

## 🔧 集成到现有系统

### 1. MarketContext 扩展（`core/context.py`）

新增字段：
- `market_memory_context`: 市场记忆上下文

新增方法：
- `get_market_cycle()`: 获取市场周期
- `get_emotion_trend()`: 获取情绪趋势
- `get_sector_rotation()`: 获取板块轮动描述
- `get_leader_rotation()`: 获取龙头切换描述
- `get_risk_change()`: 获取风险变化描述
- `has_market_memory()`: 是否有市场记忆数据

### 2. DataProvider 集成（`core/data_provider.py`）

在构建 MarketContext 时自动加载市场记忆上下文（仅A股支持）。

### 3. Agent 升级

#### SentimentAgent（`agents/sentiment_agent.py`）
- `format_report()` 方法增加 `context` 参数
- 如果有市场记忆上下文，增加历史趋势展示

#### ControllerAgent（`agents/controller_agent.py`）
- 在 AI 报告生成时添加市场记忆上下文
- 在 `run_all_agents()` 中传递 context 给 SentimentAgent.format_report()

### 4. UI 升级（`app.py`）

#### Tab5 - 市场情绪周期
新增功能：
- **生成市场快照按钮**: 点击后生成并保存当前市场快照
- **市场记忆 - 历史趋势分析**:
  - 市场周期展示
  - 情绪趋势展示
  - 板块轮动展示
  - 龙头切换展示
  - 风险变化展示
- **趋势图表**:
  - 情绪得分折线图
  - 涨停家数折线图

## 📊 数据库表结构

### market_snapshots 表
```sql
CREATE TABLE IF NOT EXISTS market_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE,
    timestamp TEXT,
    market_sentiment TEXT,
    emotion_score REAL,
    limit_up_count INTEGER,
    limit_down_count INTEGER,
    highest_board INTEGER,
    rising_count INTEGER,
    falling_count INTEGER,
    flat_count INTEGER,
    rise_ratio REAL,
    total_volume REAL,
    volume_trend TEXT,
    north_money REAL,
    north_money_trend TEXT,
    bomb_rate REAL,
    risk_level TEXT,
    top_sectors TEXT,
    hot_theme TEXT,
    leaders TEXT,
    dragon_rotation INTEGER,
    rotation_from TEXT,
    rotation_to TEXT,
    market_cycle TEXT,
    cycle_stage TEXT,
    index_change TEXT,
    raw_data TEXT,
    created_at TEXT
)
```

### market_insights 表
```sql
CREATE TABLE IF NOT EXISTS market_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE,
    timestamp TEXT,
    current_state TEXT,
    state_description TEXT,
    trend_analysis TEXT,
    risk_alert TEXT,
    opportunity TEXT,
    action_suggestion TEXT,
    key_changes TEXT,
    confidence REAL,
    created_at TEXT
)
```

## 🧪 测试

运行测试脚本：
```bash
python3 test_market_memory.py
```

测试内容：
1. 生成市场快照
2. 保存市场快照
3. 读取历史快照
4. 分析市场周期
5. 分析情绪趋势
6. 分析板块轮动
7. 分析龙头切换
8. 分析风险变化
9. 生成市场趋势
10. 获取市场上下文

## 💡 使用示例

### 1. 生成市场快照
```python
from core.market_memory import MarketMemory
from modules.market_sentiment import get_market_sentiment

memory = MarketMemory()
sentiment_data = get_market_sentiment()
success = memory.save_snapshot(sentiment_data)
```

### 2. 获取市场上下文
```python
from core.market_memory import MarketMemory

memory = MarketMemory()
context = memory.get_market_context(days=5)

if context.get("has_context"):
    print(f"市场周期：{context['market_cycle']['cycle']}")
    print(f"情绪趋势：{context['emotion_trend']['direction']}")
    print(f"板块轮动：{context['sector_rotation']['description']}")
```

### 3. 在 Agent 中使用
```python
from core.context import MarketContext

def analyze(context: MarketContext):
    if context.has_market_memory():
        market_cycle = context.get_market_cycle()
        emotion_trend = context.get_emotion_trend()
        # 使用市场记忆数据进行分析
```

## 🎨 UI 展示效果

### Tab5 - 市场情绪周期
- 当前市场情绪数据展示
- 历史情绪记录
- **新增**：市场记忆 - 历史趋势分析
  - 市场周期（冰点期/修复期/主升期/分歧期/退潮期）
  - 情绪趋势（上升/下降/震荡）
  - 板块轮动
  - 龙头切换
  - 风险变化
- **新增**：趋势图表
  - 情绪得分折线图
  - 涨停家数折线图

### Agent 报告
- 情绪分析报告中增加历史趋势展示
- AI 最终报告中增加市场记忆上下文

## 🚀 核心优势

1. **时间序列推理**: 从单点数据升级为趋势分析
2. **市场状态机**: 理解市场周期（冰点→修复→高潮→分歧→退潮）
3. **动态分析**: 不仅看今天，还能理解历史演化
4. **智能决策**: 结合历史上下文，提供更准确的交易建议

## 📈 未来扩展

1. 自动化每日收盘后生成市场快照
2. AI 生成市场洞察（MarketInsight）
3. 更精确的龙头切换检测
4. 板块轮动预测
5. 风险预警系统
6. 交易信号生成

## 🎯 总结

通过实现市场记忆功能，系统已经从"单日分析"升级为"市场叙事分析"，具备了真正的"时间记忆能力"，能够理解市场故事，像专业交易员一样思考。
