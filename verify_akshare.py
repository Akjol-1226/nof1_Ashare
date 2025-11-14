#!/usr/bin/env python3
"""
AKShare接口验证脚本
验证关键接口的可用性、响应速度和数据完整性
"""

import akshare as ak
import time
from datetime import datetime
import pandas as pd

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_realtime_quotes():
    """测试实时行情接口"""
    print_section("1. 测试实时行情接口 - stock_zh_a_spot_em()")
    
    try:
        start_time = time.time()
        df = ak.stock_zh_a_spot_em()
        elapsed = time.time() - start_time
        
        print(f"✅ 成功获取数据")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")
        print(f"📊 数据行数: {len(df)} 只股票")
        print(f"📋 数据列: {list(df.columns)}")
        print(f"\n前5行数据样例:")
        print(df.head())
        
        # 检查关键字段
        required_fields = ['代码', '名称', '最新价', '涨跌幅', '成交量', '成交额']
        missing_fields = [f for f in required_fields if f not in df.columns]
        
        if missing_fields:
            print(f"\n⚠️  缺失字段: {missing_fields}")
        else:
            print(f"\n✅ 所有关键字段完整")
        
        # 检查数据质量
        print(f"\n数据质量检查:")
        print(f"  - 是否有空值: {df[required_fields].isnull().any().any()}")
        print(f"  - 最新价范围: {df['最新价'].min():.2f} ~ {df['最新价'].max():.2f}")
        print(f"  - 涨跌幅范围: {df['涨跌幅'].min():.2f}% ~ {df['涨跌幅'].max():.2f}%")
        
        return True, elapsed, len(df)
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False, 0, 0

def test_stock_list():
    """测试股票列表接口"""
    print_section("2. 测试股票列表接口 - stock_info_a_code_name()")
    
    try:
        start_time = time.time()
        df = ak.stock_info_a_code_name()
        elapsed = time.time() - start_time
        
        print(f"✅ 成功获取数据")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")
        print(f"📊 股票总数: {len(df)} 只")
        print(f"📋 数据列: {list(df.columns)}")
        print(f"\n前10行数据样例:")
        print(df.head(10))
        
        return True, elapsed
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False, 0

def test_historical_data():
    """测试历史行情接口"""
    print_section("3. 测试历史行情接口 - stock_zh_a_hist()")
    
    # 测试贵州茅台
    stock_code = "600519"
    
    try:
        start_time = time.time()
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date="20241101",
            end_date="20241110",
            adjust="qfq"  # 前复权
        )
        elapsed = time.time() - start_time
        
        print(f"✅ 成功获取数据 (股票代码: {stock_code})")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")
        print(f"📊 数据行数: {len(df)} 天")
        print(f"📋 数据列: {list(df.columns)}")
        print(f"\n数据样例:")
        print(df)
        
        # 检查关键字段
        required_fields = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']
        missing_fields = [f for f in required_fields if f not in df.columns]
        
        if missing_fields:
            print(f"\n⚠️  缺失字段: {missing_fields}")
        else:
            print(f"\n✅ 所有关键字段完整")
        
        return True, elapsed
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False, 0

def test_minute_data():
    """测试分钟级数据接口"""
    print_section("4. 测试分钟级数据接口 - stock_zh_a_hist_min_em()")
    
    # 测试贵州茅台
    stock_code = "600519"
    
    try:
        start_time = time.time()
        df = ak.stock_zh_a_hist_min_em(
            symbol=stock_code,
            period="5",  # 5分钟K线
            adjust="qfq"
        )
        elapsed = time.time() - start_time
        
        print(f"✅ 成功获取数据 (股票代码: {stock_code}, 5分钟K线)")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")
        print(f"📊 数据行数: {len(df)} 条")
        print(f"📋 数据列: {list(df.columns)}")
        print(f"\n最近10条数据:")
        print(df.tail(10))
        
        return True, elapsed
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
        return False, 0

def test_trading_time_check():
    """检查当前是否在交易时间"""
    print_section("5. 交易时间检查")
    
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"星期: {['一', '二', '三', '四', '五', '六', '日'][weekday]}")
    
    # A股交易时间：周一到周五 9:30-11:30, 13:00-15:00
    is_trading_day = weekday < 5  # 周一到周五
    
    morning_start = datetime.strptime("09:30", "%H:%M").time()
    morning_end = datetime.strptime("11:30", "%H:%M").time()
    afternoon_start = datetime.strptime("13:00", "%H:%M").time()
    afternoon_end = datetime.strptime("15:00", "%H:%M").time()
    
    is_trading_time = is_trading_day and (
        (morning_start <= current_time <= morning_end) or
        (afternoon_start <= current_time <= afternoon_end)
    )
    
    if is_trading_time:
        print(f"✅ 当前在交易时间内")
    else:
        print(f"⚠️  当前不在交易时间内")
        print(f"   交易时间: 周一至周五 9:30-11:30, 13:00-15:00")

def main():
    """主函数"""
    print(f"\n{'#'*60}")
    print(f"#  AKShare 接口验证测试")
    print(f"#  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    results = {}
    
    # 测试各个接口
    results['realtime'] = test_realtime_quotes()
    results['stock_list'] = test_stock_list()
    results['historical'] = test_historical_data()
    results['minute'] = test_minute_data()
    test_trading_time_check()
    
    # 总结报告
    print_section("测试总结")
    
    total_tests = 4
    passed_tests = sum(1 for r in results.values() if r[0])
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    
    if results['realtime'][0]:
        realtime_speed = results['realtime'][1]
        stock_count = results['realtime'][2]
        print(f"\n实时行情:")
        print(f"  - 响应速度: {realtime_speed:.2f}秒")
        print(f"  - 股票数量: {stock_count}只")
        print(f"  - 10秒轮询: {'✅ 可行' if realtime_speed < 8 else '⚠️  可能较慢'}")
    
    print("\n" + "="*60)
    
    if passed_tests == total_tests:
        print("✅ 所有测试通过！AKShare接口可以满足项目需求。")
    else:
        print("⚠️  部分测试失败，请检查网络连接和AKShare版本。")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()


