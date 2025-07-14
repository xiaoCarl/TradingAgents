"""
TuShare数据客户端

提供A股数据的获取接口，包括历史行情、财务数据、公司信息等
"""

import os
import pandas as pd
import tushare as ts
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
from .stock_code import AStockCode


class TuShareClient:
    """TuShare数据客户端"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化TuShare客户端
        
        Args:
            token: TuShare API token，如果未提供则从环境变量获取
        """
        self.token = token or os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("TuShare token未提供，请设置TUSHARE_TOKEN环境变量")
        
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        
        # 缓存机制
        self._cache = {}
        self._cache_timeout = 3600  # 1小时缓存
    
    def _get_cache_key(self, func_name: str, **kwargs) -> str:
        """生成缓存键"""
        return f"{func_name}_{hash(str(sorted(kwargs.items())))}"
    
    def _get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_timeout:
                return data
            else:
                del self._cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: pd.DataFrame):
        """保存数据到缓存"""
        self._cache[key] = (data, time.time())
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取A股历史行情数据
        
        Args:
            symbol: 股票代码，支持多种格式
            start_date: 开始日期，格式：2024-01-01
            end_date: 结束日期，格式：2024-12-31
            
        Returns:
            DataFrame包含：日期、开盘、收盘、最高、最低、成交量、成交额
        """
        std_code = AStockCode.standardize(symbol)
        if not std_code:
            raise ValueError(f"无效的股票代码: {symbol}")
        
        ts_code = AStockCode.to_tushare_format(std_code)
        cache_key = self._get_cache_key('stock_data', ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # 获取历史行情
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', '')
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # 转换数据格式，与yfinance保持一致
            df = df.sort_values('trade_date')
            df = df.rename(columns={
                'trade_date': 'Date',
                'open': 'Open',
                'close': 'Close', 
                'high': 'High',
                'low': 'Low',
                'vol': 'Volume',
                'amount': 'Amount'
            })
            
            # 设置日期为索引
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            
            # 转换数据类型
            numeric_cols = ['Open', 'Close', 'High', 'Low', 'Volume', 'Amount']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            self._save_to_cache(cache_key, df)
            return df
            
        except Exception as e:
            print(f"获取{symbol}行情数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含公司基本信息的字典
        """
        std_code = AStockCode.standardize(symbol)
        if not std_code:
            raise ValueError(f"无效的股票代码: {symbol}")
        
        ts_code = AStockCode.to_tushare_format(std_code)
        
        try:
            # 获取股票基本信息
            stock_basic = self.pro.stock_basic(
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,list_date,market,exchange'
            )
            
            if stock_basic.empty:
                return {}
            
            # 获取最新行情数据
            daily_basic = self.pro.daily_basic(
                ts_code=ts_code,
                limit=1,
                fields='ts_code,trade_date,total_mv,circ_mv,turnover_rate,pe_ttm,pb'
            )
            
            info = stock_basic.iloc[0].to_dict()
            
            # 构造与yfinance兼容的格式
            result = {
                'symbol': std_code,
                'shortName': info.get('name', ''),
                'longName': info.get('name', ''),
                'industry': info.get('industry', ''),
                'sector': info.get('industry', ''),
                'country': 'China',
                'currency': 'CNY',
                'exchange': info.get('exchange', ''),
                'market': info.get('market', ''),
                'list_date': info.get('list_date', ''),
                'area': info.get('area', '')
            }
            
            # 添加市值信息（如果有最新数据）
            if not daily_basic.empty:
                latest = daily_basic.iloc[0]
                result['marketCap'] = latest.get('total_mv', 0) * 10000  # 转换为元
                result['enterpriseValue'] = latest.get('total_mv', 0) * 10000
                result['trailingPE'] = latest.get('pe_ttm')
                result['priceToBook'] = latest.get('pb')
            
            return result
            
        except Exception as e:
            print(f"获取{symbol}基本信息失败: {e}")
            return {}
    
    def get_financial_data(self, symbol: str, statement_type: str = 'income') -> pd.DataFrame:
        """
        获取财务报表数据
        
        Args:
            symbol: 股票代码
            statement_type: 报表类型 ('income', 'balance', 'cashflow')
            
        Returns:
            财务数据DataFrame
        """
        std_code = AStockCode.standardize(symbol)
        if not std_code:
            raise ValueError(f"无效的股票代码: {symbol}")
        
        ts_code = AStockCode.to_tushare_format(std_code)
        
        try:
            if statement_type == 'income':
                df = self.pro.income(ts_code=ts_code)
            elif statement_type == 'balance':
                df = self.pro.balancesheet(ts_code=ts_code)
            elif statement_type == 'cashflow':
                df = self.pro.cashflow(ts_code=ts_code)
            else:
                raise ValueError("statement_type必须是 'income', 'balance', 或 'cashflow'")
            
            if df.empty:
                return pd.DataFrame()
            
            # 按报告期排序
            df = df.sort_values('end_date', ascending=False)
            
            return df
            
        except Exception as e:
            print(f"获取{symbol}{statement_type}报表失败: {e}")
            return pd.DataFrame()
    
    def get_dividends(self, symbol: str) -> pd.DataFrame:
        """
        获取分红数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            分红数据DataFrame
        """
        std_code = AStockCode.standardize(symbol)
        if not std_code:
            raise ValueError(f"无效的股票代码: {symbol}")
        
        ts_code = AStockCode.to_tushare_format(std_code)
        
        try:
            # 获取分红送股数据
            df = self.pro.dividend(ts_code=ts_code)
            
            if df.empty:
                return pd.DataFrame()
            
            # 转换数据格式
            df = df.sort_values('end_date', ascending=False)
            
            return df
            
        except Exception as e:
            print(f"获取{symbol}分红数据失败: {e}")
            return pd.DataFrame()
    
    def get_index_stocks(self, index_code: str = '000001.SH') -> List[str]:
        """
        获取指数成分股列表
        
        Args:
            index_code: 指数代码，如 '000001.SH' (上证指数)
            
        Returns:
            成分股代码列表
        """
        try:
            # 获取指数成分股
            df = self.pro.index_weight(index_code=index_code)
            
            if df.empty:
                return []
            
            # 转换为标准格式
            stocks = []
            for _, row in df.iterrows():
                ts_code = row['con_code']
                if ts_code:
                    # 转换格式：000001.SZ -> 000001.SZ
                    code_parts = ts_code.split('.')
                    if len(code_parts) == 2:
                        stocks.append(f"{code_parts[0]}.{code_parts[1]}")
            
            return list(set(stocks))  # 去重
            
        except Exception as e:
            print(f"获取指数{index_code}成分股失败: {e}")
            return []
    
    def get_realtime_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取实时行情数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            实时行情DataFrame
        """
        if not symbols:
            return pd.DataFrame()
        
        # 转换代码格式
        ts_codes = []
        for symbol in symbols:
            std_code = AStockCode.standardize(symbol)
            if std_code:
                ts_codes.append(AStockCode.to_tushare_format(std_code))
        
        if not ts_codes:
            return pd.DataFrame()
        
        try:
            # 获取实时行情
            df = self.pro.stk_mins(ts_code=','.join(ts_codes))
            
            if df.empty:
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return pd.DataFrame()


# 测试函数
def test_tushare_client():
    """测试TuShare客户端"""
    try:
        client = TuShareClient()
        
        # 测试获取股票数据
        data = client.get_stock_data("000001", "2024-01-01", "2024-01-31")
        print(f"000001 数据条数: {len(data)}")
        
        # 测试获取股票信息
        info = client.get_stock_info("000001")
        print(f"000001 公司信息: {info}")
        
        # 测试获取财务数据
        financial = client.get_financial_data("000001", "income")
        print(f"000001 财务数据条数: {len(financial)}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_tushare_client()