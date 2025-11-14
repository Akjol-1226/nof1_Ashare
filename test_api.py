#!/usr/bin/env python3
"""
API测试脚本
用于测试后端API功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8888"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """测试健康检查"""
    print_section("1. 健康检查")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

def test_register_ai():
    """测试注册AI"""
    print_section("2. 注册AI")
    
    # 注册三个测试AI
    ais = [
        {
            "name": "GPT-4 Trader",
            "model_name": "gpt-4",
            "initial_cash": 100000.0
        },
        {
            "name": "Claude Trader",
            "model_name": "claude-3-sonnet",
            "initial_cash": 100000.0
        },
        {
            "name": "DeepSeek Trader",
            "model_name": "deepseek-chat",
            "initial_cash": 100000.0
        }
    ]
    
    for ai_data in ais:
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai/register",
                json=ai_data
            )
            
            if response.status_code == 200:
                ai = response.json()
                print(f"✅ Registered: {ai['name']} (ID: {ai['id']})")
            else:
                print(f"⚠️  Failed to register {ai_data['name']}: {response.status_code}")
                if response.status_code == 400:
                    print(f"   (AI may already exist)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    return True

def test_get_ai_list():
    """测试获取AI列表"""
    print_section("3. 获取AI列表")
    
    response = requests.get(f"{BASE_URL}/api/ai/list")
    ais = response.json()
    
    print(f"Total AIs: {len(ais)}")
    for ai in ais:
        print(f"- {ai['name']}: ¥{ai['total_assets']:.2f}")
    
    return len(ais) > 0

def test_get_ranking():
    """测试获取排行榜"""
    print_section("4. 获取排行榜")
    
    response = requests.get(f"{BASE_URL}/api/ai/ranking")
    rankings = response.json()
    
    print(f"{'Rank':<6} {'Name':<20} {'Assets':<15} {'Return':<10}")
    print("-" * 60)
    for ranking in rankings:
        print(f"{ranking['rank']:<6} {ranking['ai_name']:<20} "
              f"¥{ranking['total_assets']:<14.2f} {ranking['return_rate']:>6.2f}%")
    
    return True

def test_get_system_status():
    """测试获取系统状态"""
    print_section("5. 系统状态")
    
    response = requests.get(f"{BASE_URL}/api/system/status")
    status = response.json()
    
    print(f"Is Running: {status['is_running']}")
    print(f"Trading Time: {status['trading_time']}")
    print(f"Total AIs: {status['total_ais']}")
    print(f"Active AIs: {status['active_ais']}")
    
    return True

def test_get_market_quotes():
    """测试获取市场行情"""
    print_section("6. 市场行情")
    
    try:
        response = requests.get(f"{BASE_URL}/api/market/quotes?limit=10")
        data = response.json()
        
        print(f"Timestamp: {data['timestamp']}")
        print(f"\n{'Code':<10} {'Name':<10} {'Price':<10} {'Change':<10}")
        print("-" * 50)
        
        for quote in data['quotes'][:10]:
            change_str = f"{quote['change_percent']:+.2f}%"
            print(f"{quote['code']:<10} {quote['name']:<10} "
                  f"¥{quote['price']:<9.2f} {change_str:<10}")
        
        return True
    except Exception as e:
        print(f"⚠️  Market data unavailable: {str(e)}")
        return False

def main():
    """主函数"""
    print(f"\n{'#'*60}")
    print(f"#  nof1.AShare API测试")
    print(f"#  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    tests = [
        ("健康检查", test_health_check),
        ("注册AI", test_register_ai),
        ("获取AI列表", test_get_ai_list),
        ("获取排行榜", test_get_ranking),
        ("系统状态", test_get_system_status),
        ("市场行情", test_get_market_quotes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            results.append((name, False))
    
    # 总结
    print_section("测试总结")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    print()
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print("\n" + "="*60 + "\n")
    
    if passed == total:
        print("✅ 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查后端服务。")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务 (http://localhost:8000)")
        print("   请确保后端服务已启动: cd backend && python main.py")
    except KeyboardInterrupt:
        print("\n\n测试被中断")


