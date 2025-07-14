"""
A股代码标准化工具

处理各种A股代码格式，统一转换为标准格式
支持沪市、深市、创业板、科创板
"""

import re
from typing import Optional, Tuple


class AStockCode:
    """A股代码标准化处理类"""
    
    # 市场代码映射
    MARKET_MAPPING = {
        'sh': 'SH',
        'sz': 'SZ', 
        'bj': 'BJ'  # 北交所
    }
    
    # 板块定义
    BOARD_DEFINITIONS = {
        '600': 'SH',      # 沪市主板
        '601': 'SH',      # 沪市主板
        '603': 'SH',      # 沪市主板
        '605': 'SH',      # 沪市主板
        '000': 'SZ',      # 深市主板
        '001': 'SZ',      # 深市主板
        '002': 'SZ',      # 深市中小板
        '003': 'SZ',      # 深市中小板
        '300': 'SZ',      # 创业板
        '301': 'SZ',      # 创业板
        '688': 'SH',      # 科创板
        '689': 'SH',      # 科创板
        '830': 'BJ',      # 北交所
        '831': 'BJ',      # 北交所
        '832': 'BJ',      # 北交所
        '833': 'BJ',      # 北交所
        '835': 'BJ',      # 北交所
        '836': 'BJ',      # 北交所
        '837': 'BJ',      # 北交所
        '838': 'BJ',      # 北交所
        '839': 'BJ',      # 北交所
    }
    
    @classmethod
    def standardize(cls, code: str) -> Optional[str]:
        """
        将各种格式的A股代码标准化为 000001.SZ 格式
        
        Args:
            code: 输入的股票代码，支持多种格式
                 - 000001
                 - 000001.SZ
                 - sz000001
                 - SH600000
                 - 600000
        
        Returns:
            标准化的股票代码，如 000001.SZ，如果无法识别则返回None
        """
        if not code:
            return None
            
        code = str(code).strip().upper()
        
        # 处理带市场后缀的格式
        pattern_with_suffix = r'(\d{6})\.?(SH|SZ|BJ)'
        match = re.match(pattern_with_suffix, code)
        if match:
            stock_code, market = match.groups()
            return f"{stock_code}.{market}"
        
        # 处理前缀格式，如 sz000001
        pattern_with_prefix = r'(SH|SZ|BJ)(\d{6})'
        match = re.match(pattern_with_prefix, code)
        if match:
            market, stock_code = match.groups()
            return f"{stock_code}.{market}"
        
        # 处理纯6位数字格式
        pattern_numeric = r'(\d{6})'
        match = re.match(pattern_numeric, code)
        if match:
            stock_code = match.group(1)
            market = cls._infer_market(stock_code)
            if market:
                return f"{stock_code}.{market}"
        
        return None
    
    @classmethod
    def _infer_market(cls, code: str) -> Optional[str]:
        """
        根据股票代码前3位推断所属市场
        
        Args:
            code: 6位股票代码
            
        Returns:
            市场代码 (SH/SZ/BJ) 或 None
        """
        if len(code) != 6:
            return None
            
        prefix = code[:3]
        for key, market in cls.BOARD_DEFINITIONS.items():
            if prefix.startswith(key):
                return market
        
        return None
    
    @classmethod
    def get_market_info(cls, code: str) -> dict:
        """
        获取股票的市场信息
        
        Args:
            code: 股票代码
            
        Returns:
            包含市场、板块等信息的字典
        """
        std_code = cls.standardize(code)
        if not std_code:
            return {}
        
        stock_code, market = std_code.split('.')
        prefix = stock_code[:3]
        
        # 确定板块
        board = "主板"
        if prefix == '002' or prefix == '003':
            board = "中小板"
        elif prefix == '300' or prefix == '301':
            board = "创业板"
        elif prefix == '688' or prefix == '689':
            board = "科创板"
        elif market == 'BJ':
            board = "北交所"
        
        return {
            'code': std_code,
            'pure_code': stock_code,
            'market': market,
            'board': board,
            'prefix': prefix
        }
    
    @classmethod
    def is_valid(cls, code: str) -> bool:
        """验证股票代码是否有效"""
        return cls.standardize(code) is not None
    
    @classmethod
    def to_tushare_format(cls, code: str) -> Optional[str]:
        """
        转换为TuShare格式 (市场前缀 + 代码)
        如：000001.SZ -> sz000001
        """
        std_code = cls.standardize(code)
        if not std_code:
            return None
        
        stock_code, market = std_code.split('.')
        return f"{market.lower()}{stock_code}"
    
    @classmethod
    def to_display_format(cls, code: str) -> Optional[str]:
        """
        转换为显示格式
        如：000001.SZ -> 000001
        """
        std_code = cls.standardize(code)
        if not std_code:
            return None
        
        return std_code.split('.')[0]


def test_stock_code():
    """测试函数"""
    test_cases = [
        "000001",
        "000001.SZ", 
        "sz000001",
        "SZ000001",
        "600000",
        "600000.SH",
        "sh600000",
        "300750",
        "688981",
        "830799"
    ]
    
    for code in test_cases:
        std = AStockCode.standardize(code)
        info = AStockCode.get_market_info(code)
        tushare = AStockCode.to_tushare_format(code)
        print(f"{code:12} -> {std:10} | {info} | {tushare}")


if __name__ == "__main__":
    test_stock_code()