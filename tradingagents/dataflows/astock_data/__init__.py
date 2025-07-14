"""
A股数据模块 - 独立的中国A股数据接口

提供与现有美股接口兼容的A股数据获取功能
"""

from .tushare_client import TuShareClient
from .akshare_client import AkShareClient
from .stock_code import AStockCode
from .market_calendar import AStockCalendar
from .data_validator import AStockDataValidator

__all__ = [
    "TuShareClient",
    "AkShareClient", 
    "AStockCode",
    "AStockCalendar",
    "AStockDataValidator"
]