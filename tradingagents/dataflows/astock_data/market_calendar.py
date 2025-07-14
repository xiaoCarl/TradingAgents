"""
A股交易日历

处理A股市场的交易日、节假日、休市安排等
"""

import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import List, Optional
import json
import os


class AStockCalendar:
    """A股交易日历类"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化交易日历
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), 'cache')
        self.calendar_cache_file = os.path.join(self.cache_dir, 'trading_calendar.json')
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 交易日历缓存
        self._trading_days = None
        self._holidays = None
        
        # 加载缓存
        self._load_calendar_cache()
    
    def _load_calendar_cache(self):
        """从缓存加载交易日历"""
        if os.path.exists(self.calendar_cache_file):
            try:
                with open(self.calendar_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._trading_days = [pd.to_datetime(d) for d in data.get('trading_days', [])]
                    self._holidays = [pd.to_datetime(d) for d in data.get('holidays', [])]
            except Exception:
                pass
    
    def _save_calendar_cache(self):
        """保存交易日历到缓存"""
        try:
            data = {
                'trading_days': [d.strftime('%Y-%m-%d') for d in self._trading_days or []],
                'holidays': [d.strftime('%Y-%m-%d') for d in self._holidays or []]
            }
            with open(self.calendar_cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _fetch_trading_calendar(self, start_year: int, end_year: int) -> List[datetime]:
        """
        从AkShare获取指定年份范围的交易日历
        
        Args:
            start_year: 开始年份
            end_year: 结束年份
            
        Returns:
            交易日列表
        """
        trading_days = []
        
        try:
            for year in range(start_year, end_year + 1):
                # 获取年度交易日历
                tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
                
                if not tool_trade_date_hist_sina_df.empty:
                    # 筛选指定年份的交易日
                    year_data = tool_trade_date_hist_sina_df[
                        pd.to_datetime(tool_trade_date_hist_sina_df['trade_date']).dt.year == year
                    ]
                    
                    for _, row in year_data.iterrows():
                        trading_days.append(pd.to_datetime(row['trade_date']))
        
        except Exception as e:
            print(f"获取交易日历失败: {e}")
            # 使用默认的交易日历生成
            trading_days = self._generate_default_calendar(start_year, end_year)
        
        return sorted(trading_days)
    
    def _generate_default_calendar(self, start_year: int, end_year: int) -> List[datetime]:
        """
        生成默认的交易日历（当网络不可用时的备用方案）
        
        Args:
            start_year: 开始年份
            end_year: 结束年份
            
        Returns:
            交易日列表（排除周末和主要节假日）
        """
        trading_days = []
        
        # 定义主要节假日（简化版）
        holidays = [
            '2024-01-01', '2024-02-09', '2024-02-10', '2024-02-11', '2024-02-12',
            '2024-02-13', '2024-02-14', '2024-02-15', '2024-02-16', '2024-02-17',
            '2024-04-04', '2024-04-05', '2024-04-06', '2024-05-01', '2024-05-02',
            '2024-05-03', '2024-06-10', '2024-09-15', '2024-09-16', '2024-09-17',
            '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-07'
        ]
        
        holiday_dates = [pd.to_datetime(h) for h in holidays]
        
        for year in range(start_year, end_year + 1):
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            current_date = start_date
            while current_date <= end_date:
                # 排除周末和节假日
                if (current_date.weekday() < 5 and 
                    current_date not in holiday_dates):
                    trading_days.append(current_date)
                current_date += timedelta(days=1)
        
        return trading_days
    
    def refresh_calendar(self, start_year: int = 2020, end_year: int = None):
        """
        刷新交易日历缓存
        
        Args:
            start_year: 开始年份
            end_year: 结束年份，默认为当前年份+1
        """
        if end_year is None:
            end_year = datetime.now().year + 1
        
        self._trading_days = self._fetch_trading_calendar(start_year, end_year)
        self._holidays = self._get_holidays_from_trading_days()
        self._save_calendar_cache()
    
    def _get_holidays_from_trading_days(self) -> List[datetime]:
        """从交易日历推断节假日"""
        if not self._trading_days:
            return []
        
        start_date = min(self._trading_days)
        end_date = max(self._trading_days)
        
        all_days = pd.date_range(start=start_date, end=end_date, freq='D')
        trading_set = set(self._trading_days)
        
        holidays = [day for day in all_days if day not in trading_set]
        return holidays
    
    def is_trading_day(self, date: str or datetime) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期字符串或datetime对象
            
        Returns:
            True如果是交易日，否则False
        """
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        if self._trading_days is None:
            self.refresh_calendar()
        
        # 确保时间部分一致
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return date in self._trading_days
    
    def get_trading_days(self, start_date: str, end_date: str) -> List[datetime]:
        """
        获取指定日期范围内的交易日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        if self._trading_days is None:
            self.refresh_calendar(start.year, end.year)
        
        trading_days = [d for d in self._trading_days if start <= d <= end]
        return trading_days
    
    def next_trading_day(self, date: str, n: int = 1) -> Optional[datetime]:
        """
        获取下一个交易日
        
        Args:
            date: 起始日期
            n: 第n个交易日，默认为1（下一个交易日）
            
        Returns:
            第n个交易日，如果不存在则返回None
        """
        date = pd.to_datetime(date)
        
        if self._trading_days is None:
            self.refresh_calendar()
        
        # 找到第一个大于等于给定日期的交易日
        future_days = [d for d in self._trading_days if d >= date]
        
        if len(future_days) >= n:
            return future_days[n-1]
        
        return None
    
    def previous_trading_day(self, date: str, n: int = 1) -> Optional[datetime]:
        """
        获取上一个交易日
        
        Args:
            date: 起始日期
            n: 第n个交易日，默认为1（上一个交易日）
            
        Returns:
            第n个交易日，如果不存在则返回None
        """
        date = pd.to_datetime(date)
        
        if self._trading_days is None:
            self.refresh_calendar()
        
        # 找到最后一个小于等于给定日期的交易日
        past_days = [d for d in self._trading_days if d <= date]
        
        if len(past_days) >= n:
            return past_days[-n]
        
        return None
    
    def count_trading_days(self, start_date: str, end_date: str) -> int:
        """
        计算两个日期之间的交易日数量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日数量
        """
        trading_days = self.get_trading_days(start_date, end_date)
        return len(trading_days)
    
    def get_holidays(self, start_date: str, end_date: str) -> List[datetime]:
        """
        获取指定日期范围内的节假日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            节假日列表
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        if self._holidays is None:
            if self._trading_days is None:
                self.refresh_calendar()
            else:
                self._holidays = self._get_holidays_from_trading_days()
        
        holidays = [d for d in self._holidays if start <= d <= end]
        return holidays
    
    def get_current_trading_day(self) -> Optional[datetime]:
        """
        获取当前交易日
        如果今天是交易日则返回今天，否则返回下一个交易日
        
        Returns:
            当前交易日
        """
        today = datetime.now()
        
        if self.is_trading_day(today):
            return today.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return self.next_trading_day(today.strftime('%Y-%m-%d'))
    
    def get_trading_hours(self, date: str = None) -> tuple:
        """
        获取指定日期的交易时间
        
        Args:
            date: 日期，默认为当前日期
            
        Returns:
            交易时间段 (开盘时间, 收盘时间)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # A股交易时间：9:30-11:30, 13:00-15:00
        if self.is_trading_day(date):
            return (
                datetime.strptime(f"{date} 09:30:00", '%Y-%m-%d %H:%M:%S'),
                datetime.strptime(f"{date} 15:00:00", '%Y-%m-%d %H:%M:%S')
            )
        
        return None
    
    def is_trading_time(self, datetime_obj: datetime = None) -> bool:
        """
        判断是否处于交易时间
        
        Args:
            datetime_obj: 时间对象，默认为当前时间
            
        Returns:
            True如果处于交易时间，否则False
        """
        if datetime_obj is None:
            datetime_obj = datetime.now()
        
        # 检查是否为交易日
        if not self.is_trading_day(datetime_obj.strftime('%Y-%m-%d')):
            return False
        
        # 检查交易时间
        current_time = datetime_obj.time()
        
        # A股交易时间段
        morning_start = datetime.strptime('09:30:00', '%H:%M:%S').time()
        morning_end = datetime.strptime('11:30:00', '%H:%M:%S').time()
        afternoon_start = datetime.strptime('13:00:00', '%H:%M:%S').time()
        afternoon_end = datetime.strptime('15:00:00', '%H:%M:%S').time()
        
        return (
            (morning_start <= current_time <= morning_end) or
            (afternoon_start <= current_time <= afternoon_end)
        )


# 测试函数
def test_market_calendar():
    """测试交易日历"""
    calendar = AStockCalendar()
    
    # 测试交易日判断
    test_date = "2024-01-02"
    is_trading = calendar.is_trading_day(test_date)
    print(f"{test_date} 是交易日: {is_trading}")
    
    # 测试获取交易日
    trading_days = calendar.get_trading_days("2024-01-01", "2024-01-10")
    print(f"2024-01-01 到 2024-01-10 的交易日: {len(trading_days)} 天")
    for day in trading_days:
        print(f"  {day.strftime('%Y-%m-%d')}")
    
    # 测试下一个交易日
    next_day = calendar.next_trading_day("2024-01-01")
    print(f"2024-01-01 的下一个交易日: {next_day.strftime('%Y-%m-%d') if next_day else 'None'}")
    
    # 测试交易时间
    trading_hours = calendar.get_trading_hours("2024-01-02")
    print(f"2024-01-02 交易时间: {trading_hours}")


if __name__ == "__main__":
    test_market_calendar()