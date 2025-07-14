# A股数据模块 - 中国A股专业数据接口

## 功能概述

本模块提供完整的中国A股市场数据支持，包括：

- **历史行情数据**：日线、周线、月线
- **公司基本信息**：行业、地区、主营业务等
- **财务数据**：资产负债表、利润表、现金流量表
- **分红数据**：历史分红、送股、配股记录
- **交易日历**：A股交易日、节假日安排
- **数据验证**：涨跌停、停牌、数据完整性检查

## 快速开始

### 1. 安装依赖

```bash
# 安装必要的Python包
pip install tushare akshare pandas numpy

# 设置TuShare token（推荐）
export TUSHARE_TOKEN=your_tushare_token_here
```

### 2. 基本使用

```python
from tradingagents.dataflows.astock_interface import AStockData

# 创建A股数据接口
astock = AStockData()

# 获取历史数据
data = astock.get_stock_data("000001", "2024-01-01", "2024-12-31")
print(f"获取到{len(data)}条数据")

# 获取公司信息
info = astock.get_stock_info("000001")
print(f"公司名称: {info.get('shortName')}")
```

### 3. 智能数据源选择

```python
from tradingagents.dataflows.data_selector import get_stock_data_auto

# 自动识别市场并获取数据
# A股会自动使用AStockData，美股使用YFinance
astock_data = get_stock_data_auto("000001", "2024-01-01", "2024-12-31")
us_stock_data = get_stock_data_auto("AAPL", "2024-01-01", "2024-12-31")
```

## 支持的A股代码格式

### 标准格式
- `000001.SZ` - 深市股票
- `600000.SH` - 沪市股票
- `300750.SZ` - 创业板股票
- `688981.SH` - 科创板股票

### 兼容格式
- `000001` - 省略后缀，自动识别
- `sz000001` - 前缀格式
- `SZ000001` - 大写前缀格式

## 市场分类

| 前缀 | 市场 | 板块 |
|------|------|------|
| 600/601/603/605 | SH | 沪市主板 |
| 000/001/002/003 | SZ | 深市主板/中小板 |
| 300/301 | SZ | 创业板 |
| 688/689 | SH | 科创板 |
| 830/831/832/833/835-839 | BJ | 北交所 |

## 核心功能

### 1. 股票数据获取

```python
from tradingagents.dataflows.astock_interface import AStockData

astock = AStockData()

# 获取历史行情
data = astock.get_stock_data(
    symbol="000001",
    start_date="2024-01-01",
    end_date="2024-12-31",
    method="auto"  # 可选: "tushare", "akshare", "auto"
)

# 数据格式与yfinance兼容
# 包含: Open, Close, High, Low, Volume, Amount
```

### 2. 公司信息

```python
info = astock.get_stock_info("000001")
print(info.keys())
# ['symbol', 'shortName', 'longName', 'industry', 'sector', 
#  'country', 'currency', 'exchange', 'marketCap', 'list_date']
```

### 3. 财务数据

```python
# 获取财务报表
income_stmt = astock.get_financial_data("000001", "income")
balance_sheet = astock.get_financial_data("000001", "balance")
cash_flow = astock.get_financial_data("000001", "cashflow")
```

### 4. 交易日历

```python
from tradingagents.dataflows.astock_data.market_calendar import AStockCalendar

calendar = AStockCalendar()

# 检查交易日
is_trading = calendar.is_trading_day("2024-01-02")

# 获取交易日列表
trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")

# 获取下一个交易日
next_day = calendar.next_trading_day("2024-01-01")
```

### 5. 数据验证

```python
from tradingagents.dataflows.astock_data.data_validator import AStockDataValidator

validator = AStockDataValidator()

# 验证数据完整性
report = validator.get_validation_report(data, "000001", "2024-01-01", "2024-12-31")
print(f"数据质量评分: {report['overall_score']}/100")
```

## 配置选项

在 `default_config.py` 中添加A股相关配置：

```python
DEFAULT_CONFIG = {
    # ... 原有配置 ...
    
    "astock": {
        "tushare_token": os.getenv("TUSHARE_TOKEN", ""),
        "prefer_tushare": True,      # 优先使用TuShare
        "cache_enabled": True,       # 启用缓存
        "cache_timeout": 3600,       # 缓存超时时间（秒）
        "max_retries": 3,            # 最大重试次数
        "retry_delay": 1,            # 重试延迟（秒）
    },
}
```

## 环境变量配置

```bash
# TuShare API Token (可选，但推荐使用)
export TUSHARE_TOKEN=your_tushare_token_here

# 数据缓存目录
export TRADINGAGENTS_RESULTS_DIR=./results

# A股配置
export AStock_PREFER_TUSHARE=true
export AStock_CACHE_ENABLED=true
```

## 使用示例

### 集成到现有代码

```python
from tradingagents.dataflows.data_selector import get_data_selector

# 替换原有的yfinance调用
selector = get_data_selector()

# 现在可以处理A股和美股
data = selector.get_stock_data("000001", "2024-01-01", "2024-12-31")
us_data = selector.get_stock_data("AAPL", "2024-01-01", "2024-12-31")
```

### 批量处理

```python
# 同时处理多个股票
symbols = ["000001", "600000", "300750", "AAPL", "TSLA"]

for symbol in symbols:
    market = selector.identify_market(symbol)
    data = selector.get_stock_data(symbol, "2024-01-01", "2024-12-31")
    print(f"{symbol} ({market}): {len(data)}条数据")
```

## 注意事项

### 1. 数据限制
- **TuShare**: 每日免费额度有限，建议缓存数据
- **AkShare**: 无限制，但速度较慢，建议作为备用

### 2. 时间区域
- A股数据时间为中国标准时间（UTC+8）
- 美股数据时间为美国东部时间（UTC-5/-4）

### 3. 数据更新
- A股数据通常在交易结束后1小时内更新
- 建议缓存历史数据，减少API调用

### 4. 错误处理
- 自动重试机制（最多3次）
- 优雅降级到备用数据源
- 详细错误日志

## 故障排除

### 常见问题

1. **TuShare token未设置**
   ```
   ValueError: TuShare token未提供
   ```
   解决：设置环境变量 `export TUSHARE_TOKEN=your_token`

2. **数据获取失败**
   ```
   警告: 未获取到数据，尝试备用数据源...
   ```
   解决：检查网络连接，尝试使用AkShare

3. **股票代码格式错误**
   ```
   ValueError: 无效的股票代码
   ```
   解决：使用标准格式，如 `000001.SZ`

### 性能优化

1. **启用缓存**（默认开启）
2. **批量查询**减少API调用
3. **合理设置日期范围**

## 更新日志

- **v1.0.0**: 初始版本，支持A股历史数据获取
- **v1.1.0**: 增加交易日历和数据验证功能
- **v1.2.0**: 优化数据源选择器，支持美股A股无缝切换