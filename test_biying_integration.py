#!/usr/bin/env python3
"""
测试 Biying 接口集成
验证实时行情和五档盘口接口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.data_service.akshare_client import AKShareClient
from backend.config import settings

def test_biying_integration():
    """测试 Biying 接口集成"""
    
    print("=" * 60)
    print("  测试 Biying 接口集成")
    print("=" * 60)
    
    # 检查配置
    print(f"\n1. 检查配置:")
    print(f"   Biying Base URL: {settings.biying_base_url}")
    print(f"   Biying License: {'已配置' if settings.biying_license else '❌ 未配置'}")
    
    if not settings.biying_license:
        print("\n⚠️  请在 .env 文件中设置 BIYING_LICENSE")
        print("   示例: BIYING_LICENSE=your-license-key-here")
        return
    
    # 初始化客户端
    print(f"\n2. 初始化 AKShareClient...")
    client = AKShareClient()
    print("   ✅ 客户端初始化成功")
    
    # 测试实时行情（多股接口）
    print(f"\n3. 测试实时行情（多股接口）...")
    test_codes = ["000001", "600019"]
    print(f"   查询股票: {', '.join(test_codes)}")
    
    try:
        quotes = client.get_realtime_quotes(test_codes)
        
        if quotes:
            print(f"   ✅ 成功获取 {len(quotes)} 只股票的行情:")
            for q in quotes:
                print(f"\n   股票: {q.code} - {q.name}")
                print(f"     最新价: {q.price}")
                print(f"     涨跌幅: {q.change_percent}%")
                print(f"     昨收: {q.close_yesterday}")
                print(f"     成交量: {q.volume}")
                print(f"     成交额: {q.amount}")
        else:
            print("   ❌ 未获取到行情数据")
            
    except Exception as e:
        print(f"   ❌ 获取行情失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试五档盘口
    print(f"\n4. 测试五档盘口...")
    test_code = "000001"
    print(f"   查询股票: {test_code}")
    
    try:
        order_book = client.get_order_book(test_code)
        
        if order_book:
            print(f"   ✅ 成功获取五档盘口:")
            print(f"     卖五到卖一: {order_book.get('ask_prices', [])}")
            print(f"     卖盘量: {order_book.get('ask_volumes', [])}")
            print(f"     买一到买五: {order_book.get('bid_prices', [])}")
            print(f"     买盘量: {order_book.get('bid_volumes', [])}")
            print(f"     时间: {order_book.get('timestamp', '')}")
        else:
            print("   ❌ 未获取到五档盘口数据")
            
    except Exception as e:
        print(f"   ❌ 获取五档盘口失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试单股信息（用于撮合）
    print(f"\n5. 测试单股信息（撮合引擎使用）...")
    try:
        stock_info = client.get_stock_info("000001")
        
        if stock_info:
            print(f"   ✅ 成功获取股票信息:")
            print(f"     代码: {stock_info['code']}")
            print(f"     名称: {stock_info['name']}")
            print(f"     最新价: {stock_info['price']}")
            print(f"     昨收: {stock_info['close_yesterday']}")
        else:
            print("   ❌ 未获取到股票信息")
            
    except Exception as e:
        print(f"   ❌ 获取股票信息失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("  测试完成！")
    print("  如果所有测试通过，说明 Biying 接口已成功集成")
    print("  现在可以启动系统，撮合引擎将使用 Biying 数据")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_biying_integration()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

