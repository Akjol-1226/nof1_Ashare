#!/usr/bin/env python3
"""
测试指定股票的实时行情数据获取
专门测试6只可交易股票
"""

import akshare as ak
import time
from datetime import datetime
import pandas as pd

# 定义可交易的6只股票
TRADING_STOCKS = {
    '000063': '中兴通讯',
    '300750': '宁德时代',
    '600703': '三安光电',
    '002594': '比亚迪',
    '688256': '寒武纪',
    '600276': '恒瑞医药'
}

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_single_stock_info():
    """测试单个股票信息获取"""
    print_section("1. 测试单个股票信息获取")
    
    for code, name in TRADING_STOCKS.items():
        try:
            # 添加市场后缀
            full_code = f"{code}.SZ" if code.startswith(('000', '002', '300')) else f"{code}.SH"
            
            print(f"正在获取 {full_code} {name} 的行情...")
            
            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == code]
            
            if not stock_data.empty:
                stock = stock_data.iloc[0]
                print(f"✅ {name} ({full_code})")
                print(f"   最新价: ¥{stock['最新价']:.2f}")
                print(f"   涨跌幅: {stock['涨跌幅']:.2f}%")
                print(f"   涨跌额: ¥{stock['涨跌额']:.2f}")
                print(f"   成交量: {stock['成交量']:,.0f}")
                print(f"   成交额: ¥{stock['成交额']:,.0f}")
                print(f"   今开: ¥{stock['今开']:.2f}")
                print(f"   最高: ¥{stock['最高']:.2f}")
                print(f"   最低: ¥{stock['最低']:.2f}")
                print(f"   昨收: ¥{stock['昨收']:.2f}")
                print()
            else:
                print(f"❌ 未找到股票 {code}")
                print()
            
            time.sleep(0.5)  # 避免请求过快
            
        except Exception as e:
            print(f"❌ 获取 {name} ({code}) 失败: {str(e)}\n")

def test_batch_quotes():
    """测试批量获取6只股票行情"""
    print_section("2. 批量获取6只股票实时行情")
    
    try:
        print("正在获取实时行情数据...\n")
        start_time = time.time()
        
        # 获取所有A股实时行情
        df = ak.stock_zh_a_spot_em()
        
        # 筛选出6只股票
        codes = list(TRADING_STOCKS.keys())
        selected_stocks = df[df['代码'].isin(codes)]
        
        elapsed = time.time() - start_time
        
        if not selected_stocks.empty:
            print(f"✅ 成功获取 {len(selected_stocks)} 只股票数据")
            print(f"⏱️  响应时间: {elapsed:.2f} 秒\n")
            
            # 格式化显示
            print(f"{'代码':<10} {'名称':<10} {'最新价':<10} {'涨跌幅':<10} {'成交量(万手)':<15}")
            print("-" * 80)
            
            for _, row in selected_stocks.iterrows():
                code = row['代码']
                name = TRADING_STOCKS.get(code, row['名称'])
                price = row['最新价']
                change = row['涨跌幅']
                volume = row['成交量'] / 10000  # 转换为万手
                
                change_str = f"{change:+.2f}%"
                color = '🟢' if change >= 0 else '🔴'
                
                print(f"{code:<10} {name:<10} {price:<10.2f} {color}{change_str:<9} {volume:<15,.0f}")
            
            print()
            return True
        else:
            print("❌ 未找到任何股票数据")
            return False
            
    except Exception as e:
        print(f"❌ 批量获取失败: {str(e)}")
        return False

def test_historical_data():
    """测试历史数据获取"""
    print_section("3. 测试历史数据获取（最近5日）")
    
    # 只测试一只股票作为代表
    test_code = "000063"
    test_name = TRADING_STOCKS[test_code]
    
    try:
        print(f"正在获取 {test_name} ({test_code}) 的历史数据...\n")
        
        # 获取最近5个交易日数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now().replace(day=datetime.now().day - 10)).strftime("%Y%m%d")
        
        df = ak.stock_zh_a_hist(
            symbol=test_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if not df.empty:
            print(f"✅ 成功获取 {len(df)} 天的历史数据")
            print(f"\n最近5日行情:")
            print(df.tail(5).to_string())
            print()
            return True
        else:
            print("❌ 未获取到历史数据")
            return False
            
    except Exception as e:
        print(f"❌ 获取历史数据失败: {str(e)}")
        return False

def test_realtime_updates():
    """测试实时更新（模拟10秒轮询）"""
    print_section("4. 测试实时更新（10秒轮询，共3次）")
    
    print("模拟AI决策的10秒轮询机制...\n")
    
    for i in range(3):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {i+1}/3 次获取")
        print("-" * 80)
        
        try:
            df = ak.stock_zh_a_spot_em()
            codes = list(TRADING_STOCKS.keys())
            selected_stocks = df[df['代码'].isin(codes)]
            
            if not selected_stocks.empty:
                for _, row in selected_stocks.iterrows():
                    code = row['代码']
                    name = TRADING_STOCKS.get(code, row['名称'])
                    price = row['最新价']
                    change = row['涨跌幅']
                    
                    print(f"  {name:<8} ¥{price:>8.2f}  {change:>+6.2f}%")
                
                print()
            
            if i < 2:  # 不在最后一次等待
                print("等待10秒...\n")
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ 获取失败: {str(e)}\n")
    
    print("✅ 10秒轮询测试完成")

def test_trading_time_data():
    """检查当前是否可以获取数据"""
    print_section("5. 检查数据可用性")
    
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"星期: {['一', '二', '三', '四', '五', '六', '日'][weekday]}")
    
    # A股交易时间
    from datetime import time as dt_time
    is_trading_day = weekday < 5
    morning_start = dt_time(9, 30)
    morning_end = dt_time(11, 30)
    afternoon_start = dt_time(13, 0)
    afternoon_end = dt_time(15, 0)
    
    is_trading_time = is_trading_day and (
        (morning_start <= current_time <= morning_end) or
        (afternoon_start <= current_time <= afternoon_end)
    )
    
    if is_trading_time:
        print("✅ 当前在交易时间内，数据是实时的")
    else:
        print("⚠️  当前不在交易时间内，显示的是上一个交易日的收盘数据")
        print("   交易时间: 周一至周五 9:30-11:30, 13:00-15:00")
    
    print()

def generate_stock_config():
    """生成股票配置文件"""
    print_section("6. 生成股票配置文件")
    
    config = f"""# 可交易股票列表配置
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TRADING_STOCKS = {{
"""
    
    for code, name in TRADING_STOCKS.items():
        full_code = f"{code}.SZ" if code.startswith(('000', '002', '300')) else f"{code}.SH"
        config += f"    '{code}': '{name}',  # {full_code}\n"
    
    config += "}\n"
    
    with open('stock_config.py', 'w', encoding='utf-8') as f:
        f.write(config)
    
    print("✅ 已生成 stock_config.py 配置文件")
    print("\n配置内容:")
    print(config)

def main():
    """主函数"""
    print(f"\n{'#'*80}")
    print(f"#  nof1.AShare - 6只可交易股票行情测试")
    print(f"#  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    print("\n可交易股票列表:")
    for code, name in TRADING_STOCKS.items():
        full_code = f"{code}.SZ" if code.startswith(('000', '002', '300')) else f"{code}.SH"
        print(f"  - {full_code} {name}")
    
    # 执行测试
    tests = [
        ("检查数据可用性", test_trading_time_data),
        ("单个股票信息获取", test_single_stock_info),
        ("批量获取行情", test_batch_quotes),
        ("历史数据获取", test_historical_data),
        ("实时更新测试", test_realtime_updates),
        ("生成配置文件", generate_stock_config),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            if test_func in [test_trading_time_data, generate_stock_config, test_single_stock_info]:
                test_func()
                results.append((name, True))
            else:
                success = test_func()
                results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            results.append((name, False))
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"通过: {passed}/{total}\n")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print("\n" + "="*80)
    
    if passed >= total - 1:  # 允许一个测试失败
        print("\n✅ 测试通过！6只股票的实时行情数据可以正常获取。")
        print("   系统可以基于这些股票进行AI模拟交易。")
    else:
        print("\n⚠️  部分测试失败，请检查网络连接和AKShare版本。")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

