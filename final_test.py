#!/usr/bin/env python3
"""
最终系统测试
验证整个后端系统是否能正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 导入代理禁用
try:
    import disable_proxy
except:
    print("⚠️ 未能加载代理禁用模块")

from data_service.akshare_client import AKShareClient
from datetime import datetime

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_akshare_client():
    """测试AKShare客户端"""
    print_section("测试AKShare客户端")
    
    print("初始化客户端...")
    client = AKShareClient(cache_expire=10, max_retries=3)
    
    print("✅ 客户端初始化成功\n")
    
    # 测试获取实时行情
    print("获取6只可交易股票的实时行情...")
    quotes = client.get_realtime_quotes()
    
    if quotes:
        print(f"✅ 成功获取 {len(quotes)} 只股票的数据\n")
        
        print(f"{'代码':<10} {'名称':<10} {'最新价':<10} {'涨跌幅':<10} {'成交量(万手)':<15}")
        print("-" * 80)
        
        for quote in quotes:
            volume_wanshou = quote.volume / 10000
            change_str = f"{quote.change_percent:+.2f}%"
            color = '🟢' if quote.change_percent >= 0 else '🔴'
            
            print(f"{quote.code:<10} {quote.name:<10} ¥{quote.price:<9.2f} {color}{change_str:<9} {volume_wanshou:<15,.0f}")
        
        print()
        return True, len(quotes)
    else:
        print("❌ 未能获取任何数据")
        return False, 0

def test_cache():
    """测试缓存机制"""
    print_section("测试缓存机制")
    
    client = AKShareClient(cache_expire=10)
    
    print("第一次获取（从API）...")
    import time
    start = time.time()
    quotes1 = client.get_realtime_quotes()
    time1 = time.time() - start
    
    print(f"耗时: {time1:.2f}秒，获取 {len(quotes1)} 只股票")
    
    print("\n第二次获取（从缓存）...")
    start = time.time()
    quotes2 = client.get_realtime_quotes()
    time2 = time.time() - start
    
    print(f"耗时: {time2:.2f}秒，获取 {len(quotes2)} 只股票")
    
    if time2 < time1 / 10:  # 缓存应该快很多
        print(f"\n✅ 缓存工作正常（快了{time1/time2:.0f}倍）")
        return True
    else:
        print("\n⚠️ 缓存可能未生效")
        return False

def test_historical_data():
    """测试历史数据获取"""
    print_section("测试历史数据获取")
    
    client = AKShareClient()
    
    print("获取中兴通讯（000063）最近5日数据...")
    df = client.get_historical_data("000063")
    
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 天的数据")
        print("\n最近3日:")
        print(df.tail(3)[['日期', '开盘', '收盘', '最高', '最低', '涨跌幅']])
        print()
        return True
    else:
        print("❌ 未能获取历史数据")
        return False

def main():
    print(f"\n{'#'*80}")
    print(f"#  nof1.AShare 系统最终测试")
    print(f"#  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    results = []
    
    # 测试1: AKShare客户端
    success, count = test_akshare_client()
    results.append(("实时行情获取", success))
    
    # 测试2: 缓存机制
    if success:
        cache_ok = test_cache()
        results.append(("缓存机制", cache_ok))
    
    # 测试3: 历史数据
    hist_ok = test_historical_data()
    results.append(("历史数据获取", hist_ok))
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    print(f"测试结果: {passed}/{total} 通过\n")
    
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
    
    print("\n" + "="*80)
    
    if passed == total:
        print("\n🎉 完美！所有测试通过！")
        print("\n系统已就绪，可以启动后端服务:")
        print("  cd backend")
        print("  python3 main.py")
        print("\n然后访问:")
        print("  - API文档: http://localhost:8000/docs")
        print("  - 测试页面: test_stocks.html")
    elif passed >= 2:
        print(f"\n✅ 系统基本可用 ({passed}/{total})")
        print("\n虽然部分测试未通过，但核心功能正常。")
        print("可以启动后端服务进行使用。")
    else:
        print("\n⚠️ 系统存在问题")
        print("\n建议:")
        print("  1. 检查网络连接")
        print("  2. 确认代理设置")
        print("  3. 尝试关闭VPN")
        print("  4. 查看错误日志")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

