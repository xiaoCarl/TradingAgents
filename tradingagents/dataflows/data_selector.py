"""
数据源选择器

根据股票代码自动选择合适的数据源
支持A股和美股的无缝切换
"""

import re
from typing import Optional, Dict, Any
import logging

from .yfin_utils import YFinanceUtils
from .astock_interface import AStockData, AStockCode

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSelector:
    """智能数据源选择器"""
    
    def __init__(self, 
                 tushare_token: Optional[str] = None,
                 prefer_tushare: bool = True):
        """
        初始化数据源选择器
        
        Args:
            tushare_token: TuShare API token
            prefer_tushare: 是否优先使用TuShare获取A股数据
        """
        self.tushare_token = tushare_token
        self.prefer_tushare = prefer_tushare
        
        # 初始化客户端
        self.yfinance_client = YFinanceUtils()
        self.astock_client = None
        
        # 延迟初始化A股客户端，避免不必要的依赖
        self._astock_initialized = False
    
    def _init_astock_client(self):
        """初始化A股客户端"""
        if not self._astock_initialized:
            try:
                self.astock_client = AStockData(
                    tushare_token=self.tushare_token,
                    prefer_tushare=self.prefer_tushare
                )
                self._astock_initialized = True
                logger.info("A股客户端初始化成功")
            except Exception as e:
                logger.warning(f"A股客户端初始化失败: {e}")
                self.astock_client = None
    
    def identify_market(self, symbol: str) -> str:
        """
        识别股票所属市场
        
        Args:
            symbol: 股票代码
            
        Returns:
            市场类型 ('A股', '美股', '港股', '未知')
        """
        symbol = str(symbol).strip().upper()
        
        # A股识别
        if AStockCode.is_valid(symbol):
            return 'A股'
        
        # 美股识别
        # 常见的美国股票交易所后缀
        us_patterns = [
            r'^[A-Z]{1,5}$',           # 纯字母，如 AAPL, TSLA
            r'^[A-Z]{1,5}\.US$',       # .US后缀
            r'^[A-Z]{1,5}\.NYSE$',     # NYSE
            r'^[A-Z]{1,5}\.NASDAQ$',   # NASDAQ
            r'^[A-Z]{1,5}\.AMEX$',     # AMEX
        ]
        
        for pattern in us_patterns:
            if re.match(pattern, symbol):
                return '美股'
        
        # 港股识别
        hk_patterns = [
            r'^\d{4}$',               # 纯4位数字
            r'^\d{4}\.HK$',           # .HK后缀
            r'^\d{4}\.HKG$',          # .HKG后缀
        ]
        
        for pattern in hk_patterns:
            if re.match(pattern, symbol):
                return '港股'
        
        # 其他市场
        if '.' in symbol:
            suffix = symbol.split('.')[-1]
            market_mapping = {
                'SS': '美股',  # NYSE
                'SI': '美股',  # NASDAQ
                'T': '加拿大',
                'TO': '加拿大',
                'L': '英国',
                'PA': '法国',
                'BE': '德国',
                'SS': '西班牙',
                'AX': '澳大利亚',
                'T': '日本',
                'KS': '韩国',
                'SG': '新加坡',
            }
            return market_mapping.get(suffix.upper(), '未知')
        
        return '未知'
    
    def get_data_source(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票对应的数据源信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            数据源信息字典
        """
        market = self.identify_market(symbol)
        
        source_info = {
            'symbol': symbol,
            'market': market,
            'data_source': None,
            'client': None,
            'standardized_symbol': None
        }
        
        if market == 'A股':
            self._init_astock_client()
            if self.astock_client:
                source_info.update({
                    'data_source': 'AStockData',
                    'client': self.astock_client,
                    'standardized_symbol': AStockCode.standardize(symbol)
                })
        elif market == '美股':
            source_info.update({
                'data_source': 'YFinance',
                'client': self.yfinance_client,
                'standardized_symbol': symbol.split('.')[0]  # 去除后缀
            })
        else:
            logger.warning(f"未识别的市场类型: {symbol} -> {market}")
            
            # 默认使用yfinance处理
            source_info.update({
                'data_source': 'YFinance',
                'client': self.yfinance_client,
                'standardized_symbol': symbol
            })
        
        return source_info
    
    def get_stock_data(self, 
                      symbol: str, 
                      start_date: str, 
                      end_date: str,
                      **kwargs) -> pd.DataFrame:
        """
        智能获取股票数据（自动选择数据源）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
            
        Returns:
            股票数据DataFrame
        """
        try:
            source_info = self.get_data_source(symbol)
            
            if not source_info['client']:
                logger.error(f"无法获取{symbol}的数据源客户端")
                return pd.DataFrame()
            
            client = source_info['client']
            standardized_symbol = source_info['standardized_symbol']
            
            logger.info(f"使用{source_info['data_source']}获取{symbol}的数据")
            
            # 根据数据源类型调用相应方法
            if source_info['data_source'] == 'AStockData':
                return client.get_stock_data(standardized_symbol, start_date, end_date, **kwargs)
            elif source_info['data_source'] == 'YFinance':
                # yfinance的调用方式
                ticker = client.get_stock_data(standardized_symbol, start_date, end_date)
                return ticker
            else:
                logger.error(f"不支持的数据源: {source_info['data_source']}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取{symbol}数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        智能获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票基本信息字典
        """
        try:
            source_info = self.get_data_source(symbol)
            
            if not source_info['client']:
                logger.error(f"无法获取{symbol}的数据源客户端")
                return {}
            
            client = source_info['client']
            standardized_symbol = source_info['standardized_symbol']
            
            if source_info['data_source'] == 'AStockData':
                return client.get_stock_info(standardized_symbol)
            elif source_info['data_source'] == 'YFinance':
                # yfinance的调用方式
                ticker = client.get_stock_info(standardized_symbol)
                return ticker
            else:
                return {}
                
        except Exception as e:
            logger.error(f"获取{symbol}基本信息失败: {e}")
            return {}
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取公司信息（兼容现有接口）
        
        Args:
            symbol: 股票代码
            
        Returns:
            公司信息字典
        """
        info = self.get_stock_info(symbol)
        
        # 转换为统一格式
        company_info = {
            'Company Name': info.get('shortName', info.get('name', 'N/A')),
            'Industry': info.get('industry', 'N/A'),
            'Sector': info.get('sector', 'N/A'),
            'Country': info.get('country', 'N/A'),
            'Website': info.get('website', 'N/A'),
            'Market': info.get('market', 'N/A'),
            'Exchange': info.get('exchange', 'N/A'),
            'Currency': info.get('currency', 'N/A')
        }
        
        return company_info
    
    def get_dividends(self, symbol: str) -> pd.DataFrame:
        """
        获取分红数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            分红数据DataFrame
        """
        try:
            source_info = self.get_data_source(symbol)
            
            if not source_info['client']:
                return pd.DataFrame()
            
            client = source_info['client']
            
            if source_info['data_source'] == 'AStockData':
                return client.get_dividends(source_info['standardized_symbol'])
            elif source_info['data_source'] == 'YFinance':
                # yfinance的调用方式
                ticker = source_info['standardized_symbol']
                # 这里需要实现yfinance的分红数据获取
                return pd.DataFrame()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取{symbol}分红数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, symbol: str, statement_type: str = 'income') -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            symbol: 股票代码
            statement_type: 报表类型
            
        Returns:
            财务数据DataFrame
        """
        try:
            source_info = self.get_data_source(symbol)
            
            if source_info['data_source'] != 'AStockData':
                logger.warning(f"{source_info['data_source']}暂不支持财务数据查询")
                return pd.DataFrame()
            
            client = source_info['client']
            return client.get_financial_data(source_info['standardized_symbol'], statement_type)
            
        except Exception as e:
            logger.error(f"获取{symbol}财务数据失败: {e}")
            return pd.DataFrame()
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        验证股票代码是否有效
        
        Args:
            symbol: 股票代码
            
        Returns:
            True如果代码有效
        """
        try:
            source_info = self.get_data_source(symbol)
            return source_info['client'] is not None
        except Exception:
            return False
    
    def list_supported_markets(self) -> Dict[str, List[str]]:
        """
        列出支持的市场类型
        
        Returns:
            支持的市场字典
        """
        return {
            'A股': [
                '上海证券交易所 (SH)',
                '深圳证券交易所 (SZ)', 
                '北京证券交易所 (BJ)'
            ],
            '美股': [
                '纽约证券交易所 (NYSE)',
                '纳斯达克 (NASDAQ)',
                '美国证券交易所 (AMEX)'
            ],
            '港股': [
                '香港交易所 (HKEX)'
            ]
        }
    
    def get_symbol_examples(self) -> Dict[str, List[str]]:
        """
        获取示例股票代码
        
        Returns:
            示例代码字典
        """
        return {
            'A股': [
                '000001',      # 平安银行
                '600000',      # 浦发银行
                '300750',      # 宁德时代
                '688981',      # 中芯国际
                '000001.SZ',   # 平安银行（带后缀）
                'sz000001'     # 平安银行（前缀格式）
            ],
            '美股': [
                'AAPL',        # 苹果
                'TSLA',        # 特斯拉
                'MSFT',        # 微软
                'GOOGL',       # 谷歌
                'NVDA'         # 英伟达
            ],
            '港股': [
                '00001',       # 长和
                '00700',       # 腾讯控股
                '03690',       # 美团点评
                '09988'        # 阿里巴巴
            ]
        }


# 全局实例
_data_selector = None


def get_data_selector(tushare_token: Optional[str] = None,
                     prefer_tushare: bool = True) -> DataSelector:
    """
    获取全局数据源选择器实例
    
    Args:
        tushare_token: TuShare token
        prefer_tushare: 是否优先使用TuShare
        
    Returns:
        DataSelector实例
    """
    global _data_selector
    
    if _data_selector is None:
        _data_selector = DataSelector(
            tushare_token=tushare_token,
            prefer_tushare=prefer_tushare
        )
    
    return _data_selector


# 快捷函数
def get_stock_data_auto(symbol: str,
                       start_date: str,
                       end_date: str,
                       tushare_token: Optional[str] = None) -> pd.DataFrame:
    """
    自动获取股票数据的快捷函数
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        tushare_token: TuShare token
        
    Returns:
        股票数据DataFrame
    """
    selector = get_data_selector(tushare_token=tushare_token)
    return selector.get_stock_data(symbol, start_date, end_date)


def get_stock_info_auto(symbol: str,
                       tushare_token: Optional[str] = None) -> Dict[str, Any]:
    """
    自动获取股票基本信息的快捷函数
    
    Args:
        symbol: 股票代码
        tushare_token: TuShare token
        
    Returns:
        股票基本信息字典
    """
    selector = get_data_selector(tushare_token=tushare_token)
    return selector.get_stock_info(symbol)


# 测试函数
def test_data_selector():
    """测试数据源选择器"""
    selector = DataSelector()
    
    # 测试市场识别
    test_symbols = [
        '000001', '000001.SZ', '600000', '300750', '688981',
        'AAPL', 'TSLA', 'MSFT', 'GOOGL',
        '00001', '00700', '03690'
    ]
    
    print("=== 市场识别测试 ===")
    for symbol in test_symbols:
        market = selector.identify_market(symbol)
        source = selector.get_data_source(symbol)
        print(f"{symbol:12} -> {market:4} ({source['data_source']})")
    
    print("\n=== 支持的市场和示例 ===")
    print("支持的市场:", selector.list_supported_markets())
    print("示例代码:", selector.get_symbol_examples())


if __name__ == "__main__":
    test_data_selector()