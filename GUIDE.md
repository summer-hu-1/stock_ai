# 龙抬头识别系统 - 开发指南与核心指令记录

---

## 一、项目概览

这是一个**A股市场结构识别系统**，从单市场股票工具逐步演进为完整的因子+信号+龙头识别体系。

**核心模块架构：**
```
数据源层 → Factor Engine → Signal Engine → Leader Engine → 验证系统
```

---

## 二、开发历程与核心指令

### 阶段1：基础架构搭建

| 序号 | 指令 | 实现内容 | 文件 |
|------|------|----------|------|
| 1 | 实现MarketContext统一数据层 | 集中管理股票数据、市场情绪、板块数据 | `core/context.py` |
| 2 | 实现DataProvider统一数据提供者 | 从AkShare/yfinance获取数据 | `core/base_provider.py` |
| 3 | 实现多市场数据路由系统 | 支持A股、港股、美股自动切换 | `core/provider_factory.py` |
| 4 | 实现Market Registry | 市场配置注册表 | `core/market_registry.py` |
| 5 | 实现Symbol Resolver | 股票名称/代码转换 | `core/symbol_resolver.py` |

### 阶段2：本地数据中心

| 序号 | 指令 | 实现内容 | 文件 |
|------|------|----------|------|
| 6 | 实现本地A股历史日线数据中心 | 自动拉取A股3年日线 | `data_sync/sync_cn_daily.py` |
| 7 | 实现增量数据更新 | 只更新最新交易日 | `data_sync/update_cn_daily.py` |
| 8 | 实现CSV数据访问层 | 按股票代码存储CSV | `core/csv_provider.py` |

### 阶段3：因子工程系统 (V8.1)

| 序号 | 指令 | 实现内容 | 文件 |
|------|------|----------|------|
| 9 | 实现趋势因子 | MA5/10/20/60、多头排列 | `factors/trend_factor.py` |
| 10 | 实现成交量因子 | 量比、放量突破检测 | `factors/volume_factor.py` |
| 11 | 实现动量因子 | 动量排名、相对强度 | `factors/momentum_factor.py` |
| 12 | 实现波动率因子 | ATR、振幅 | `factors/volatility_factor.py` |
| 13 | 实现强度因子 | 价格强度、成交量强度 | `factors/strength_factor.py` |
| 14 | 实现FactorEngine | 统一因子调度 | `factors/factor_engine.py` |

### 阶段4：信号系统 (V8.2)

| 序号 | 指令 | 实现内容 | 文件 |
|------|------|----------|------|
| 15 | 实现突破信号 | 20日/60日新高、放量突破 | `signals/breakout_signal.py` |
| 16 | 实现趋势信号 | 均线排列、金叉死叉 | `signals/trend_signal.py` |
| 17 | 实现反转信号 | 底部反弹、长上下影线 | `signals/reversal_signal.py` |
| 18 | 实现成交量信号 | 量价齐升、缩量盘整 | `signals/volume_signal.py` |
| 19 | 实现SignalEngine | 统一信号调度与综合 | `signals/signal_engine.py` |

### 阶段5：龙头识别系统 (V8.3)

| 序号 | 指令 | 实现内容 | 文件 |
|------|------|----------|------|
| 20 | 实现龙头识别器 | 评分系统、连板检测 | `leaders/leader_detector.py` |
| 21 | 实现涨停信号 | 连续涨停、逼近涨跌停 | `leaders/limitup_signal.py` |
| 22 | 实现板块龙头分析 | 板块分析、龙头对比 | `leaders/sector_leader.py` |
| 23 | 实现龙头排名器 | 多股票排名、龙头汇总 | `leaders/dragon_ranker.py` |
| 24 | 实现LeaderEngine | 统一龙头调度 | `leaders/leader_engine.py` |

### 阶段6：系统验证 (V8.4)

| 序号 | 指令 | 实现内容 | 文件 |
|------|------|----------|------|
| 25 | 实现回测框架 | 交易记录、收益曲线、夏普比率 | `validation/backtester.py` |
| 26 | 实现信号验证 | 信号胜率统计、多股票验证 | `validation/signal_validator.py` |
| 27 | 实现因子分析 | IC计算、分位数收益 | `validation/factor_analyzer.py` |
| 28 | 实现模拟交易 | 投资组合管理、实时更新 | `validation/simulator.py` |
| 29 | 实现验证引擎 | 统一验证入口、报告生成 | `validation/validation_engine.py` |

---

## 三、核心算法原理

### 1. 因子计算流程

```python
# 因子输入输出规范
input:  DataFrame(OHLCV)
output: Dict包含5个因子维度
{
    "trend": {"ma5": 14.5, "ma_bullish": True, "trend_strength": 72},
    "volume": {"volume_ratio": 2.3, "volume_breakout": True},
    "momentum": {"return_5d": 5.2, "momentum_score": 68},
    "volatility": {"atr": 0.8, "amplitude": 3.5},
    "strength": {"combined_strength": 75},
    "summary": {"overall_score": 70, "bullish_signals": 3}
}
```

### 2. 信号生成流程

```python
# 信号输入输出规范
input:  DataFrame + Factors
output: Dict包含信号方向和强度
{
    "breakout": {"signal": "breakout_20d", "direction": "bullish", "strength": 78},
    "trend": {"signal": "ma_bullish", "direction": "bullish", "strength": 72},
    "summary": {"overall_direction": "bullish", "overall_strength": 75}
}
```

### 3. 龙头评分算法

```python
leader_score = (
    limit_up_score * 0.30 +   # 涨停连板（权重最高）
    momentum_score * 0.25 +   # 价格动量
    volume_score * 0.20 +     # 成交量关注度
    turnover_score * 0.15 +   # 换手率活跃度
    strength_score * 0.10     # 综合强度
)
```

### 4. 龙头类型判定

| 类型 | 条件 | 业务含义 |
|------|------|----------|
| **龙头** | 评分≥85 且 连板≥2 | 市场核心领涨股 |
| **强势股** | 评分≥75 且 动量≥70 | 板块强势股 |
| **活跃股** | 评分≥65 且 涨停≥1 | 高活跃度股票 |
| **潜力股** | 评分≥60 | 具备龙头潜力 |
| **普通** | 评分<60 | 非龙头股票 |

---

## 四、目录结构

```
stock_ai/
├── core/                    # 核心模块
│   ├── csv_provider.py     # CSV数据访问
│   ├── market_registry.py   # 市场配置
│   ├── symbol_resolver.py   # 股票解析
│   └── provider_factory.py  # 数据源工厂
│
├── factors/                 # 因子系统 (V8.1)
│   ├── base_factor.py
│   ├── trend_factor.py      # 趋势因子
│   ├── volume_factor.py     # 成交量因子
│   ├── momentum_factor.py    # 动量因子
│   ├── volatility_factor.py  # 波动率因子
│   ├── strength_factor.py    # 强度因子
│   └── factor_engine.py     # 因子引擎
│
├── signals/                 # 信号系统 (V8.2)
│   ├── base_signal.py
│   ├── breakout_signal.py   # 突破信号
│   ├── trend_signal.py      # 趋势信号
│   ├── reversal_signal.py    # 反转信号
│   ├── volume_signal.py     # 成交量信号
│   └── signal_engine.py     # 信号引擎
│
├── leaders/                 # 龙头系统 (V8.3)
│   ├── base_leader.py
│   ├── leader_detector.py   # 龙头识别
│   ├── limitup_signal.py    # 涨停信号
│   ├── sector_leader.py     # 板块龙头
│   ├── dragon_ranker.py     # 龙头排名
│   └── leader_engine.py     # 龙头引擎
│
├── validation/              # 验证系统 (V8.4)
│   ├── backtester.py       # 回测框架
│   ├── signal_validator.py  # 信号验证
│   ├── factor_analyzer.py   # 因子分析
│   ├── simulator.py         # 模拟交易
│   └── validation_engine.py  # 验证引擎
│
├── providers/               # 数据源
│   ├── ashare_provider.py   # A股
│   ├── hk_provider.py       # 港股
│   └── us_provider.py       # 美股
│
├── data_sync/               # 数据同步
│   ├── get_stock_list.py    # 获取股票列表
│   ├── sync_cn_daily.py     # 同步3年日线
│   └── update_cn_daily.py   # 增量更新
│
├── data/                    # 数据存储
│   └── cn/
│       ├── stock_list.csv   # 股票列表
│       └── daily/           # 日线CSV
│
└── app.py                   # 主程序入口
```

---

## 五、快速使用示例

### 完整流程示例

```python
# 1. 加载数据
from core.csv_provider import CSVProvider
provider = CSVProvider()
df = provider.get_stock_daily("000001")

# 2. 计算因子
from factors.factor_engine import FactorEngine
factor_engine = FactorEngine()
factors = factor_engine.calculate(df)

# 3. 生成信号
from signals.signal_engine import SignalEngine
signal_engine = SignalEngine()
signals = signal_engine.generate(df, factors)

# 4. 龙头识别
from leaders.leader_engine import LeaderEngine
leader_engine = LeaderEngine()
leader = leader_engine.analyze(df, factors, signals)

# 5. 系统验证
from validation.validation_engine import ValidationEngine
validator = ValidationEngine()
result = validator.validate_single_stock(df, factors, signals, leader)
print(validator.generate_report(result))
```

---

## 六、问题解决记录

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `st.autocomplete`不存在 | Streamlit版本问题 | 替换为`st.selectbox` |
| ProxyError无法访问API | 代理设置问题 | 禁用代理环境变量 |
| TypeError: NoneType不可下标 | 网络问题导致None | 添加None检查和模拟数据 |
| 信号验证缺少scipy | 依赖缺失 | 实现自定义相关性计算 |

---

## 七、环境要求

```bash
Python >= 3.8

pip install pandas numpy
pip install akshare streamlit
```

---

## 八、启动方式

```bash
cd stock_ai
streamlit run app.py
```

---

*版本：V8.4 Factor + Signal + Leader + Validation*
*最后更新：2026-05-10*
