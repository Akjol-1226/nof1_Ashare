#!/usr/bin/env python3
"""
测试撮合引擎
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI, Order, Transaction, Position
from trading_engine.matching_engine import MatchingEngine
from trading_engine.order_manager import OrderManager
from rules.trading_rules import TradingRules
from portfolio.portfolio_manager import PortfolioManager
from data_service.akshare_client import AKShareClient

def test_matching_engine():
    """测试撮合引擎"""
    print("=" * 60)
    print("  测试撮合引擎")
    print("=" * 60)

    # 1. 检查数据库
    print("\n1. 检查数据库...")
    with get_db_session() as db:
        ai = db.query(AI).first()
        if not ai:
            print("❌ 数据库中没有AI")
            return

        ai_id = ai.id
        ai_name = ai.name

        print(f"✅ 找到AI: {ai_name} (ID: {ai_id})")
        print(f"   当前现金: ¥{ai.current_cash:,.2f}")
        print(f"   总资产: ¥{ai.total_assets:,.2f}")

        # 2. 初始化组件
        print("\n2. 初始化撮合引擎...")
        trading_rules = TradingRules()
        portfolio_manager = PortfolioManager(db, trading_rules)
        akshare_client = AKShareClient()
        matching_engine = MatchingEngine(
            db, trading_rules, portfolio_manager, akshare_client
        )
        order_manager = OrderManager(db, trading_rules)

        print("✅ 组件初始化完成")

        # 3. 获取待撮合的订单
        print("\n3. 查找待撮合订单...")
        pending_orders = db.query(Order).filter(
            Order.ai_id == ai_id,
            Order.status == 'pending'
        ).limit(3).all()  # 最多测试3个订单

        if not pending_orders:
            print("❌ 没有待撮合的订单")
            print("请先运行订单生成测试")
            return

        print(f"✅ 找到 {len(pending_orders)} 个待撮合订单:")

        for i, order in enumerate(pending_orders, 1):
            print(f"   订单{i}: {order.direction} {order.stock_code} {order.quantity}股 "
                  f"({order.order_type})")

        # 4. 测试撮合
        print("\n4. 开始撮合测试...")

        matched_count = 0
        failed_count = 0

        for order in pending_orders:
            print(f"\n   撮合订单: {order.id} - {order.direction} {order.stock_code}")

            try:
                success, message = matching_engine.match_order(order)

                if success:
                    print(f"   ✅ 撮合成功: {message}")
                    matched_count += 1

                    # 显示成交详情
                    transaction = db.query(Transaction).filter(
                        Transaction.order_id == order.id
                    ).first()

                    if transaction:
                        print(f"   📊 成交详情:")
                        print(f"      价格: ¥{transaction.price:.2f}")
                        print(f"      数量: {transaction.quantity}")
                        print(f"      金额: ¥{transaction.amount:,.2f}")
                        print(f"      手续费: ¥{transaction.commission:.2f}")
                        if transaction.stamp_tax:
                            print(f"      印花税: ¥{transaction.stamp_tax:.2f}")

                else:
                    print(f"   ❌ 撮合失败: {message}")
                    failed_count += 1

            except Exception as e:
                print(f"   ❌ 撮合异常: {str(e)}")
                failed_count += 1

        # 5. 验证结果
        print("\n5. 验证撮合结果...")

        # 检查订单状态
        updated_orders = db.query(Order).filter(
            Order.ai_id == ai_id,
            Order.id.in_([o.id for o in pending_orders])
        ).all()

        filled_count = sum(1 for o in updated_orders if o.status == 'filled')
        rejected_count = sum(1 for o in updated_orders if o.status == 'rejected')

        print(f"✅ 订单状态更新:")
        print(f"   已成交: {filled_count}")
        print(f"   已拒绝: {rejected_count}")
        print(f"   待处理: {len(updated_orders) - filled_count - rejected_count}")

        # 检查持仓变化
        positions = db.query(Position).filter(Position.ai_id == ai_id).all()

        print(f"\n✅ 持仓状态:")
        if positions:
            for pos in positions:
                print(f"   {pos.stock_code}: {pos.quantity}股 "
                      f"@ ¥{pos.avg_cost:.2f} (市值: ¥{pos.market_value:,.2f})")
        else:
            print("   无持仓")

        # 检查资金变化
        updated_ai = db.query(AI).filter(AI.id == ai_id).first()
        cash_change = updated_ai.current_cash - ai.current_cash

        print(f"\n✅ 资金变化:")
        print(f"   原始现金: ¥{ai.current_cash:,.2f}")
        print(f"   当前现金: ¥{updated_ai.current_cash:,.2f}")
        print(f"   变化: {'+' if cash_change >= 0 else ''}¥{cash_change:,.2f}")

        # 6. 统计结果
        print("\n" + "=" * 60)
        print("  撮合测试结果")
        print("=" * 60)
        print(f"总订单数: {len(pending_orders)}")
        print(f"撮合成功: {matched_count}")
        print(f"撮合失败: {failed_count}")
        print(f"成交率: {matched_count}/{len(pending_orders)} "
              f"({matched_count/len(pending_orders)*100:.1f}%)")

        if matched_count > 0:
            print("\n🎉 撮合引擎测试通过！")
        else:
            print("\n⚠️  没有订单被撮合，可能需要检查市场数据或订单条件")

        print("=" * 60)

if __name__ == "__main__":
    try:
        test_matching_engine()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
