#!/usr/bin/env python3
"""
测试AKShare的各种实时行情接口
找出最稳定可用的接口
"""

import akshare as ak
import time
from datetime import datetime

# 6只可交易股票及其市场分类
STOCKS_BY_MARKET = {
    '沪A股': {
        '600703': '三安光电',
        '600276': '恒瑞医药'
    },
    '深A股': {
        '000063': '中兴通讯',
        '002594': '比亚迪',
        '300750': '宁德时代'
    },
    '科创板': {
        '688256': '寒武纪'
    }
}

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_interface(interface_func, name, codes_to_check):
    """
    测试单个接口
    
    Args:
        interface_func: AKShare接口函数
        name: 接口名称
        codes_to_check: 要检查的股票代码列表
    
    Returns:
        (是否成功, 响应时间, 找到的股票数据)
    """
    print(f"测试接口: {name}")
    print("-" * 80)
    
    try:
        start_time = time.time()
        df = interface_func()
        elapsed = time.time() - start_time
        
        print(f"✅ 成功获取数据")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")
        print(f"📊 总股票数: {len(df)}")
        print(f"📋 数据列: {list(df.columns)[:8]}...")  # 只显示前8列
        
        # 检查我们关心的股票是否在结果中
        found_stocks = {}
        for code in codes_to_check:
            stock_data = df[df['代码'] == code]
            if not stock_data.empty:
                stock = stock_data.iloc[0]
                found_stocks[code] = {
                    'name': stock.get('名称', 'N/A'),
                    'price': stock.get('最新价', 0),
                    'change': stock.get('涨跌幅', 0)
                }
        
        print(f"\n找到的目标股票: {len(found_stocks)}/{len(codes_to_check)}")
        for code, info in found_stocks.items():
            print(f"  ✓ {code} {info['name']}: ¥{info['price']:.2f} ({info['change']:+.2f}%)")
        
        if not found_stocks:
            print("  ⚠️  未找到任何目标股票")
        
        print()
        return True, elapsed, found_stocks
        
    except Exception as e:
        print(f"❌ 失败: {str(e)}\n")
        return False, 0, {}

def main():
    """主函数"""
    print(f"\n{'#'*80}")
    print(f"#  AKShare 实时行情接口测试")
    print(f"#  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # 汇总所有需要检查的股票代码
    all_codes = []
    for market, stocks in STOCKS_BY_MARKET.items():
        all_codes.extend(stocks.keys())
    
    print(f"\n目标股票: {len(all_codes)} 只")
    for market, stocks in STOCKS_BY_MARKET.items():
        print(f"  {market}: {', '.join([f'{code}({name})' for code, name in stocks.items()])}")
    
    # 测试各个接口
    results = []
    
    # 1. 测试沪深京A股（全市场）
    print_section("接口1: stock_zh_a_spot_em() - 沪深京A股")
    success, elapsed, found = test_interface(
        ak.stock_zh_a_spot_em,
        "沪深京A股",
        all_codes
    )
    results.append(("沪深京A股 (stock_zh_a_spot_em)", success, elapsed, len(found)))
    
    # 2. 测试沪A股
    print_section("接口2: stock_sh_a_spot_em() - 沪A股")
    sh_codes = list(STOCKS_BY_MARKET['沪A股'].keys())
    success, elapsed, found = test_interface(
        ak.stock_sh_a_spot_em,
        "沪A股",
        sh_codes
    )
    results.append(("沪A股 (stock_sh_a_spot_em)", success, elapsed, len(found)))
    
    # 3. 测试深A股
    print_section("接口3: stock_sz_a_spot_em() - 深A股")
    sz_codes = list(STOCKS_BY_MARKET['深A股'].keys())
    success, elapsed, found = test_interface(
        ak.stock_sz_a_spot_em,
        "深A股",
        sz_codes
    )
    results.append(("深A股 (stock_sz_a_spot_em)", success, elapsed, len(found)))
    
    # 4. 测试科创板
    print_section("接口4: stock_kc_a_spot_em() - 科创板")
    kc_codes = list(STOCKS_BY_MARKET['科创板'].keys())
    success, elapsed, found = test_interface(
        ak.stock_kc_a_spot_em,
        "科创板",
        kc_codes
    )
    results.append(("科创板 (stock_kc_a_spot_em)", success, elapsed, len(found)))
    
    # 总结
    print_section("测试总结")
    
    print(f"{'接口名称':<40} {'状态':<10} {'响应时间':<12} {'找到股票':<10}")
    print("-" * 80)
    
    for name, success, elapsed, found_count in results:
        status = "✅ 成功" if success else "❌ 失败"
        time_str = f"{elapsed:.2f}s" if success else "N/A"
        found_str = str(found_count) if success else "N/A"
        print(f"{name:<40} {status:<10} {time_str:<12} {found_str:<10}")
    
    print("\n" + "="*80)
    
    # 给出建议
    successful = [r for r in results if r[1]]
    
    if not successful:
        print("\n⚠️  所有接口都失败了，可能的原因：")
        print("   1. 网络连接问题（建议检查网络）")
        print("   2. 代理设置问题（尝试关闭代理）")
        print("   3. AKShare版本问题（尝试升级：pip install -U akshare）")
        print("   4. 东方财富网API暂时不可用")
        print("\n💡 建议：")
        print("   - 使用历史数据接口（stock_zh_a_hist）")
        print("   - 在交易时间重试")
        print("   - 检查防火墙设置")
    else:
        fastest = min(successful, key=lambda x: x[2])
        print(f"\n✅ 推荐使用: {fastest[0]}")
        print(f"   原因: 响应最快 ({fastest[2]:.2f}秒)，找到 {fastest[3]} 只股票")
        
        if fastest[3] < len(all_codes):
            print(f"\n💡 提示: 该接口未找到所有股票，建议组合使用：")
            print("   - 沪A股接口 + 深A股接口 + 科创板接口")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

