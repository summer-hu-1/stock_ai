# 数据结构优化总结

## 完成的工作

✅ 1. 统一数据库 market.db
   - 整合了所有数据模型到一个 SQLite 数据库
   - 分层结构：事实层 -> 计算层 -> 行为层

✅ 2. DataLake 数据湖
   - Parquet 格式存储原始 K线数据
   - 支持多市场 (cn/hk/us) 和频率 (daily/minute)

✅ 3. 统一数据接口
   - data/unifier.py 提供统一数据访问
   - 优先 DataLake，fallback DataHub

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

## 数据目录结构

```
stock_ai/
├── data_lake/              # 数据湖（Parquet）
│   ├── cn/daily/
│   ├── cn/minute/
│   ├── hk/
│   └── us/
│
├── database/market.db      # 统一数据库（SQLite）
│
├── data/unifier.py         # 统一数据访问接口
│
└── deprecated_data/        # 旧数据备份
```

## 下一步

1. 将现有 OHLCV 数据迁移到 DataLake (Parquet)
2. 启用 SnapshotEngine 进行每日离线计算
3. 更新所有模块使用新的统一接口
