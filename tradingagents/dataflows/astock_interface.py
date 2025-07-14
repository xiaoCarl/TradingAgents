"""
A股统一数据接口层

提供与现有美股接口兼容的A股数据获取功能
封装底层数据源（TuShare/AkShare）的调用逻辑
"""

import os
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from .astock_data import TuShareClient, AkShareClient, AStockCode, AStockDataValidator, AStockCalendar

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AStockData:
    """A股统一数据接口类"""
    
    def __init__(self, 
                 tushare_token: Optional[str] = None,
                 prefer_tushare: bool = True,
                 cache_enabled: bool = True):
        """
        初始化A股数据接口
        
        Args:
            tushare_token: TuShare API token
            prefer_tushare: 是否优先使用TuShare，默认为True
            cache_enabled: 是否启用缓存，默认为True
        """
        self.prefer_tushare = prefer_tushare
        self.cache_enabled = cache_enabled
        
        # 初始化客户端
        self.tushare_client = None
        self.akshare_client = None
        self.validator = AStockDataValidator()
        self.calendar = AStockCalendar()
        
        # 尝试初始化TuShare
        if prefer_tushare:
            try:
                self.tushare_client = TuShareClient(tushare_token)
                logger.info("TuShare客户端初始化成功")
            except Exception as e:
                logger.warning(f"TuShare初始化失败: {e}，将使用AkShare作为备用")
                self.prefer_tushare = False
        
        # 初始化AkShare
        try:
            self.akshare_client = AkShareClient()
            logger.info("AkShare客户端初始化成功")
        except Exception as e:
            logger.error(f"AkShare初始化失败: {e}")
            raise RuntimeError("无法初始化任何A股数据源")
    
    def _get_client(self, method: str = "auto") -> object:
        """
        根据方法选择客户端
        
        Args:
            method: 数据源选择 ('tushare', 'akshare', 'auto')
            
        Returns:
            数据客户端实例
        """
        if method == "tushare" and self.tushare_client:
            return self.tushare_client
        elif method == "akshare":
            return self.akshare_client
        elif method == "auto":
            # 自动选择：优先TuShare，其次AkShare
            if self.prefer_tushare and self.tushare_client:
                return self.tushare_client
            else:
                return self.akshare_client
        else:
            raise ValueError(f"不支持的数据源: {method}")
    
    def get_stock_data(self, 
                      symbol: str, 
                      start_date: str, 
                      end_date: str,
                      method: str = "auto",
                      validate: bool = True) -> pd.DataFrame:
        """
        获取股票历史行情数据
        
        Args:
            symbol: 股票代码（支持多种格式）
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            method: 数据源选择 ('tushare', 'akshare', 'auto')
            validate: 是否验证数据，默认为True
            
        Returns:
            股票历史数据DataFrame，格式与yfinance兼容
        """
        try:
            # 标准化股票代码
            std_code = AStockCode.standardize(symbol)
            if not std_code:
                raise ValueError(f"无效的股票代码: {symbol}")
            
            # 验证日期范围
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                if start_dt > end_dt:
                    raise ValueError("开始日期必须早于结束日期")
            except ValueError:
                raise ValueError("日期格式必须为YYYY-MM-DD")
            
            # 获取数据
            client = self._get_client(method)
            df = client.get_stock_data(std_code, start_date, end_date)
            
            if df.empty:
                logger.warning(f"未获取到{symbol}的数据，尝试备用数据源...")
                if method == "auto":
                    # 尝试另一个数据源
                    backup_client = (self.akshare_client if client == self.tushare_client 
                                   else self.tushare_client)
                    if backup_client:
                        df = backup_client.get_stock_data(std_code, start_date, end_date)
            
            if df.empty:
                logger.error(f"无法获取{symbol}的任何数据")
                return pd.DataFrame()
            
            # 数据验证
            if validate:
                validation_result = self.validator.get_validation_report(
                    df, std_code, start_date, end_date
                )
                
                if validation_result['overall_score'] < 70:
                    logger.warning(f"{symbol}数据质量评分较低: {validation_result['overall_score']}/100")
                
                # 记录验证结果
                if validation_result['basic_validation']['warnings']:
                    logger.warning(f"数据警告: {validation_result['basic_validation']['warnings']}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取{symbol}数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str, method: str = "auto") -> Dict[str, Any]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            method: 数据源选择
            
        Returns:
            股票基本信息字典，格式与yfinance兼容
        """
        try:
            std_code = AStockCode.standardize(symbol)
            if not std_code:
                raise ValueError(f"无效的股票代码: {symbol}")
            
            client = self._get_client(method)
            info = client.get_stock_info(std_code)
            
            if not info:
                # 尝试备用数据源
                if method == "auto":
                    backup_client = (self.akshare_client if client == self.tushare_client 
                                   else self.tushare_client)
                    if backup_client:
                        info = backup_client.get_stock_info(std_code)
            
            return info or {}
            
        except Exception as e:
            logger.error(f"获取{symbol}基本信息失败: {e}")
            return {}
    
    def get_financial_data(self, symbol: str, statement_type: str = 'income',
                          method: str = "auto") -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            symbol: 股票代码
            statement_type: 报表类型 ('income', 'balance', 'cashflow')
            method: 数据源选择
            
        Returns:
            财务数据DataFrame
        """
        try:
            std_code = AStockCode.standardize(symbol)
            if not std_code:
                raise ValueError(f"无效的股票代码: {symbol}")
            
            client = self._get_client(method)
            
            # 检查客户端是否支持财务数据
            if hasattr(client, 'get_financial_data'):
                df = client.get_financial_data(std_code, statement_type)
            else:
                logger.warning(f"{method}不支持财务数据查询")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"获取{symbol}财务数据失败: {e}")
            return pd.DataFrame()
    
    def get_dividends(self, symbol: str, method: str = "auto") -> pd.DataFrame:
        """
        获取分红数据
        
        Args:
            symbol: 股票代码
            method: 数据源选择
            
        Returns:
            分红数据DataFrame
        """
        try:
            std_code = AStockCode.standardize(symbol)
            if not std_code:
                raise ValueError(f"无效的股票代码: {symbol}")
            
            client = self._get_client(method)
            
            if hasattr(client, 'get_dividends'):
                df = client.get_dividends(std_code)
            else:
                logger.warning(f"{method}不支持分红数据查询")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"获取{symbol}分红数据失败: {e}")
            return pd.DataFrame()
    
    def get_realtime_quotes(self, symbols: List[str], method: str = "auto") -> pd.DataFrame:
        """
        获取实时行情数据
        
        Args:
            symbols: 股票代码列表
            method: 数据源选择
            
        Returns:
            实时行情DataFrame
        """
        try:
            # 标准化股票代码
            std_symbols = []
            for symbol in symbols:
                std_code = AStockCode.standardize(symbol)
                if std_code:
                    std_symbols.append(std_code)
            
            if not std_symbols:
                return pd.DataFrame()
            
            client = self._get_client(method)
            
            if hasattr(client, 'get_realtime_quotes'):
                df = client.get_realtime_quotes(std_symbols)
            else:
                logger.warning(f"{method}不支持实时行情查询")
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return pd.DataFrame()
    
    def get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """
        获取指定日期范围内的交易日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日列表（字符串格式）
        """
        try:
            trading_days = self.calendar.get_trading_days(start_date, end_date)
            return [d.strftime('%Y-%m-%d') for d in trading_days]
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            return []
    
    def is_trading_day(self, date: str) -> bool:
        """
        判断是否为交易日
        
        Args:
            date: 日期字符串
            
        Returns:
            True如果是交易日
        """
        try:
            return self.calendar.is_trading_day(date)
        except Exception as e:
            logger.error(f"判断交易日失败: {e}")
            return False
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场信息（包括板块、市场类型等）
        
        Args:
            symbol: 股票代码
            
        Returns:
            市场信息字典
        """
        return AStockCode.get_market_info(symbol)
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        验证股票代码是否有效
        
        Args:
            symbol: 股票代码
            
        Returns:
            True如果代码有效
        """
        return AStockCode.is_valid(symbol)


# 兼容现有接口的快捷函数
def get_astock_data(symbol: str, 
                   start_date: str, 
                   end_date: str,
                   tushare_token: Optional[str] = None,
                   method: str = "auto") -> pd.DataFrame:
    """
    快速获取A股数据的便捷函数
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        tushare_token: TuShare token
        method: 数据源选择
        
    Returns:
        股票数据DataFrame
    """
    astock = AStockData(tushare_token=tushare_token, method=method)
    return astock.get_stock_data(symbol, start_date, end_date)


# 测试函数
def test_astock_interface():
    """测试A股数据接口"""
    try:
        # 创建接口实例
        astock = AStockData()
        
        # 测试股票代码验证
        test_symbols = ["000001", "000001.SZ", "sz000001", "600000", "300750"]
        for symbol in test_symbols:
            is_valid = astock.validate_symbol(symbol)
            print(f"{symbol}: {'有效' if is_valid else '无效'}")
        
        # 测试获取股票信息
        info = astock.get_stock_info("000001")
        print(f"000001 信息: {info.get('shortName', 'N/A')}")
        
        # 测试获取交易日历
        trading_days = astock.get_trading_days("2024-01-01", "2024-01-10")
        print(f"交易日数量: {len(trading_days)}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_astock_interface()