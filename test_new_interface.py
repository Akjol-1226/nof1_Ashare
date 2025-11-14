#!/usr/bin/env python3
"""
测试新的 stock_bid_ask_em 接口
这个接口单独查询每只股票，可能更稳定
"""

# 首先导入禁用代理的模块
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import disable_proxy
except:
    print("⚠️  未能加载代理禁用模块")

import akshare as ak
import time
from datetime import datetime
import pandas as pd

# 6只可交易股票
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

def test_single_stock(code, name):
    """
    测试单个股票的行情报价接口
    
    Args:
        code: 股票代码
        name: 股票名称
        
    Returns:
        (是否成功, 股票数据字典)
    """
    try:
        print(f"正在获取 {code} {name} 的行情...")
        
        start_time = time.time()
        df = ak.stock_bid_ask_em(symbol=code)
        elapsed = time.time() - start_time
        
        # 解析数据
        data = {}
        for _, row in df.iterrows():
            data[row['item']] = row['value']
        
        print(f"✅ 成功！响应时间: {elapsed:.2f}秒")
        print(f"   最新价: ¥{data.get('最新', 0):.2f}")
        print(f"   涨跌幅: {data.get('涨幅', 0):.2f}%")
        print(f"   成交量: {data.get('总手', 0):.0f}手")
        print(f"   成交额: ¥{data.get('金额', 0)/100000000:.2f}亿")
        print(f"   今开: ¥{data.get('今开', 0):.2f}")
        print(f"   最高: ¥{data.get('最高', 0):.2f}")
        print(f"   最低: ¥{data.get('最低', 0):.2f}")
        print(f"   昨收: ¥{data.get('昨收', 0):.2f}")
        print()
        
        return True, data
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}\n")
        return False, {}

def test_all_stocks():
    """测试所有6只股票"""
    print_section("测试所有6只可交易股票")
    
    results = []
    all_data = {}
    
    for code, name in TRADING_STOCKS.items():
        success, data = test_single_stock(code, name)
        results.append((code, name, success))
        if success:
            all_data[code] = data
        time.sleep(0.5)  # 避免请求过快
    
    return results, all_data

def test_batch_speed():
    """测试批量获取的速度"""
    print_section("测试批量获取速度")
    
    print("连续获取6只股票...")
    start_time = time.time()
    
    success_count = 0
    for code, name in TRADING_STOCKS.items():
        try:
            df = ak.stock_bid_ask_em(symbol=code)
            success_count += 1
        except:
            pass
    
    elapsed = time.time() - start_time
    
    print(f"\n总耗时: {elapsed:.2f}秒")
    print(f"成功: {success_count}/6")
    print(f"平均每只: {elapsed/6:.2f}秒")
    
    if success_count == 6:
        print(f"\n✅ 满足10秒轮询要求！" if elapsed < 10 else "⚠️  超过10秒，可能需要优化")

def compare_interfaces():
    """对比不同接口"""
    print_section("接口对比")
    
    print("方法1: stock_bid_ask_em (单个查询)")
    print("  优点: ✓ 数据量小，速度快")
    print("       ✓ 可以逐个查询，失败不影响其他")
    print("       ✓ 包含买卖盘口数据")
    print("  缺点: ✗ 需要循环查询多只股票")
    
    print("\n方法2: stock_zh_a_spot_em (全市场)")
    print("  优点: ✓ 一次获取所有股票")
    print("  缺点: ✗ 数据量大（5000+只股票）")
    print("       ✗ 容易触发限制或代理问题")
    
    print("\n方法3: 历史数据 (stock_zh_a_hist)")
    print("  优点: ✓ 最稳定可靠")
    print("  缺点: ✗ 不是实时数据")
    
    print("\n💡 推荐策略:")
    print("  1. 优先使用 stock_bid_ask_em（单个查询）")
    print("  2. 失败时回退到历史数据")
    print("  3. 组合使用保证系统稳定性")

def generate_new_client():
    """生成使用新接口的客户端代码"""
    print_section("生成新的数据客户端代码")
    
    code = '''"""
使用stock_bid_ask_em接口的AKShare客户端
"""

import akshare as ak
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class AKShareClientV2:
    """使用单股票查询接口的客户端"""
    
    def __init__(self, stock_codes: List[str]):
        """
        Args:
            stock_codes: 股票代码列表
        """
        self.stock_codes = stock_codes
        
    def get_realtime_quotes(self) -> List[Dict]:
        """获取所有股票的实时行情"""
        quotes = []
        
        for code in self.stock_codes:
            try:
                df = ak.stock_bid_ask_em(symbol=code)
                data = {}
                for _, row in df.iterrows():
                    data[row['item']] = row['value']
                
                # 转换为统一格式
                quote = {
                    'code': code,
                    'price': data.get('最新', 0),
                    'change_percent': data.get('涨幅', 0),
                    'volume': data.get('总手', 0),
                    'amount': data.get('金额', 0),
                    'high': data.get('最高', 0),
                    'low': data.get('最低', 0),
                    'open': data.get('今开', 0),
                    'close_yesterday': data.get('昨收', 0)
                }
                quotes.append(quote)
                
            except Exception as e:
                logger.error(f"Failed to get quote for {code}: {e}")
                
        return quotes
'''
    
    with open('akshare_client_v2.py', 'w', encoding='utf-8') as f:
        f.write(code)
    
    print("✅ 已生成新客户端代码: akshare_client_v2.py")
    print("\n使用方法:")
    print("  from akshare_client_v2 import AKShareClientV2")
    print("  client = AKShareClientV2(['000063', '300750', ...])")
    print("  quotes = client.get_realtime_quotes()")

def main():
    """主函数"""
    print(f"\n{'#'*80}")
    print(f"#  测试 stock_bid_ask_em 接口")
    print(f"#  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    print("\n📝 说明:")
    print("  这个接口通过单独查询每只股票来获取行情")
    print("  避免了全市场查询的网络问题")
    
    # 测试所有股票
    results, all_data = test_all_stocks()
    
    # 测试速度
    if any(r[2] for r in results):  # 如果有成功的
        test_batch_speed()
    
    # 对比接口
    compare_interfaces()
    
    # 生成新代码
    generate_new_client()
    
    # 总结
    print_section("测试总结")
    
    success_count = sum(1 for r in results if r[2])
    total = len(results)
    
    print(f"测试结果: {success_count}/{total} 成功\n")
    
    for code, name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {code} {name}")
    
    print("\n" + "="*80)
    
    if success_count == total:
        print("\n🎉 完美！所有股票都能正常获取数据！")
        print("   建议立即切换到这个接口。")
    elif success_count > 0:
        print(f"\n✅ 部分成功 ({success_count}/{total})")
        print("   可以使用这个接口，失败的股票使用历史数据兜底。")
    else:
        print("\n⚠️  所有请求都失败了")
        print("   建议检查:")
        print("   1. 网络连接")
        print("   2. 防火墙设置")
        print("   3. 是否需要关闭VPN/代理")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

