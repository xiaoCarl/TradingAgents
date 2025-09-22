#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据采集功能测试运行脚本

运行所有A股相关的测试用例
"""

import unittest
import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """运行所有A股测试"""
    print("🚀 开始运行A股数据采集功能测试...")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有A股测试模块
    test_modules = [
        'tests.astock_tests.test_astock_interface',
        'tests.astock_tests.test_data_validator',
        'tests.astock_tests.test_stock_code',
        'tests.astock_tests.test_market_calendar',
    ]
    
    for module_name in test_modules:
        try:
            suite.addTests(loader.loadTestsFromName(module_name))
            print(f"✅ 已加载测试模块: {module_name}")
        except Exception as e:
            print(f"❌ 加载测试模块失败: {module_name} - {e}")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   总测试数: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失败: {len(result.failures)}")
    print(f"   错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ 出错的测试:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    return result.wasSuccessful()

def run_specific_test(test_name):
    """运行特定测试"""
    print(f"🎯 运行特定测试: {test_name}")
    
    loader = unittest.TestLoader()
    
    try:
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False

def show_test_help():
    """显示测试帮助信息"""
    print("""
A股数据采集功能测试帮助

使用方法:
    python tests/run_astock_tests.py          # 运行所有测试
    python tests/run_astock_tests.py -t 模块名 # 运行特定测试模块
    python tests/run_astock_tests.py -h       # 显示帮助

可用测试模块:
    tests.astock_tests.test_astock_interface  - A股数据接口测试
    tests.astock_tests.test_data_validator    - 数据验证测试
    tests.astock_tests.test_stock_code        - 股票代码验证测试
    tests.astock_tests.test_market_calendar   - 交易日历测试

示例:
    python tests/run_astock_tests.py -t tests.astock_tests.test_stock_code
    python tests/run_astock_tests.py -t tests.astock_tests.test_astock_interface.TestAStockInterface.test_stock_code_validation
    """)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='A股数据采集功能测试')
    parser.add_argument('-t', '--test', help='运行特定测试模块或测试用例')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有测试模块')
    parser.add_argument('-h', '--help', action='help', help='显示帮助信息')
    
    args = parser.parse_args()
    
    if args.list:
        print("可用测试模块:")
        print("  - tests.astock_tests.test_astock_interface")
        print("  - tests.astock_tests.test_data_validator")
        print("  - tests.astock_tests.test_stock_code")
        print("  - tests.astock_tests.test_market_calendar")
        return
    
    if args.test:
        success = run_specific_test(args.test)
    else:
        success = run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)

if __name__ == '__main__':
    # 如果直接运行脚本，显示帮助
    if len(sys.argv) == 1:
        show_test_help()
        print("运行以下命令执行所有测试:")
        print("  python tests/run_astock_tests.py")
    else:
        main()