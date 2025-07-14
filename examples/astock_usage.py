"""
A股功能使用示例

展示如何使用新的A股数据接口功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tradingagents.dataflows.data_selector import DataSelector, get_stock_data_auto
from tradingagents.dataflows.astock_interface import AStockData
from tradingagents.default_config import DEFAULT_CONFIG


def demo_astock_basic():
    """A股基本功能演示"""
    print("=== A股基本功能演示 ===")
    
    # 创建数据源选择器
    selector = DataSelector(
        tushare_token=DEFAULT_CONFIG["astock"]["tushare_token"],
        prefer_tushare=DEFAULT_CONFIG["astock"]["prefer_tushare"]
    )
    
    # 测试股票代码
    test_symbols = [
        "000001",    # 平安银行
        "600000",    # 浦发银行
        "300750",    # 宁德时代
        "688981",    # 中芯国际
    ]
    
    print("1. 市场识别测试:")
    for symbol in test_symbols:
        market = selector.identify_market(symbol)
        print(f"  {symbol:8} -> {market}")
    
    print("\n2. 股票信息获取:")
    for symbol in test_symbols[:2]:
        info = selector.get_stock_info(symbol)
        print(f"  {symbol:8}: {info.get('shortName', 'N/A')}")
    
    print("\n3. 数据获取测试 (最近5个交易日):")
    try:
        data = selector.get_stock_data("000001", "2024-01-01", "2024-01-10")
        if not data.empty:
            print(f"  数据条数: {len(data)}")
            print(f"  数据列: {list(data.columns)}")
            print(f"  最新价格: {data['Close'].iloc[-1]:.2f}")
        else:
            print("  警告: 未获取到数据")
    except Exception as e:
        print(f"  错误: {e}")


def demo_astock_comprehensive():
    """A股综合功能演示"""
    print("\n=== A股综合功能演示 ===")
    
    # 直接使用A股接口
    astock = AStockData()
    
    # 测试多种股票代码格式
    formats = [
        "000001",
        "000001.SZ", 
        "sz000001",
        "600000",
        "300750",
        "688981"
    ]
    
    print("1. 代码格式标准化:")
    from tradingagents.dataflows.astock_data.stock_code import AStockCode
    
    for code in formats:
        std = AStockCode.standardize(code)
        info = AStockCode.get_market_info(code)
        print(f"  {code:12} -> {std:10} ({info.get('board', 'N/A')})")
    
    print("\n2. 交易日历功能:")
    from tradingagents.dataflows.astock_data.market_calendar import AStockCalendar
    
    calendar = AStockCalendar()
    print(f"  2024-01-02是交易日: {calendar.is_trading_day('2024-01-02')}")
    print(f"  2024-01-01是交易日: {calendar.is_trading_day('2024-01-01')}")
    
    trading_days = calendar.get_trading_days("2024-01-01", "2024-01-10")
    print(f"  2024-01-01到2024-01-10交易日: {len(trading_days)}天")


def demo_astock_vs_us_stock():
    """A股与美股对比演示"""
    print("\n=== A股与美股对比演示 ===")
    
    selector = DataSelector()
    
    # 对比A股和美股
    symbols = {
        "A股": ["000001", "600000"],
        "美股": ["AAPL", "TSLA"],
    }
    
    for market, symbols_list in symbols.items():
        print(f"\n{market}:")
        for symbol in symbols_list:
            source = selector.get_data_source(symbol)
            print(f"  {symbol:8} -> {source['data_source']}")


def demo_error_handling():
    """错误处理演示"""
    print("\n=== 错误处理演示 ===")
    
    selector = DataSelector()
    
    # 测试无效代码
    invalid_codes = [
        "999999",    # 不存在的A股代码
        "XXXXXX",    # 无效格式
        "1234567",   # 长度错误
    ]
    
    for code in invalid_codes:
        try:
            market = selector.identify_market(code)
            print(f"  {code:8} -> {market}")
            
            # 尝试获取数据
            data = selector.get_stock_data(code, "2024-01-01", "2024-01-10")
            print(f"    数据状态: {'成功' if not data.empty else '失败'}")
            
        except Exception as e:
            print(f"    错误: {e}")


def demo_configuration():
    """配置演示"""
    print("\n=== 配置演示 ===")
    
    print("1. 环境变量设置:")
    print("   设置 TuShare Token: export TUSHARE_TOKEN=your_token_here")
    print("   设置结果目录: export TRADINGAGENTS_RESULTS_DIR=./results")
    
    print("\n2. 配置选项:")
    astock_config = DEFAULT_CONFIG["astock"]
    for key, value in astock_config.items():
        print(f"   {key}: {value}")
    
    print("\n3. 使用示例:")
    print("   # 使用自动选择数据源")
    print("   data = get_stock_data_auto('000001', '2024-01-01', '2024-01-31')")
    print("   ")
    print("   # 使用特定数据源")
    print("   astock = AStockData(tushare_token='your_token')")
    print("   data = astock.get_stock_data('000001', '2024-01-01', '2024-01-31')")


def main():
    """主函数"""
    print("A股数据接口功能演示")
    print("=" * 50)
    
    # 检查TuShare token
    tushare_token = DEFAULT_CONFIG["astock"]["tushare_token"]
    if not tushare_token:
        print("⚠️  警告: 未找到TuShare token")
        print("   请设置环境变量: export TUSHARE_TOKEN=your_token_here")
        print("   或使用AkShare作为备用数据源")
    else:
        print("✅ TuShare token已配置")
    
    # 运行演示
    demo_astock_basic()
    demo_astock_comprehensive()
    demo_astock_vs_us_stock()
    demo_error_handling()
    demo_configuration()
    
    print("\n" + "=" * 50)
    print("演示完成！")


if __name__ == "__main__":
    main()