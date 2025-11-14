#!/usr/bin/env python3
"""
测试性能优化
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI, Order, Position
from trading_engine.matching_engine import MatchingEngine
from trading_engine.order_manager import OrderManager
from rules.trading_rules import TradingRules
from portfolio.portfolio_manager import PortfolioManager
from data_service.akshare_client import AKShareClient

def test_market_data_performance():
    """测试市场数据获取性能"""
    print("\n1. 测试市场数据获取性能...")

    akshare_client = AKShareClient()
    stock_codes = ["000063", "300750", "600703", "002594", "688256", "600276"]

    # 测试单次获取
    start_time = time.time()
    quotes = akshare_client.get_realtime_quotes(stock_codes)
    single_duration = time.time() - start_time

    print(f"   单次获取 {len(stock_codes)} 只股票: {single_duration:.2f}秒")

    # 测试批量获取性能
    iterations = 5
    start_time = time.time()
    for i in range(iterations):
        quotes = akshare_client.get_realtime_quotes(stock_codes)
    batch_duration = time.time() - start_time

    avg_batch_time = batch_duration / iterations
    print(f"   批量获取 {iterations} 次平均: {avg_batch_time:.2f}秒/次")

    # 性能标准
    if single_duration < 2.0:
        print("   ✅ 市场数据获取性能良好")
    else:
        print("   ⚠️  市场数据获取较慢")

    return single_duration, avg_batch_time

def test_database_performance():
    """测试数据库操作性能"""
    print("\n2. 测试数据库操作性能...")

    with get_db_session() as db:
        ai = db.query(AI).first()
        if not ai:
            print("   ❌ 数据库中没有AI")
            return

        ai_id = ai.id

        # 测试订单创建性能
        order_count = 10
        start_time = time.time()

        for i in range(order_count):
            order = Order(
                ai_id=ai_id,
                stock_code="000063",
                stock_name="中兴通讯",
                direction="buy",
                order_type="market",
                quantity=100,
                price=0.0,
                status="pending"
            )
            db.add(order)

        db.commit()
        order_create_duration = time.time() - start_time

        print(f"   创建 {order_count} 个订单: {order_create_duration:.2f}秒")
        print(f"   平均创建时间: {order_create_duration/order_count*1000:.1f}ms/个")

        # 测试订单查询性能
        start_time = time.time()
        orders = db.query(Order).filter(Order.ai_id == ai_id).limit(100).all()
        query_duration = time.time() - start_time

        print(f"   查询 {len(orders)} 个订单: {query_duration:.3f}秒")

        # 清理测试数据
        for order in orders:
            if order.status == "pending":  # 只删除测试订单
                db.delete(order)
        db.commit()

        # 性能标准
        if order_create_duration < 1.0 and query_duration < 0.1:
            print("   ✅ 数据库操作性能良好")
        else:
            print("   ⚠️  数据库操作性能需优化")

        return order_create_duration, query_duration

def test_matching_engine_performance():
    """测试撮合引擎性能"""
    print("\n3. 测试撮合引擎性能...")

    with get_db_session() as db:
        # 初始化组件
        trading_rules = TradingRules()
        portfolio_manager = PortfolioManager(db, trading_rules)
        akshare_client = AKShareClient()
        matching_engine = MatchingEngine(db, trading_rules, portfolio_manager, akshare_client)
        order_manager = OrderManager(db, trading_rules)

        ai = db.query(AI).first()
        if not ai:
            print("   ❌ 数据库中没有AI")
            return

        ai_id = ai.id

        # 创建测试订单
        test_orders = []
        for i in range(5):
            order = Order(
                ai_id=ai_id,
                stock_code="000063",
                stock_name="中兴通讯",
                direction="buy" if i % 2 == 0 else "sell",
                order_type="market",
                quantity=100,
                price=0.0,
                status="pending"
            )
            db.add(order)
            test_orders.append(order)

        db.commit()

        # 测试撮合性能
        start_time = time.time()
        matched_count = 0

        for order in test_orders:
            success, message = matching_engine.match_order(order)
            if success:
                matched_count += 1

        matching_duration = time.time() - start_time

        print(f"   撮合 {len(test_orders)} 个订单: {matching_duration:.2f}秒")
        print(f"   成功撮合: {matched_count}/{len(test_orders)}")
        print(f"   平均撮合时间: {matching_duration/len(test_orders)*1000:.1f}ms/个")

        # 清理测试订单
        for order in test_orders:
            db.delete(order)
        db.commit()

        # 性能标准
        if matching_duration < 5.0:
            print("   ✅ 撮合引擎性能良好")
        else:
            print("   ⚠️  撮合引擎性能需优化")

        return matching_duration

def test_concurrent_performance():
    """测试并发性能"""
    print("\n4. 测试并发性能...")

    def worker_thread(thread_id, results):
        """工作线程"""
        try:
            with get_db_session() as db:
                # 初始化组件
                trading_rules = TradingRules()
                portfolio_manager = PortfolioManager(db, trading_rules)
                akshare_client = AKShareClient()
                matching_engine = MatchingEngine(db, trading_rules, portfolio_manager, akshare_client)

                ai = db.query(AI).first()
                if not ai:
                    results[thread_id] = "No AI found"
                    return

                ai_id = ai.id

                # 创建和撮合订单
                start_time = time.time()

                order = Order(
                    ai_id=ai_id,
                    stock_code="000063",
                    stock_name="中兴通讯",
                    direction="buy",
                    order_type="market",
                    quantity=10,  # 小量订单避免资金不足
                    price=0.0,
                    status="pending"
                )
                db.add(order)
                db.commit()

                success, message = matching_engine.match_order(order)
                duration = time.time() - start_time

                results[thread_id] = {
                    'success': success,
                    'duration': duration,
                    'message': message
                }

                # 清理
                db.delete(order)
                db.commit()

        except Exception as e:
            results[thread_id] = f"Error: {str(e)}"

    # 启动并发测试
    thread_count = 3
    threads = []
    results = {}

    start_time = time.time()

    for i in range(thread_count):
        thread = threading.Thread(target=worker_thread, args=(i, results))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    total_duration = time.time() - start_time

    # 分析结果
    success_count = sum(1 for r in results.values() if isinstance(r, dict) and r['success'])
    error_count = sum(1 for r in results.values() if isinstance(r, str) or not r['success'])

    print(f"   并发线程数: {thread_count}")
    print(f"   总耗时: {total_duration:.2f}秒")
    print(f"   成功交易: {success_count}")
    print(f"   失败/错误: {error_count}")

    for i, result in results.items():
        if isinstance(result, dict):
            print(f"   线程{i}: {'成功' if result['success'] else '失败'} "
                  f"({result['duration']:.2f}秒)")
        else:
            print(f"   线程{i}: {result}")

    # 性能标准
    if total_duration < 10.0 and success_count >= thread_count * 0.8:
        print("   ✅ 并发性能良好")
    else:
        print("   ⚠️  并发性能需优化")

    return total_duration, success_count, error_count

def test_performance():
    """测试系统性能"""
    print("=" * 60)
    print("  测试性能优化")
    print("=" * 60)

    try:
        # 1. 市场数据性能
        market_single, market_batch = test_market_data_performance()

        # 2. 数据库性能
        db_create, db_query = test_database_performance()

        # 3. 撮合引擎性能
        matching_time = test_matching_engine_performance()

        # 4. 并发性能
        concurrent_time, concurrent_success, concurrent_errors = test_concurrent_performance()

        # 5. 总体评估
        print("\n" + "=" * 60)
        print("  性能测试结果总结")
        print("=" * 60)

        print("市场数据获取:")
        print(".2f")
        print(".2f")
        print("数据库操作:")
        print(".2f")
        print(".3f")
        print("撮合引擎:")
        print(".2f")
        print("并发性能:")
        print(".2f")
        print(f"   成功率: {concurrent_success}/{concurrent_success + concurrent_errors}")

        # 给出优化建议
        suggestions = []

        if market_single > 2.0:
            suggestions.append("• 优化市场数据获取速度，可考虑缓存或异步获取")
        if db_create > 1.0:
            suggestions.append("• 优化数据库写入性能，可考虑批量操作或索引优化")
        if db_query > 0.1:
            suggestions.append("• 优化数据库查询性能，可添加适当索引")
        if matching_time > 5.0:
            suggestions.append("• 优化撮合引擎性能，可考虑异步处理或算法优化")
        if concurrent_time > 10.0 or concurrent_success < 2:
            suggestions.append("• 优化并发性能，可考虑连接池或锁优化")

        if suggestions:
            print("\n优化建议:")
            for suggestion in suggestions:
                print(suggestion)
        else:
            print("\n🎉 系统性能表现优秀！")

        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 性能测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_performance()
