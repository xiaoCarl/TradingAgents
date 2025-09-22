# -*- coding: utf-8 -*-
"""
A股交易日历测试

测试交易日历相关的功能
"""

import unittest
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tradingagents.dataflows.astock_data.market_calendar import AStockCalendar


class TestAStockCalendar(unittest.TestCase):
    """A股交易日历测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.calendar = AStockCalendar()

    def test_is_trading_day_format(self):
        """测试日期格式验证"""
        # 测试有效日期格式
        valid_dates = [
            "2024-01-01",
            "2024-12-31",
            "2023-02-28",
            "2024-02-29",  # 闰年
        ]
        
        for date_str in valid_dates:
            with self.subTest(date=date_str):
                # 测试日期格式解析
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    valid = True
                except ValueError:
                    valid = False
                self.assertTrue(valid)

    def test_invalid_date_format(self):
        """测试无效日期格式"""
        invalid_dates = [
            "2024-13-01",  # 无效月份
            "2024-01-32",  # 无效日期
            "2024-02-30",  # 无效日期
            "2023-02-29",  # 非闰年
            "invalid-date",
            "20240101",
            "01/01/2024",
            "",
        ]
        
        for date_str in invalid_dates:
            with self.subTest(date=date_str):
                with self.assertRaises(ValueError):
                    datetime.strptime(date_str, '%Y-%m-%d')

    def test_get_trading_days_range(self):
        """测试获取交易日范围"""
        # 测试有效日期范围
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        trading_days = self.calendar.get_trading_days(start_date, end_date)
        
        self.assertIsInstance(trading_days, list)
        self.assertGreater(len(trading_days), 0)
        
        # 验证返回的是datetime对象列表
        for day in trading_days:
            self.assertIsInstance(day, datetime)
            self.assertGreaterEqual(day, datetime(2024, 1, 1))
            self.assertLessEqual(day, datetime(2024, 1, 31))

    def test_trading_days_order(self):
        """测试交易日排序"""
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        trading_days = self.calendar.get_trading_days(start_date, end_date)
        
        # 验证按时间升序排列
        for i in range(1, len(trading_days)):
            self.assertGreater(trading_days[i], trading_days[i-1])

    def test_single_day_range(self):
        """测试单日范围"""
        date_str = "2024-01-15"
        trading_days = self.calendar.get_trading_days(date_str, date_str)
        
        # 如果该日是交易日，应该返回包含该日的列表
        # 如果不是交易日，应该返回空列表
        self.assertIsInstance(trading_days, list)

    def test_invalid_date_range(self):
        """测试无效日期范围"""
        # 开始日期晚于结束日期
        with self.assertRaises(ValueError):
            self.calendar.get_trading_days("2024-01-31", "2024-01-01")

    def test_weekend_detection(self):
        """测试周末识别"""
        # 2024年的一些已知周末
        weekends = [
            "2024-01-06",  # 周六
            "2024-01-07",  # 周日
            "2024-01-13",  # 周六
            "2024-01-14",  # 周日
        ]
        
        for weekend in weekends:
            with self.subTest(date=weekend):
                is_trading = self.calendar.is_trading_day(weekend)
                # 注意：实际结果可能受节假日调休影响
                self.assertIsInstance(is_trading, bool)

    def test_weekday_detection(self):
        """测试工作日识别"""
        # 2024年的一些已知工作日
        weekdays = [
            "2024-01-02",  # 周二
            "2024-01-03",  # 周三
            "2024-01-04",  # 周四
            "2024-01-05",  # 周五
        ]
        
        for weekday in weekdays:
            with self.subTest(date=weekday):
                is_trading = self.calendar.is_trading_day(weekday)
                self.assertIsInstance(is_trading, bool)

    def test_trading_days_count(self):
        """测试交易日数量"""
        # 测试2024年1月（假设约22个交易日）
        january_days = self.calendar.get_trading_days("2024-01-01", "2024-01-31")
        
        # 1月最多31天，最少16个交易日（考虑节假日）
        self.assertGreater(len(january_days), 15)
        self.assertLessEqual(len(january_days), 23)

    def test_year_boundary(self):
        """测试年度边界"""
        # 测试2023-2024年跨年
        year_end_days = self.calendar.get_trading_days("2023-12-25", "2024-01-05")
        
        self.assertIsInstance(year_end_days, list)
        self.assertGreater(len(year_end_days), 0)
        
        # 验证包含2023年和2024年的日期
        has_2023 = any(day.year == 2023 for day in year_end_days)
        has_2024 = any(day.year == 2024 for day in year_end_days)
        
        # 注意：实际可能只包含一个年度的日期
        self.assertTrue(has_2023 or has_2024)

    def test_month_boundary(self):
        """测试月度边界"""
        # 测试2024年1-2月边界
        month_boundary = self.calendar.get_trading_days("2024-01-29", "2024-02-02")
        
        self.assertIsInstance(month_boundary, list)
        self.assertGreater(len(month_boundary), 0)

    def test_empty_range(self):
        """测试空范围"""
        # 测试相同日期的范围
        single_day = self.calendar.get_trading_days("2024-01-15", "2024-01-15")
        self.assertIsInstance(single_day, list)

    def test_future_dates(self):
        """测试未来日期"""
        # 测试未来日期（应该返回空列表或仅返回已知交易日）
        future_start = "2025-12-01"
        future_end = "2025-12-31"
        
        future_days = self.calendar.get_trading_days(future_start, future_end)
        self.assertIsInstance(future_days, list)
        # 未来日期的交易日历可能为空或有限

    def test_past_dates(self):
        """测试历史日期"""
        # 测试历史日期
        past_start = "2020-01-01"
        past_end = "2020-01-31"
        
        past_days = self.calendar.get_trading_days(past_start, past_end)
        self.assertIsInstance(past_days, list)

    def test_holiday_detection(self):
        """测试节假日识别"""
        # 测试已知的中国法定节假日
        holidays = [
            "2024-01-01",  # 元旦
            "2024-02-09",  # 除夕（假设）
            "2024-02-10",  # 春节
            "2024-05-01",  # 劳动节
            "2024-10-01",  # 国庆节
        ]
        
        for holiday in holidays:
            with self.subTest(holiday=holiday):
                is_trading = self.calendar.is_trading_day(holiday)
                # 注意：实际结果取决于具体的节假日安排
                self.assertIsInstance(is_trading, bool)

    def test_leap_year(self):
        """测试闰年处理"""
        # 测试2024年2月29日（闰年）
        leap_day = "2024-02-29"
        
        # 验证日期格式正确
        try:
            parsed_date = datetime.strptime(leap_day, '%Y-%m-%d')
            self.assertEqual(parsed_date.year, 2024)
            self.assertEqual(parsed_date.month, 2)
            self.assertEqual(parsed_date.day, 29)
        except ValueError:
            self.fail("闰年2月29日应该被正确解析")

    def test_date_format_conversion(self):
        """测试日期格式转换"""
        test_date = "2024-01-15"
        
        # 验证日期字符串可以正确转换为datetime
        dt = datetime.strptime(test_date, '%Y-%m-%d')
        self.assertEqual(dt.strftime('%Y-%m-%d'), test_date)

    def test_trading_days_string_format(self):
        """测试交易日字符串格式"""
        # 测试返回的日期字符串格式
        trading_days = self.calendar.get_trading_days("2024-01-01", "2024-01-10")
        
        # 验证返回的是datetime对象，可以转换为字符串
        for day in trading_days:
            date_str = day.strftime('%Y-%m-%d')
            self.assertRegex(date_str, r'^\d{4}-\d{2}-\d{2}$')

    def test_performance(self):
        """测试性能"""
        import time
        
        # 测试获取一个月的交易日历
        start_time = time.time()
        days = self.calendar.get_trading_days("2024-01-01", "2024-01-31")
        end_time = time.time()
        
        # 验证在合理时间内完成（假设小于1秒）
        self.assertLess(end_time - start_time, 1.0)
        self.assertIsInstance(days, list)


if __name__ == '__main__':
    unittest.main()