# -*- coding: utf-8 -*-
"""
A股数据验证测试

测试A股数据的质量验证和错误处理功能
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tradingagents.dataflows.astock_data.data_validator import AStockDataValidator


class TestAStockDataValidator(unittest.TestCase):
    """A股数据验证器测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.validator = AStockDataValidator()

    def test_basic_validation(self):
        """测试基础数据验证"""
        # 创建有效的基础数据
        valid_data = pd.DataFrame({
            'Open': [10.0, 10.5, 11.0],
            'High': [10.5, 11.0, 11.5],
            'Low': [9.8, 10.2, 10.8],
            'Close': [10.2, 10.8, 11.2],
            'Volume': [1000000, 1200000, 1100000]
        })
        
        result = self.validator.validate_basic_structure(valid_data)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['missing_columns'], [])
        self.assertEqual(result['warnings'], [])

    def test_missing_columns(self):
        """测试缺失列检测"""
        # 创建缺失列的数据
        incomplete_data = pd.DataFrame({
            'Open': [10.0, 10.5],
            'Close': [10.2, 10.8]
            # 缺少 High, Low, Volume
        })
        
        result = self.validator.validate_basic_structure(incomplete_data)
        
        self.assertFalse(result['is_valid'])
        self.assertIn('High', result['missing_columns'])
        self.assertIn('Low', result['missing_columns'])
        self.assertIn('Volume', result['missing_columns'])

    def test_data_quality_validation(self):
        """测试数据质量验证"""
        # 创建高质量数据
        high_quality_data = pd.DataFrame({
            'Open': [10.0, 10.5, 11.0, 10.8],
            'High': [10.5, 11.0, 11.5, 11.2],
            'Low': [9.8, 10.2, 10.8, 10.5],
            'Close': [10.2, 10.8, 11.2, 10.9],
            'Volume': [1000000, 1200000, 1100000, 1300000]
        })
        
        result = self.validator.validate_data_quality(high_quality_data)
        
        self.assertTrue(result['is_valid'])
        self.assertGreater(result['quality_score'], 80)

    def test_data_consistency_validation(self):
        """测试数据一致性验证"""
        # 创建数据一致性测试
        consistent_data = pd.DataFrame({
            'Open': [10.0, 10.5, 11.0],
            'High': [10.5, 11.0, 11.5],
            'Low': [9.8, 10.2, 10.8],
            'Close': [10.2, 10.8, 11.2],
            'Volume': [1000000, 1200000, 1100000]
        })
        
        result = self.validator.validate_data_consistency(consistent_data)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['inconsistencies']), 0)

    def test_price_consistency(self):
        """测试价格数据一致性"""
        # 创建价格一致的数据
        consistent_prices = pd.DataFrame({
            'Open': [10.0, 10.5],
            'High': [10.5, 11.0],
            'Low': [9.8, 10.2],
            'Close': [10.2, 10.8]
        })
        
        result = self.validator.validate_price_consistency(consistent_prices)
        self.assertTrue(result['is_valid'])
        
        # 创建价格不一致的数据
        inconsistent_prices = pd.DataFrame({
            'Open': [10.0, 10.5],
            'High': [9.5, 10.0],  # High < Open
            'Low': [10.5, 11.0],  # Low > Open
            'Close': [10.2, 10.8]
        })
        
        result = self.validator.validate_price_consistency(inconsistent_prices)
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['inconsistencies']), 0)

    def test_volume_validation(self):
        """测试交易量验证"""
        # 创建正常交易量数据
        normal_volume = pd.DataFrame({
            'Volume': [1000000, 1200000, 800000]
        })
        
        result = self.validator.validate_volume_data(normal_volume)
        self.assertTrue(result['is_valid'])
        
        # 创建异常交易量数据
        abnormal_volume = pd.DataFrame({
            'Volume': [1000000, 0, -500000, 50000000]  # 包含0和负值
        })
        
        result = self.validator.validate_volume_data(abnormal_volume)
        self.assertFalse(result['is_valid'])

    def test_gaps_and_outliers(self):
        """测试数据缺口和异常值"""
        # 创建连续数据
        continuous_data = pd.DataFrame({
            'Close': [10.0, 10.1, 10.2, 10.3, 10.4],
            'Volume': [1000000, 1100000, 1050000, 1200000, 1150000]
        })
        
        result = self.validator.validate_gaps_and_outliers(continuous_data)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['gaps']), 0)
        self.assertEqual(len(result['outliers']), 0)

    def test_comprehensive_validation(self):
        """测试综合验证报告"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'Open': [10.0, 10.5, 11.0, 10.8, 11.2],
            'High': [10.5, 11.0, 11.5, 11.2, 11.6],
            'Low': [9.8, 10.2, 10.8, 10.5, 10.9],
            'Close': [10.2, 10.8, 11.2, 10.9, 11.4],
            'Volume': [1000000, 1200000, 1100000, 1300000, 1250000]
        })
        
        # 生成验证报告
        report = self.validator.get_validation_report(
            test_data, "000001.SZ", "2024-01-01", "2024-01-05"
        )
        
        self.assertIsInstance(report, dict)
        self.assertIn('overall_score', report)
        self.assertIn('basic_validation', report)
        self.assertIn('quality_validation', report)
        self.assertIn('consistency_validation', report)
        self.assertIn('summary', report)
        
        self.assertGreaterEqual(report['overall_score'], 0)
        self.assertLessEqual(report['overall_score'], 100)

    def test_empty_data_validation(self):
        """测试空数据验证"""
        empty_data = pd.DataFrame()
        
        result = self.validator.validate_basic_structure(empty_data)
        self.assertFalse(result['is_valid'])
        
        report = self.validator.get_validation_report(
            empty_data, "000001.SZ", "2024-01-01", "2024-01-01"
        )
        self.assertEqual(report['overall_score'], 0)

    def test_negative_values(self):
        """测试负值检测"""
        # 创建包含负值的数据
        negative_values = pd.DataFrame({
            'Open': [10.0, -10.5, 11.0],
            'High': [10.5, 11.0, -11.5],
            'Low': [-9.8, 10.2, 10.8],
            'Close': [10.2, 10.8, 11.2],
            'Volume': [1000000, 1200000, -500000]
        })
        
        result = self.validator.validate_data_quality(negative_values)
        self.assertFalse(result['is_valid'])
        self.assertIn('negative_values', result['issues'])

    def test_duplicate_data(self):
        """测试重复数据检测"""
        # 创建重复数据
        duplicate_data = pd.DataFrame({
            'Close': [10.0, 10.5, 10.0, 10.5],
            'Volume': [1000000, 1200000, 1000000, 1200000]
        })
        
        result = self.validator.validate_data_quality(duplicate_data)
        self.assertIn('duplicate_rows', result['issues'])

    def test_zero_values(self):
        """测试零值检测"""
        # 创建零值数据
        zero_data = pd.DataFrame({
            'Open': [0, 10.5, 11.0],
            'High': [10.5, 0, 11.5],
            'Low': [9.8, 10.2, 0],
            'Close': [0, 0, 0],
            'Volume': [1000000, 0, 1100000]
        })
        
        result = self.validator.validate_data_quality(zero_data)
        self.assertIn('zero_values', result['issues'])


if __name__ == '__main__':
    unittest.main()