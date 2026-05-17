# 数据结构优化总结

## 完成的工作

✅ 1. 统一数据库 market.db
   - 整合了所有数据模型到一个 SQLite 数据库
   - 分层结构：事实层 -> 计算层 -> 行为层

✅ 2. DataLake 数据湖
   - Parquet 格式存储原始 K线数据
   - 支持多市场 (cn/hk/us) 和频率 (daily/minute)
   - 已完成 2405 只股票的 CSV -> Parquet 迁移

✅ 3. 统一数据接口
   - data/unifier.py 提供统一数据访问
   - 优先 DataLake，fallback DataHub
   - 新增 DataLakeAdapter 支持 Parquet 格式

✅ 4. 旧文件备份
   - 所有旧数据库已备份到 deprecated_data/ 目录

## 数据访问方式

### 旧方式（已不推荐）
```python
# 分散访问各种数据库
```

### 新方式（推荐）
```python
from data.unifier import get_unified_provider

provider = get_unified_provider()
df = provider.get_ohlcv(code="000001", market="cn")
market_state = provider.get_latest_market_state()
```

### DataLake 直接访问
```python
from data.adapters.datalake_adapter import get_datalake_adapter

datalake = get_datalake_adapter()
df = datalake.get_stock_daily_df(code="000001", market="cn")
stocks = datalake.list_available_stocks()
```

## 数据目录结构

```
stock_ai/
├── datalake/                # 数据湖（Parquet）
│   └── cn/daily/
│       ├── SH/              # 上海交易所
│       ├── SZ/              # 深圳交易所
│       └── metadata.json    # 元数据
│
├── database/market.db       # 统一数据库（SQLite）
│
├── data/
│   ├── unifier.py           # 统一数据访问接口
│   └── adapters/
│       └── datalake_adapter.py  # DataLake 适配器
│
├── data/cn/daily/           # 原始 CSV 数据（备份）
│
└── deprecated_data/         # 旧数据备份
```

## 迁移脚本

```bash
# 运行数据迁移（扫描所有子目录）
python migrate_to_datalake.py

# 迁移结果
# 发现 5506 个CSV文件
# 迁移完成：5506 成功, 0 跳过
```

## 下一步

✅ 1. 将现有 OHLCV 数据迁移到 DataLake (Parquet) ✓ 已完成
✅ 2. 更新统一数据接口支持 DataLake ✓ 已完成
3. 启用 SnapshotEngine 进行每日离线计算
4. 更新所有模块使用新的统一接口
