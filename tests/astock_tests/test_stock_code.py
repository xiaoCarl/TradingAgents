# -*- coding: utf-8 -*-
"""
A股股票代码验证测试

测试股票代码的格式验证、标准化和市场识别功能
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tradingagents.dataflows.astock_data.stock_code import AStockCode


class TestAStockCode(unittest.TestCase):
    """A股股票代码测试类"""

    def test_standardize_valid_codes(self):
        """测试有效股票代码的标准化"""
        test_cases = [
            # 主板股票
            ("000001", "000001.SZ"),
            ("000001.SZ", "000001.SZ"),
            ("SZ000001", "000001.SZ"),
            ("sz000001", "000001.SZ"),
            
            # 主板股票
            ("600000", "600000.SH"),
            ("600000.SH", "600000.SH"),
            ("SH600000", "600000.SH"),
            ("sh600000", "600000.SH"),
            
            # 创业板股票
            ("300750", "300750.SZ"),
            ("300750.SZ", "300750.SZ"),
            ("SZ300750", "300750.SZ"),
            
            # 科创板股票
            ("688981", "688981.SH"),
            ("688981.SH", "688981.SH"),
            ("SH688981", "688981.SH"),
            
            # 北交所股票
            ("830799", "830799.BJ"),
            ("830799.BJ", "830799.BJ"),
            ("BJ830799", "830799.BJ"),
            
            # 中小板股票
            ("002415", "002415.SZ"),
            ("002415.SZ", "002415.SZ"),
        ]
        
        for input_code, expected in test_cases:
            with self.subTest(input=input_code, expected=expected):
                result = AStockCode.standardize(input_code)
                self.assertEqual(result, expected)

    def test_standardize_invalid_codes(self):
        """测试无效股票代码的标准化"""
        invalid_codes = [
            "", "1", "12", "123", "1234", "12345",          # 长度不足
            "1234567", "12345678", "123456789",             # 长度过长
            "ABCDEF", "abc123", "12!@#", "000001.XX",      # 无效字符或后缀
            "000000", "999999", "000000.SZ", "999999.SH",  # 不存在的代码
            "000001.sz", "600000.sh",                       # 小写后缀
            "invalid", "stock", "test",                     # 纯文本
        ]
        
        for invalid_code in invalid_codes:
            with self.subTest(code=invalid_code):
                result = AStockCode.standardize(invalid_code)
                self.assertIsNone(result)

    def test_is_valid(self):
        """测试股票代码有效性验证"""
        valid_codes = [
            "000001", "000001.SZ", "SZ000001", "sz000001",
            "600000", "600000.SH", "SH600000", "sh600000",
            "300750", "300750.SZ", "SZ300750",
            "688981", "688981.SH", "SH688981",
            "002415", "002415.SZ", "SZ002415",
            "830799", "830799.BJ", "BJ830799"
        ]
        
        for code in valid_codes:
            with self.subTest(code=code):
                self.assertTrue(AStockCode.is_valid(code))

    def test_is_invalid(self):
        """测试无效股票代码验证"""
        invalid_codes = [
            "", "123", "1234567", "ABCDEF", "000001.INVALID",
            "000000", "999999", "invalid", "stock123"
        ]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                self.assertFalse(AStockCode.is_valid(code))

    def test_get_market_info(self):
        """测试市场信息获取"""
        test_cases = [
            # (代码, 预期市场, 预期板块)
            ("000001", "SZ", "主板"),
            ("000001.SZ", "SZ", "主板"),
            ("600000", "SH", "主板"),
            ("600000.SH", "SH", "主板"),
            ("300750", "SZ", "创业板"),
            ("300750.SZ", "SZ", "创业板"),
            ("688981", "SH", "科创板"),
            ("688981.SH", "SH", "科创板"),
            ("002415", "SZ", "中小板"),
            ("002415.SZ", "SZ", "中小板"),
            ("830799", "BJ", "北交所"),
            ("830799.BJ", "BJ", "北交所"),
        ]
        
        for code, expected_market, expected_board in test_cases:
            with self.subTest(code=code):
                info = AStockCode.get_market_info(code)
                self.assertIsInstance(info, dict)
                self.assertEqual(info['market'], expected_market)
                self.assertEqual(info['board'], expected_board)

    def test_market_info_invalid_codes(self):
        """测试无效代码的市场信息获取"""
        invalid_codes = ["", "invalid", "123456", "999999"]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                info = AStockCode.get_market_info(code)
                self.assertEqual(info, {})

    def test_code_pattern_matching(self):
        """测试代码模式匹配"""
        # 测试主板股票
        main_board_sz = ["000001", "000002", "000999"]
        for code in main_board_sz:
            info = AStockCode.get_market_info(code)
            self.assertEqual(info['market'], "SZ")
            self.assertEqual(info['board'], "主板")
        
        main_board_sh = ["600000", "600999", "601000", "603000"]
        for code in main_board_sh:
            info = AStockCode.get_market_info(code)
            self.assertEqual(info['market'], "SH")
            self.assertEqual(info['board'], "主板")
        
        # 测试创业板
        chi_next = ["300001", "300999", "301000"]
        for code in chi_next:
            info = AStockCode.get_market_info(code)
            self.assertEqual(info['market'], "SZ")
            self.assertEqual(info['board'], "创业板")
        
        # 测试科创板
        star_market = ["688001", "688999"]
        for code in star_market:
            info = AStockCode.get_market_info(code)
            self.assertEqual(info['market'], "SH")
            self.assertEqual(info['board'], "科创板")
        
        # 测试中小板
        sme_board = ["002001", "002999", "003000"]
        for code in sme_board:
            info = AStockCode.get_market_info(code)
            self.assertEqual(info['market'], "SZ")
            self.assertEqual(info['board'], "中小板")
        
        # 测试北交所
        bse = ["830000", "839999", "870000", "889999"]
        for code in bse:
            info = AStockCode.get_market_info(code)
            self.assertEqual(info['market'], "BJ")
            self.assertEqual(info['board'], "北交所")

    def test_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            # 最小有效代码
            ("000001", "000001.SZ"),
            ("600000", "600000.SH"),
            ("300001", "300001.SZ"),
            ("688001", "688001.SH"),
            ("002001", "002001.SZ"),
            ("830001", "830001.BJ"),
            
            # 最大有效代码
            ("000999", "000999.SZ"),
            ("600999", "600999.SH"),
            ("300999", "300999.SZ"),
            ("688999", "688999.SH"),
            ("002999", "002999.SZ"),
            ("839999", "839999.BJ"),
        ]
        
        for input_code, expected in edge_cases:
            with self.subTest(input=input_code):
                result = AStockCode.standardize(input_code)
                self.assertEqual(result, expected)

    def test_format_consistency(self):
        """测试格式一致性"""
        # 测试所有标准化后的代码都遵循相同的格式
        codes = ["000001", "600000", "300750", "688981", "002415", "830799"]
        
        for code in codes:
            std_code = AStockCode.standardize(code)
            if std_code:
                # 检查格式: 6位数字 + 点 + 2位市场代码
                self.assertTrue(std_code.count('.') == 1)
                parts = std_code.split('.')
                self.assertEqual(len(parts[0]), 6)
                self.assertEqual(len(parts[1]), 2)
                self.assertTrue(parts[1] in ['SH', 'SZ', 'BJ'])

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        test_cases = [
            ("000001", "000001.SZ"),
            ("000001.sz", "000001.SZ"),
            ("SZ000001", "000001.SZ"),
            ("sz000001", "000001.SZ"),
        ]
        
        for input_code, expected in test_cases:
            with self.subTest(input=input_code):
                result = AStockCode.standardize(input_code)
                self.assertEqual(result, expected)

    def test_error_handling(self):
        """测试错误处理"""
        # 测试None输入
        self.assertIsNone(AStockCode.standardize(None))
        self.assertFalse(AStockCode.is_valid(None))
        self.assertEqual(AStockCode.get_market_info(None), {})
        
        # 测试非字符串输入
        self.assertIsNone(AStockCode.standardize(12345))
        self.assertFalse(AStockCode.is_valid(12345))
        self.assertEqual(AStockCode.get_market_info(12345), {})


if __name__ == '__main__':
    unittest.main()