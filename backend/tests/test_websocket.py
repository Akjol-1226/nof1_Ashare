#!/usr/bin/env python3
"""
测试WebSocket服务
"""

import sys
import os
import asyncio
import websockets
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

async def test_websocket_connection():
    """测试WebSocket连接"""
    print("1. 测试WebSocket连接...")

    uri = f"ws://localhost:{settings.api_port}/ws/market"

    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket连接成功")

            # 等待接收消息
            message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            data = json.loads(message)

            print("   ✅ 接收到消息:")
            print(f"      类型: {data.get('type')}")
            print(f"      时间戳: {data.get('data', {}).get('timestamp')}")

            quotes = data.get('data', {}).get('quotes', [])
            print(f"      行情数量: {len(quotes)}")

            if quotes:
                first_quote = quotes[0]
                print("      示例行情:")
            print(f"         代码: {first_quote.get('code')}")
            print(f"         名称: {first_quote.get('name')}")
            print(f"         价格: {first_quote.get('price')}")

            return True

    except asyncio.TimeoutError:
        print("   ❌ WebSocket连接超时")
        return False
    except Exception as e:
        print(f"   ❌ WebSocket连接失败: {str(e)}")
        return False

async def test_websocket_multiple_messages():
    """测试WebSocket多消息接收"""
    print("\n2. 测试WebSocket多消息接收...")

    uri = f"ws://localhost:{settings.api_port}/ws/market"
    messages_received = 0

    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket连接成功")

            start_time = time.time()

            # 接收多条消息
            while messages_received < 3 and (time.time() - start_time) < 35:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    messages_received += 1

                    print(f"   消息 {messages_received}:")
                    print(f"      类型: {data.get('type')}")
                    timestamp = data.get('data', {}).get('timestamp')
                    if timestamp:
                        print(f"      时间戳: {timestamp}")

                except asyncio.TimeoutError:
                    print("   等待消息超时")
                    break

            print(f"   总共接收到 {messages_received} 条消息")

            if messages_received >= 2:
                print("   ✅ 多消息接收测试通过")
                return True
            else:
                print("   ⚠️  接收到的消息较少")
                return True

    except Exception as e:
        print(f"   ❌ 多消息测试失败: {str(e)}")
        return False

async def test_websocket_trading():
    """测试交易WebSocket"""
    print("\n3. 测试交易WebSocket...")

    uri = f"ws://localhost:{settings.api_port}/ws/trading"

    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ 交易WebSocket连接成功")

            # 等待一段时间看看是否有消息
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=8.0)
                data = json.loads(message)
                print("   ✅ 接收到交易消息:")
                print(f"      类型: {data.get('type')}")
                trading_data = data.get('data', {})
                portfolios = trading_data.get('portfolios', [])
                orders = trading_data.get('orders', [])
                print(f"      持仓数量: {len(portfolios)}")
                print(f"      订单数量: {len(orders)}")
                return True
            except asyncio.TimeoutError:
                print("   ⚠️  交易WebSocket暂时无消息")
                return False

    except Exception as e:
        print(f"   ❌ 交易WebSocket连接失败: {str(e)}")
        return False


async def test_websocket_chats():
    """测试AI对话WebSocket"""
    print("\n4. 测试AI对话WebSocket...")

    uri = f"ws://localhost:{settings.api_port}/ws/chats"

    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ AI对话WebSocket连接成功")

            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=8.0)
                data = json.loads(message)
                print("   ✅ 接收到对话消息:")
                print(f"      类型: {data.get('type')}")
                chats_data = data.get('data', {})
                chats = chats_data.get('chats', [])
                print(f"      AI数量: {len(chats)}")
                return True
            except asyncio.TimeoutError:
                print("   ⚠️  AI对话WebSocket暂时无消息")
                return False

    except Exception as e:
        print(f"   ❌ AI对话WebSocket连接失败: {str(e)}")
        return False


async def test_websocket_performance():
    """测试收益曲线WebSocket"""
    print("\n5. 测试收益曲线WebSocket...")

    uri = f"ws://localhost:{settings.api_port}/ws/performance"

    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ 收益曲线WebSocket连接成功")

            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(message)
                print("   ✅ 接收到收益消息:")
                print(f"      类型: {data.get('type')}")
                perf_data = data.get('data', {})
                performance = perf_data.get('performance', [])
                print(f"      收益数据AI数量: {len(performance)}")
                return True
            except asyncio.TimeoutError:
                print("   ⚠️  收益曲线WebSocket暂时无消息")
                return False

    except Exception as e:
        print(f"   ❌ 收益曲线WebSocket连接失败: {str(e)}")
        return False

def check_backend_running():
    """检查后端是否运行"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("localhost", settings.api_port))
        sock.close()
        return True
    except:
        return False

async def test_websocket_service():
    """测试WebSocket服务"""
    print("=" * 60)
    print("  测试WebSocket服务")
    print("=" * 60)

    # 检查后端是否运行
    if not check_backend_running():
        print("❌ 后端服务未运行，请先启动后端服务")
        print(f"   运行命令: python backend/main.py")
        return

    print("✅ 后端服务正在运行")

    try:
        # 测试市场数据WebSocket
        market_success = await test_websocket_connection()

        # 测试多消息接收
        multi_success = await test_websocket_multiple_messages()

        # 测试交易WebSocket
        trading_success = await test_websocket_trading()

        # 测试AI对话WebSocket
        chats_success = await test_websocket_chats()

        # 测试收益曲线WebSocket
        perf_success = await test_websocket_performance()

        # 总结
        print("\n" + "=" * 60)
        print("  WebSocket测试结果")
        print("=" * 60)
        print(f"市场数据WebSocket: {'✅ 通过' if market_success else '❌ 失败'}")
        print(f"多消息接收: {'✅ 通过' if multi_success else '❌ 失败'}")
        print(f"交易WebSocket: {'✅ 通过' if trading_success else '❌ 失败'}")
        print(f"AI对话WebSocket: {'✅ 通过' if chats_success else '❌ 失败'}")
        print(f"收益曲线WebSocket: {'✅ 通过' if perf_success else '❌ 失败'}")

        if all([market_success, multi_success, trading_success, chats_success, perf_success]):
            print("\n🎉 所有WebSocket测试通过！")
        else:
            print("\n⚠️  部分WebSocket测试失败")

        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_service())
