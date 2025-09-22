"""
AkShare数据客户端

AkShare备用数据源，当TuShare不可用时使用
提供A股数据的获取功能
"""

import pandas as pd
import akshare as ak
from typing import Optional, Dict, Any, List
import time
from datetime import datetime, timedelta
from .stock_code import AStockCode


class AkShareClient:
    """AkShare数据客户端"""
    
    def __init__(self):
        """初始化AkShare客户端"""
        # AkShare不需要token，但设置重试机制
        self.max_retries = 3
        self.retry_delay = 1  # 重试延迟1秒
        
        # 缓存机制
        self._cache = {}
        self._cache_timeout = 1800  # 30分钟缓存
    
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
    
    def _retry_request(self, func, *args, **kwargs):
        """带重试的数据请求"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise e
    
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
        
        stock_code, market = std_code.split('.')
        cache_key = self._get_cache_key('stock_data', symbol=symbol, start_date=start_date, end_date=end_date)
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # 使用AkShare获取历史行情数据
            # 根据市场选择不同的数据源
            if market == 'SH':
                # 沪市
                stock_zh_a_hist_df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust=""
                )
            elif market == 'SZ':
                # 深市
                stock_zh_a_hist_df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily", 
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust=""
                )
            else:
                # 北交所或其他
                stock_zh_a_hist_df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust=""
                )
            
            if stock_zh_a_hist_df.empty:
                return pd.DataFrame()
            
            # 转换数据格式，与yfinance保持一致
            df = stock_zh_a_hist_df.copy()
            
            # 重命名列
            column_mapping = {
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount'
            }
            
            # 只保留我们需要的列
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            if not available_columns:
                return pd.DataFrame()
            
            df = df[available_columns].rename(columns=column_mapping)
            
            # 设置日期为索引
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            
            # 转换数据类型
            numeric_cols = ['Open', 'Close', 'High', 'Low', 'Volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 如果缺少Amount列，用Volume * Close估算
            if 'Amount' not in df.columns:
                df['Amount'] = df['Volume'] * df['Close']
            
            self._save_to_cache(cache_key, df)
            return df
            
        except Exception as e:
            print(f"使用AkShare获取{symbol}行情数据失败: {e}")
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
        
        stock_code, market = std_code.split('.')
        print("symbol:{symbol}")
        print(ak.stock_zh_a_spot())

        try:
            # 使用AkShare获取股票信息
            stock_zh_a_spot_df = ak.stock_zh_a_spot()
            
            if stock_zh_a_spot_df.empty:
                return {}
            print("df:{stock_zh_a_spot_df}")
            # 查找对应股票
            symbol_key = f"{market.lower()}{stock_code}"
            stock_info = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == symbol_key]
            
            if stock_info.empty:
                # 尝试其他格式
                stock_info = stock_zh_a_spot_df[stock_zh_a_spot_df['代码'] == stock_code]
            
            if stock_info.empty:
                return {}
            
            # 获取详细信息
            stock_individual_info_em_df = ak.stock_individual_info_em(symbol=stock_code)
            
            info = {}
            print(info)
            if not stock_individual_info_em_df.empty:
                info_dict = stock_individual_info_em_df.set_index('item')['value'].to_dict()
                info = {
                    'symbol': std_code,
                    'shortName': info_dict.get('股票简称', ''),
                    'longName': info_dict.get('股票简称', ''),
                    'industry': info_dict.get('行业', ''),
                    'sector': info_dict.get('行业', ''),
                    'country': 'China',
                    'currency': 'CNY',
                    'exchange': 'SSE' if market == 'SH' else 'SZSE',
                    'market': market,
                    'list_date': info_dict.get('上市时间', ''),
                    'area': info_dict.get('地区', ''),
                    'total_shares': info_dict.get('总股本', ''),
                    'circulating_shares': info_dict.get('流通股本', '')
                }
            
            # 从spot数据获取市值信息
            if not stock_info.empty:
                stock_data = stock_info.iloc[0]
                info['currentPrice'] = stock_data.get('最新价', 0)
                info['marketCap'] = stock_data.get('总市值', 0)
                info['enterpriseValue'] = stock_data.get('流通市值', 0)
            
            return info
            
        except Exception as e:
            print(f"使用AkShare获取{symbol}基本信息失败: {e}")
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
        
        stock_code, market = std_code.split('.')
        
        try:
            if statement_type == 'income':
                # 获取利润表
                stock_financial_report_sina_df = ak.stock_financial_report_sina(
                    stock=stock_code, 
                    symbol="利润表"
                )
            elif statement_type == 'balance':
                # 获取资产负债表
                stock_financial_report_sina_df = ak.stock_financial_report_sina(
                    stock=stock_code,
                    symbol="资产负债表"
                )
            elif statement_type == 'cashflow':
                # 获取现金流量表
                stock_financial_report_sina_df = ak.stock_financial_report_sina(
                    stock=stock_code,
                    symbol="现金流量表"
                )
            else:
                raise ValueError("statement_type必须是 'income', 'balance', 或 'cashflow'")
            
            if stock_financial_report_sina_df.empty:
                return pd.DataFrame()
            
            return stock_financial_report_sina_df
            
        except Exception as e:
            print(f"使用AkShare获取{symbol}{statement_type}报表失败: {e}")
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
        
        stock_code, market = std_code.split('.')
        
        try:
            # 获取分红数据
            stock_dividents_sina_df = ak.stock_dividents_sina(stock=stock_code)
            
            if stock_dividents_sina_df.empty:
                return pd.DataFrame()
            
            return stock_dividents_sina_df
            
        except Exception as e:
            print(f"使用AkShare获取{symbol}分红数据失败: {e}")
            return pd.DataFrame()
    
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
        
        try:
            # 获取所有A股实时行情
            stock_zh_a_spot_df = ak.stock_zh_a_spot()
            
            if stock_zh_a_spot_df.empty:
                return pd.DataFrame()
            
            # 过滤指定股票
            valid_symbols = []
            for symbol in symbols:
                std_code = AStockCode.standardize(symbol)
                if std_code:
                    stock_code, market = std_code.split('.')
                    valid_symbols.append(f"{market.lower()}{stock_code}")
                    valid_symbols.append(stock_code)
            
            if valid_symbols:
                # 过滤股票
                filtered_df = stock_zh_a_spot_df[
                    stock_zh_a_spot_df['代码'].isin(valid_symbols)
                ]
                return filtered_df
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"使用AkShare获取实时行情失败: {e}")
            return pd.DataFrame()


# 测试函数
def test_akshare_client():
    """测试AkShare客户端"""
    try:
        client = AkShareClient()
        
        # 测试获取股票数据
        data = client.get_stock_data("000001", "2024-01-01", "2024-01-31")
        print(f"000001 数据条数: {len(data)}")
        if not data.empty:
            print(f"数据列: {list(data.columns)}")
            print(f"最近一条: {data.iloc[-1].to_dict()}")
        
        # 测试获取股票信息
        info = client.get_stock_info("000001")
        print(f"000001 公司信息: {info}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_akshare_client()