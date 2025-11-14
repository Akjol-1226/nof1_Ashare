#!/usr/bin/env python3
"""
测试异常场景处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI, Order, Position
from trading_engine.matching_engine import MatchingEngine
from trading_engine.order_manager import OrderManager
from rules.trading_rules import TradingRules
from portfolio.portfolio_manager import PortfolioManager
from data_service.akshare_client import AKShareClient

def test_exception_handling():
    """测试异常场景处理"""
    print("=" * 60)
    print("  测试异常场景处理")
    print("=" * 60)

    with get_db_session() as db:
        # 1. 初始化组件
        print("\n1. 初始化组件...")
        trading_rules = TradingRules()
        akshare_client = AKShareClient()
        portfolio_manager = PortfolioManager(db, trading_rules)
        matching_engine = MatchingEngine(db, trading_rules, portfolio_manager, akshare_client)
        order_manager = OrderManager(db, trading_rules)
        print("✅ 组件初始化完成")

        # 2. 创建测试AI（如果不存在）
        ai = db.query(AI).first()
        if not ai:
            print("\n❌ 需要先创建AI")
            return
        ai_id = ai.id

        # 3. 测试无效订单撮合
        print("\n2. 测试无效订单撮合...")

        # 创建无效的订单（不存在的股票）
        invalid_order = Order(
            ai_id=ai_id,
            stock_code="999999",  # 不存在的股票代码
            stock_name="不存在的股票",
            direction="buy",
            order_type="market",
            quantity=100,
            price=0.0,
            status="pending"
        )
        db.add(invalid_order)
        db.commit()

        print(f"   测试无效股票代码: {invalid_order.stock_code}")

        success, message = matching_engine.match_order(invalid_order)
        if not success and "Failed to get stock info" in message:
            print("   ✅ 正确处理了无效股票代码")
        else:
            print(f"   ❌ 未正确处理无效股票代码: {message}")

        # 删除测试订单
        db.delete(invalid_order)
        db.commit()

        # 4. 测试资金不足
        print("\n3. 测试资金不足场景...")

        # 创建一个高价订单
        expensive_order = Order(
            ai_id=ai_id,
            stock_code="000063",
            stock_name="中兴通讯",
            direction="buy",
            order_type="limit",
            quantity=10000,  # 大量买入
            price=1000.0,    # 高价
            status="pending"
        )
        db.add(expensive_order)
        db.commit()

        print(f"   测试高价订单: {expensive_order.quantity}股 @ ¥{expensive_order.price:.2f}")

        success, message = matching_engine.match_order(expensive_order)
        if not success and "Insufficient cash" in message:
            print("   ✅ 正确处理了资金不足")
        else:
            print(f"   ❌ 未正确处理资金不足: {message}")

        # 删除测试订单
        db.delete(expensive_order)
        db.commit()

        # 5. 测试持仓不足（卖出）
        print("\n4. 测试持仓不足场景...")

        # 创建卖出订单（但没有持仓）
        sell_order = Order(
            ai_id=ai_id,
            stock_code="600000",  # 未持有的股票
            stock_name="浦发银行",
            direction="sell",
            order_type="market",
            quantity=100,
            price=0.0,
            status="pending"
        )
        db.add(sell_order)
        db.commit()

        print(f"   测试无持仓卖出: {sell_order.stock_code} {sell_order.quantity}股")

        success, message = matching_engine.match_order(sell_order)
        if not success and "Insufficient sellable quantity" in message:
            print("   ✅ 正确处理了持仓不足")
        else:
            print(f"   ❌ 未正确处理持仓不足: {message}")

        # 删除测试订单
        db.delete(sell_order)
        db.commit()

        # 6. 测试涨跌停限制
        print("\n5. 测试涨跌停限制...")

        # 获取当前价格信息
        stock_info = akshare_client.get_stock_info("000063")
        if stock_info:
            yesterday_close = stock_info['close_yesterday']

            # 计算涨停价和跌停价（与trading_rules保持一致）
            upper_limit = round(yesterday_close * 1.1, 2)  # 10%涨停
            lower_limit = round(yesterday_close * 0.9, 2)  # 10%跌停

            print(f"   昨日收盘: ¥{yesterday_close:.2f}")
            print(f"   涨停价: ¥{upper_limit:.2f}, 跌停价: ¥{lower_limit:.2f}")

            # 测试买入涨停价
            limit_buy_order = Order(
                ai_id=ai_id,
                stock_code="000063",
                stock_name="中兴通讯",
                direction="buy",
                order_type="limit",
                quantity=100,
                price=upper_limit,  # 涨停价买入
                status="pending"
            )
            db.add(limit_buy_order)
            db.commit()

            success, message = matching_engine.match_order(limit_buy_order)
            if not success and "at upper limit" in message:
                print("   ✅ 正确阻止了涨停价买入")
            else:
                print(f"   ❌ 涨停价买入处理结果: {message}")

            db.delete(limit_buy_order)
            db.commit()

        # 7. 测试订单状态检查
        print("\n6. 测试订单状态检查...")

        # 创建已完成的订单
        completed_order = Order(
            ai_id=ai_id,
            stock_code="000063",
            stock_name="中兴通讯",
            direction="buy",
            order_type="market",
            quantity=100,
            price=0.0,
            status="filled"  # 已完成状态
        )
        db.add(completed_order)
        db.commit()

        success, message = matching_engine.match_order(completed_order)
        if not success and "not pending" in message:
            print("   ✅ 正确拒绝了非pending状态订单")
        else:
            print(f"   ❌ 非pending状态订单处理结果: {message}")

        db.delete(completed_order)
        db.commit()

        # 8. 测试网络异常模拟
        print("\n7. 测试网络异常处理...")

        # 禁用网络连接（通过修改AKShare客户端）
        original_get_stock_info = akshare_client.get_stock_info
        akshare_client.get_stock_info = lambda code: None  # 模拟网络失败

        network_test_order = Order(
            ai_id=ai_id,
            stock_code="000063",
            stock_name="中兴通讯",
            direction="buy",
            order_type="market",
            quantity=10,
            price=0.0,
            status="pending"
        )
        db.add(network_test_order)
        db.commit()

        success, message = matching_engine.match_order(network_test_order)
        if not success and "Failed to get stock info" in message:
            print("   ✅ 正确处理了网络异常")
        else:
            print(f"   ❌ 网络异常处理结果: {message}")

        # 恢复网络连接
        akshare_client.get_stock_info = original_get_stock_info

        db.delete(network_test_order)
        db.commit()

        # 9. 测试批量异常处理
        print("\n8. 测试批量异常处理...")

        # 创建多个异常订单
        exception_orders = [
            Order(ai_id=ai_id, stock_code="999999", stock_name="无效股票", direction="buy",
                  order_type="market", quantity=100, price=0.0, status="pending"),
            Order(ai_id=ai_id, stock_code="000063", stock_name="中兴通讯", direction="sell",
                  order_type="market", quantity=10000, price=0.0, status="pending"),  # 无持仓卖出
        ]

        for order in exception_orders:
            db.add(order)
        db.commit()

        processed_count = 0
        failed_count = 0

        for order in exception_orders:
            success, message = matching_engine.match_order(order)
            if success:
                processed_count += 1
            else:
                failed_count += 1

        print(f"   批量处理结果: {processed_count}成功, {failed_count}失败")

        # 清理
        for order in exception_orders:
            db.delete(order)
        db.commit()

        print("\n" + "=" * 60)
        print("  异常场景处理测试完成！")
        print("  验证了以下异常处理:")
        print("  • 无效股票代码")
        print("  • 资金不足")
        print("  • 持仓不足")
        print("  • 涨跌停限制")
        print("  • 订单状态检查")
        print("  • 网络异常")
        print("  • 批量异常处理")
        print("=" * 60)

if __name__ == "__main__":
    try:
        test_exception_handling()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
