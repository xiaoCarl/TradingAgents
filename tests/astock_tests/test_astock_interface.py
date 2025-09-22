# -*- coding: utf-8 -*-
"""
A股数据接口单元测试

测试A股数据采集的核心功能，包括：
1. 股票代码验证和标准化
2. 历史数据获取
3. 股票信息获取
4. 财务数据获取
5. 实时行情获取
6. 交易日历功能
"""

import unittest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tradingagents.dataflows.astock_interface import AStockData
from tradingagents.dataflows.astock_data.stock_code import AStockCode
from tradingagents.dataflows.astock_data.market_calendar import AStockCalendar


class TestAStockInterface(unittest.TestCase):
    """A股数据接口测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.astock = AStockData(cache_enabled=False)

    def test_initialization(self):
        """测试接口初始化"""
        # 测试正常初始化
        astock = AStockData(cache_enabled=False)
        self.assertIsNotNone(astock)
        self.assertFalse(astock.cache_enabled)

    def test_stock_code_validation(self):
        """测试股票代码验证"""
        # 测试有效代码
        valid_codes = [
            "000001", "000001.SZ", "sz000001", "SZ000001",
            "600000", "600000.SH", "sh600000", "SH600000",
            "300750", "300750.SZ", "sz300750",
            "688981", "688981.SH", "sh688981"
        ]
        
        for code in valid_codes:
            with self.subTest(code=code):
                self.assertTrue(self.astock.validate_symbol(code))
                std_code = AStockCode.standardize(code)
                self.assertIsNotNone(std_code)
                self.assertIn('.', std_code)

    def test_invalid_stock_codes(self):
        """测试无效股票代码"""
        invalid_codes = [
            "", "123", "1234567", "ABCDEF", "000000", "999999", 
            "000001.INVALID", "invalid_code"
        ]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                self.assertFalse(self.astock.validate_symbol(code))
                std_code = AStockCode.standardize(code)
                self.assertIsNone(std_code)

    def test_market_info(self):
        """测试市场信息获取"""
        test_cases = [
            ("000001", "主板"),
            ("600000", "主板"),
            ("300750", "创业板"),
            ("688981", "科创板")
        ]
        
        for code, expected_board in test_cases:
            with self.subTest(code=code):
                info = self.astock.get_market_info(code)
                self.assertIsInstance(info, dict)
                self.assertIn('board', info)
                self.assertIn('market', info)

    def test_date_validation(self):
        """测试日期验证"""
        # 测试有效日期
        valid_dates = [
            ("2024-01-01", "2024-01-31"),
            ("2023-12-01", "2024-01-01"),
            ("2024-01-15", "2024-01-15")
        ]
        
        for start_date, end_date in valid_dates:
            with self.subTest(start=start_date, end=end_date):
                # 通过交易日历验证日期格式
                calendar = AStockCalendar()
                try:
                    calendar.get_trading_days(start_date, end_date)
                    valid = True
                except Exception:
                    valid = False
                self.assertTrue(valid)

    def test_invalid_dates(self):
        """测试无效日期"""
        invalid_cases = [
            ("2024-13-01", "2024-01-31"),  # 无效月份
            ("2024-01-32", "2024-01-31"),  # 无效日期
            ("2024-01-31", "2024-01-01"),  # 开始日期晚于结束日期
            ("invalid", "2024-01-31"),     # 无效格式
        ]
        
        for start_date, end_date in invalid_cases:
            with self.subTest(start=start_date, end=end_date):
                calendar = AStockCalendar()
                try:
                    calendar.get_trading_days(start_date, end_date)
                    self.fail(f"应该抛出异常: {start_date} - {end_date}")
                except Exception:
                    pass  # 期望抛出异常

    @patch('tradingagents.dataflows.astock_data.tushare_client.TuShareClient')
    def test_get_stock_data_mock(self, mock_tushare):
        """测试历史数据获取（使用Mock）"""
        # 创建Mock客户端
        mock_client = MagicMock()
        mock_tushare.return_value = mock_client
        
        # 准备测试数据
        test_data = pd.DataFrame({
            'Open': [10.0, 10.5, 11.0],
            'High': [10.5, 11.0, 11.5],
            'Low': [9.8, 10.2, 10.8],
            'Close': [10.2, 10.8, 11.2],
            'Volume': [1000000, 1200000, 1100000]
        })
        mock_client.get_stock_data.return_value = test_data
        
        # 创建测试实例
        astock = AStockData(tushare_token="test_token", cache_enabled=False)
        
        # 测试数据获取
        result = astock.get_stock_data("000001", "2024-01-01", "2024-01-03")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertListEqual(list(result.columns), ['Open', 'High', 'Low', 'Close', 'Volume'])

    @patch('tradingagents.dataflows.astock_data.akshare_client.AkShareClient')
    def test_get_stock_info_mock(self, mock_akshare):
        """测试股票信息获取（使用Mock）"""
        # 创建Mock客户端
        mock_client = MagicMock()
        mock_akshare.return_value = mock_client
        
        # 准备测试数据
        mock_info = {
            'shortName': '平安银行',
            'longName': '平安银行股份有限公司',
            'sector': '金融业',
            'industry': '银行业',
            'marketCap': 200000000000,
            'currency': 'CNY'
        }
        mock_client.get_stock_info.return_value = mock_info
        
        # 创建测试实例
        astock = AStockData(prefer_tushare=False, cache_enabled=False)
        
        # 测试信息获取
        result = astock.get_stock_info("000001")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('shortName'), '平安银行')
        self.assertEqual(result.get('sector'), '金融业')

    def test_trading_calendar(self):
        """测试交易日历功能"""
        # 测试交易日获取
        trading_days = self.astock.get_trading_days("2024-01-01", "2024-01-10")
        self.assertIsInstance(trading_days, list)
        
        # 测试交易日判断
        is_trading = self.astock.is_trading_day("2024-01-02")
        self.assertIsInstance(is_trading, bool)
        
        # 测试周末非交易日
        weekend_day = self.astock.is_trading_day("2024-01-06")  # 周六
        # 注意：这里的结果取决于实际交易日历数据

    def test_empty_data_handling(self):
        """测试空数据处理"""
        with patch('tradingagents.dataflows.astock_data.akshare_client.AkShareClient') as mock_akshare:
            # 创建Mock客户端
            mock_client = MagicMock()
            mock_akshare.return_value = mock_client
            
            # 返回空数据
            mock_client.get_stock_data.return_value = pd.DataFrame()
            mock_client.get_stock_info.return_value = {}
            
            # 创建测试实例
            astock = AStockData(prefer_tushare=False, cache_enabled=False)
            
            # 测试空数据返回
            result = astock.get_stock_data("000001", "2024-01-01", "2024-01-03")
            self.assertTrue(result.empty)
            
            result = astock.get_stock_info("000001")
            self.assertEqual(result, {})

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效股票代码
        with self.assertRaises(ValueError):
            AStockCode.standardize("invalid_code")
            
        # 测试无效日期
        with self.assertRaises(ValueError):
            calendar = AStockCalendar()
            calendar.get_trading_days("invalid-date", "2024-01-31")

    def test_data_source_fallback(self):
        """测试数据源回退机制"""
        with patch('tradingagents.dataflows.astock_data.tushare_client.TuShareClient') as mock_tushare, \
             patch('tradingagents.dataflows.astock_data.akshare_client.AkShareClient') as mock_akshare:
            
            # TuShare失败，AkShare成功
            mock_tushare.side_effect = Exception("TuShare初始化失败")
            mock_ak_client = MagicMock()
            mock_akshare.return_value = mock_ak_client
            mock_ak_client.get_stock_data.return_value = pd.DataFrame({'Close': [10.0]})
            
            # 应该成功回退到AkShare
            astock = AStockData(tushare_token="invalid", cache_enabled=False)
            result = astock.get_stock_data("000001", "2024-01-01", "2024-01-01")
            self.assertIsInstance(result, pd.DataFrame)

    def test_different_stock_formats(self):
        """测试不同股票代码格式"""
        test_cases = [
            ("000001", "000001.SZ"),
            ("000001.SZ", "000001.SZ"),
            ("sz000001", "000001.SZ"),
            ("600000", "600000.SH"),
            ("600000.SH", "600000.SH"),
            ("sh600000", "600000.SH")
        ]
        
        for input_code, expected_std in test_cases:
            with self.subTest(input=input_code, expected=expected_std):
                std_code = AStockCode.standardize(input_code)
                self.assertEqual(std_code, expected_std)

    def test_financial_data_methods(self):
        """测试财务数据相关方法"""
        # 测试财务数据获取方法存在
        self.assertTrue(hasattr(self.astock, 'get_financial_data'))
        self.assertTrue(hasattr(self.astock, 'get_dividends'))
        
        # 测试方法签名
        import inspect
        sig = inspect.signature(self.astock.get_financial_data)
        self.assertIn('symbol', sig.parameters)
        self.assertIn('statement_type', sig.parameters)


if __name__ == '__main__':
    unittest.main()