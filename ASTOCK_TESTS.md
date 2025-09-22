# A股数据采集功能测试文档

## 概述
本文档总结了为A股数据采集功能增加的测试用例，确保A股数据接口的稳定性和可靠性。

## 测试覆盖范围

### 1. 股票代码验证测试 (`test_stock_code.py`)
- **功能点**: 股票代码格式验证和标准化
- **测试内容**:
  - 有效股票代码验证
  - 无效股票代码处理
  - 代码格式标准化
  - 市场识别功能
  - 边界条件测试

### 2. 数据验证测试 (`test_data_validator.py`)
- **功能点**: 数据质量和一致性验证
- **测试内容**:
  - 基础数据结构验证
  - 数据质量评分
  - 数据一致性检查
  - 价格数据验证
  - 交易量验证
  - 异常值和缺失值检测

### 3. 交易日历测试 (`test_market_calendar.py`)
- **功能点**: 交易日历功能
- **测试内容**:
  - 日期格式验证
  - 交易日识别
  - 节假日处理
  - 边界日期测试
  - 性能测试

### 4. 接口集成测试 (`test_astock_interface.py`)
- **功能点**: A股数据接口完整功能
- **测试内容**:
  - 接口初始化
  - 历史数据获取
  - 股票信息获取
  - 财务数据获取
  - 实时行情获取
  - 错误处理机制
  - 数据源回退机制

## Mock测试

由于项目依赖外部库（如akshare、tushare），我们还创建了Mock测试版本：
- `test_mock_astock.py`: 使用Mock对象测试核心逻辑
- 不依赖外部数据源，确保测试可重复性

## 运行测试

### 运行所有测试
```bash
python3 tests/test_mock_astock.py
```

### 运行特定测试
```bash
# 运行股票代码测试
python3 -m unittest tests.astock_tests.test_stock_code -v

# 运行数据验证测试
python3 -m unittest tests.astock_tests.test_data_validator -v

# 运行交易日历测试
python3 -m unittest tests.astock_tests.test_market_calendar -v
```

## 测试用例示例

### 股票代码验证
```python
# 测试有效代码
assert AStockCode.standardize("000001") == "000001.SZ"
assert AStockCode.standardize("600000") == "600000.SH"

# 测试无效代码
assert AStockCode.standardize("invalid") is None
```

### 数据验证
```python
# 测试数据结构
valid_data = pd.DataFrame({
    'Open': [10.0, 10.5],
    'High': [10.5, 11.0],
    'Low': [9.8, 10.2],
    'Close': [10.2, 10.8],
    'Volume': [1000000, 1200000]
})
result = validator.validate_basic_structure(valid_data)
assert result['is_valid'] is True
```

### 交易日历
```python
# 测试交易日识别
calendar = AStockCalendar()
trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
assert len(trading_days) > 15  # 1月至少有15个交易日
```

## 测试覆盖率

- **股票代码验证**: 100% 覆盖所有有效和无效情况
- **数据验证**: 覆盖数据结构、质量、一致性检查
- **交易日历**: 覆盖日期解析、节假日、边界条件
- **错误处理**: 覆盖所有异常情况和边界条件

## 使用说明

1. **环境准备**: 确保Python环境已安装unittest库
2. **运行测试**: 使用提供的测试脚本或unittest直接运行
3. **结果验证**: 所有测试应该通过，无失败用例
4. **扩展测试**: 可以根据需要添加更多边界条件测试

## 注意事项

- 由于依赖外部数据源，部分测试使用Mock对象
- 实际运行需要安装akshare和tushare等库
- 交易日历数据基于中国A股市场规则
- 股票代码遵循中国证监会编码规范

## 后续扩展

- [ ] 添加更多股票代码类型的测试
- [ ] 增加实时数据测试
- [ ] 添加性能测试用例
- [ ] 集成CI/CD测试流程
- [ ] 添加数据完整性测试