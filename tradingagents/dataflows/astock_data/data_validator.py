"""
A股数据验证器

验证A股数据的完整性、准确性和合规性
处理涨跌停、停牌、退市等特殊情况
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from .stock_code import AStockCode
from .market_calendar import AStockCalendar


class AStockDataValidator:
    """A股数据验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.calendar = AStockCalendar()
        
        # 涨跌停限制
        self.limit_up_down = {
            'ST': 0.05,      # ST股 ±5%
            'normal': 0.10,  # 普通股 ±10%
            'new': 0.44,     # 新股首五日 ±44%
            'kcb': 0.20,     # 科创板 ±20%
            'cyb': 0.20,     # 创业板 ±20%
            'bj': 0.30       # 北交所 ±30%
        }
    
    def validate_stock_data(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        验证股票数据完整性
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            
        Returns:
            验证结果字典
        """
        if df is None or df.empty:
            return {
                'valid': False,
                'errors': ['数据为空'],
                'warnings': [],
                'summary': {}
            }
        
        errors = []
        warnings = []
        summary = {}
        
        try:
            # 基本数据检查
            required_columns = ['Open', 'Close', 'High', 'Low', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"缺少必要列: {missing_columns}")
            
            # 数据类型检查
            for col in ['Open', 'Close', 'High', 'Low']:
                if col in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        errors.append(f"{col}列数据类型应为数值型")
            
            # 数据范围检查
            price_columns = ['Open', 'Close', 'High', 'Low']
            for col in price_columns:
                if col in df.columns:
                    invalid_mask = (df[col] <= 0) | df[col].isna()
                    if invalid_mask.any():
                        warnings.append(f"{col}列存在无效价格数据: {invalid_mask.sum()}条")
            
            # 价格逻辑检查
            if all(col in df.columns for col in ['High', 'Low', 'Open', 'Close']):
                invalid_price = (
                    (df['High'] < df['Low']) |
                    (df['High'] < df['Open']) |
                    (df['High'] < df['Close']) |
                    (df['Low'] > df['Open']) |
                    (df['Low'] > df['Close'])
                )
                if invalid_price.any():
                    errors.append(f"价格逻辑错误: {invalid_price.sum()}条")
            
            # 成交量检查
            if 'Volume' in df.columns:
                invalid_volume = (df['Volume'] < 0) | df['Volume'].isna()
                if invalid_volume.any():
                    warnings.append(f"成交量数据异常: {invalid_volume.sum()}条")
            
            # 生成数据摘要
            summary = self._generate_data_summary(df, symbol)
            
            valid = len(errors) == 0
            
        except Exception as e:
            errors.append(f"验证过程出错: {str(e)}")
            valid = False
        
        return {
            'valid': valid,
            'errors': errors,
            'warnings': warnings,
            'summary': summary
        }
    
    def _generate_data_summary(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """生成数据摘要"""
        if df.empty:
            return {}
        
        summary = {
            'total_days': len(df),
            'start_date': df.index.min().strftime('%Y-%m-%d') if hasattr(df.index, 'min') else None,
            'end_date': df.index.max().strftime('%Y-%m-%d') if hasattr(df.index, 'max') else None,
            'missing_days': 0,
            'price_range': {},
            'volume_stats': {},
            'volatility': 0
        }
        
        try:
            # 价格范围
            if 'Close' in df.columns:
                summary['price_range'] = {
                    'min_price': float(df['Close'].min()),
                    'max_price': float(df['Close'].max()),
                    'avg_price': float(df['Close'].mean())
                }
            
            # 成交量统计
            if 'Volume' in df.columns:
                summary['volume_stats'] = {
                    'min_volume': int(df['Volume'].min()),
                    'max_volume': int(df['Volume'].max()),
                    'avg_volume': int(df['Volume'].mean())
                }
            
            # 波动率计算
            if 'Close' in df.columns and len(df) > 1:
                returns = df['Close'].pct_change().dropna()
                if len(returns) > 0:
                    summary['volatility'] = float(returns.std() * np.sqrt(252))  # 年化波动率
            
            # 检查缺失交易日
            if hasattr(df.index, 'min') and hasattr(df.index, 'max'):
                expected_days = self.calendar.count_trading_days(
                    df.index.min().strftime('%Y-%m-%d'),
                    df.index.max().strftime('%Y-%m-%d')
                )
                summary['missing_days'] = max(0, expected_days - len(df))
        
        except Exception:
            pass
        
        return summary
    
    def validate_price_limit(self, df: pd.DataFrame, symbol: str) -> List[Dict[str, Any]]:
        """
        验证涨跌停限制
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            
        Returns:
            涨跌停违规记录列表
        """
        if df.empty or 'Close' not in df.columns:
            return []
        
        violations = []
        
        try:
            # 获取股票信息
            stock_info = AStockCode.get_market_info(symbol)
            market = stock_info.get('market', 'SZ')
            prefix = stock_info.get('prefix', '000')
            
            # 确定涨跌停限制
            limit_rate = self._get_limit_rate(market, prefix)
            
            # 计算日涨跌幅
            df = df.sort_index()
            df['prev_close'] = df['Close'].shift(1)
            df['change_pct'] = (df['Close'] - df['prev_close']) / df['prev_close']
            
            # 检查涨跌停
            for idx, row in df.iterrows():
                if pd.isna(row['change_pct']) or pd.isna(row['prev_close']):
                    continue
                
                change_pct = abs(row['change_pct'])
                
                # 检查是否超过涨跌停限制
                if change_pct > limit_rate + 0.001:  # 允许微小误差
                    violations.append({
                        'date': idx.strftime('%Y-%m-%d'),
                        'price': float(row['Close']),
                        'prev_close': float(row['prev_close']),
                        'change_pct': float(row['change_pct']),
                        'limit_rate': limit_rate,
                        'violation_type': 'exceed_limit'
                    })
        
        except Exception:
            pass
        
        return violations
    
    def _get_limit_rate(self, market: str, prefix: str) -> float:
        """获取股票涨跌停限制"""
        # 根据市场类型和股票代码前缀确定限制
        if prefix.startswith('688') or prefix.startswith('689'):
            return self.limit_up_down['kcb']  # 科创板
        elif prefix.startswith('300') or prefix.startswith('301'):
            return self.limit_up_down['cyb']  # 创业板
        elif market == 'BJ':
            return self.limit_up_down['bj']   # 北交所
        else:
            return self.limit_up_down['normal']  # 普通股
    
    def check_suspension_days(self, df: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        检查停牌日期
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            停牌日期列表
        """
        if df.empty:
            return []
        
        suspension_days = []
        
        try:
            # 获取指定范围内的所有交易日
            expected_trading_days = self.calendar.get_trading_days(start_date, end_date)
            
            # 获取实际数据日期
            actual_dates = set()
            if hasattr(df.index, 'date'):
                actual_dates = set([d.date() for d in df.index])
            
            # 找出缺失的交易日（可能的停牌日）
            for trading_day in expected_trading_days:
                if trading_day.date() not in actual_dates:
                    suspension_days.append({
                        'date': trading_day.strftime('%Y-%m-%d'),
                        'type': 'suspension',
                        'reason': '停牌'
                    })
        
        except Exception:
            pass
        
        return suspension_days
    
    def validate_volume_pattern(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证成交量模式
        
        Args:
            df: 股票数据DataFrame
            
        Returns:
            成交量验证结果
        """
        if df.empty or 'Volume' not in df.columns:
            return {'valid': False, 'issues': []}
        
        volume = df['Volume']
        issues = []
        
        try:
            # 检查异常低成交量
            if len(volume) > 20:
                avg_volume = volume.rolling(window=20).mean()
                low_volume_days = (volume < avg_volume * 0.1) & (volume > 0)
                if low_volume_days.any():
                    issues.append({
                        'type': 'low_volume',
                        'count': int(low_volume_days.sum()),
                        'description': f'成交量异常低的天数: {low_volume_days.sum()}'
                    })
            
            # 检查成交量为0的天数
            zero_volume_days = (volume == 0)
            if zero_volume_days.any():
                issues.append({
                    'type': 'zero_volume',
                    'count': int(zero_volume_days.sum()),
                    'description': f'成交量为0的天数: {zero_volume_days.sum()}'
                })
            
            # 检查成交量异常高
            if len(volume) > 20:
                std_volume = volume.rolling(window=20).std()
                high_volume_days = volume > (volume.rolling(window=20).mean() + 3 * std_volume)
                if high_volume_days.any():
                    issues.append({
                        'type': 'high_volume',
                        'count': int(high_volume_days.sum()),
                        'description': f'成交量异常高的天数: {high_volume_days.sum()}'
                    })
        
        except Exception:
            pass
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def check_data_continuity(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        检查数据连续性
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            
        Returns:
            连续性检查结果
        """
        if df.empty:
            return {'continuous': False, 'gaps': []}
        
        gaps = []
        
        try:
            # 获取数据日期范围
            if hasattr(df.index, 'min') and hasattr(df.index, 'max'):
                start_date = df.index.min()
                end_date = df.index.max()
                
                # 获取预期的交易日
                expected_days = self.calendar.get_trading_days(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                # 转换为日期集合
                actual_days = set([d.date() if hasattr(d, 'date') else d for d in df.index])
                expected_day_dates = set([d.date() for d in expected_days])
                
                # 找出缺失的日期
                missing_days = expected_day_dates - actual_days
                
                if missing_days:
                    # 将缺失日期按连续区间分组
                    sorted_missing = sorted(missing_days)
                    current_gap = []
                    
                    for i, missing_date in enumerate(sorted_missing):
                        if not current_gap:
                            current_gap = [missing_date]
                        else:
                            prev_date = sorted_missing[i-1]
                            if (missing_date - prev_date).days == 1:
                                current_gap.append(missing_date)
                            else:
                                if len(current_gap) > 1:
                                    gaps.append({
                                        'start': current_gap[0].strftime('%Y-%m-%d'),
                                        'end': current_gap[-1].strftime('%Y-%m-%d'),
                                        'days': len(current_gap),
                                        'type': 'continuous_gap'
                                    })
                                else:
                                    gaps.append({
                                        'date': current_gap[0].strftime('%Y-%m-%d'),
                                        'type': 'single_gap'
                                    })
                                current_gap = [missing_date]
                    
                    # 处理最后一组
                    if current_gap:
                        if len(current_gap) > 1:
                            gaps.append({
                                'start': current_gap[0].strftime('%Y-%m-%d'),
                                'end': current_gap[-1].strftime('%Y-%m-%d'),
                                'days': len(current_gap),
                                'type': 'continuous_gap'
                            })
                        else:
                            gaps.append({
                                'date': current_gap[0].strftime('%Y-%m-%d'),
                                'type': 'single_gap'
                            })
        
        except Exception:
            pass
        
        return {
            'continuous': len(gaps) == 0,
            'gaps': gaps,
            'total_gaps': len(gaps)
        }
    
    def get_validation_report(self, df: pd.DataFrame, symbol: str, 
                            start_date: str, end_date: str) -> Dict[str, Any]:
        """
        获取完整的验证报告
        
        Args:
            df: 股票数据DataFrame
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            完整验证报告
        """
        report = {
            'symbol': symbol,
            'validation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date_range': {'start': start_date, 'end': end_date},
            'basic_validation': self.validate_stock_data(df, symbol),
            'price_limit_violations': self.validate_price_limit(df, symbol),
            'suspension_days': self.check_suspension_days(df, symbol, start_date, end_date),
            'volume_validation': self.validate_volume_pattern(df),
            'continuity_check': self.check_data_continuity(df, symbol),
            'overall_score': 0
        }
        
        # 计算总体评分
        report['overall_score'] = self._calculate_overall_score(report)
        
        return report
    
    def _calculate_overall_score(self, report: Dict[str, Any]) -> float:
        """计算总体数据质量评分"""
        score = 100.0
        
        # 基本验证扣分
        if not report['basic_validation']['valid']:
            score -= 20
        
        # 涨跌停违规扣分
        violations = report['price_limit_violations']
        if violations:
            score -= min(len(violations) * 5, 30)
        
        # 停牌天数扣分
        suspensions = report['suspension_days']
        if suspensions:
            score -= min(len(suspensions) * 2, 20)
        
        # 成交量问题扣分
        volume_issues = report['volume_validation']['issues']
        if volume_issues:
            score -= min(len(volume_issues) * 3, 15)
        
        # 连续性扣分
        continuity = report['continuity_check']
        if not continuity['continuous']:
            score -= min(continuity['total_gaps'] * 3, 15)
        
        return max(score, 0)


# 测试函数
def test_data_validator():
    """测试数据验证器"""
    validator = AStockDataValidator()
    
    # 创建测试数据
    dates = pd.date_range('2024-01-01', '2024-01-31', freq='D')
    test_data = pd.DataFrame({
        'Open': [10.0] * len(dates),
        'Close': [10.5] * len(dates),
        'High': [11.0] * len(dates),
        'Low': [9.5] * len(dates),
        'Volume': [1000000] * len(dates)
    }, index=dates)
    
    # 验证数据
    report = validator.get_validation_report(
        test_data, "000001", "2024-01-01", "2024-01-31"
    )
    
    print("数据验证报告:")
    print(f"股票代码: {report['symbol']}")
    print(f"验证时间: {report['validation_date']}")
    print(f"总体评分: {report['overall_score']}/100")
    print(f"基本验证通过: {report['basic_validation']['valid']}")
    print(f"数据条数: {report['basic_validation']['summary'].get('total_days', 0)}")


if __name__ == "__main__":
    test_data_validator()