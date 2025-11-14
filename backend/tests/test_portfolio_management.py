#!/usr/bin/env python3
"""
测试持仓管理功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI, Position
from portfolio.portfolio_manager import PortfolioManager
from rules.trading_rules import TradingRules

def test_portfolio_management():
    """测试持仓管理功能"""
    print("=" * 60)
    print("  测试持仓管理")
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

        # 2. 初始化持仓管理器
        print("\n2. 初始化持仓管理器...")
        trading_rules = TradingRules()
        portfolio_manager = PortfolioManager(db, trading_rules)
        print("✅ 持仓管理器初始化完成")

        # 3. 测试获取持仓信息
        print("\n3. 测试获取持仓信息...")
        portfolio = portfolio_manager.get_ai_portfolio(ai_id)

        print("✅ AI持仓概览:")
        print(f"   AI名称: {portfolio['ai_name']}")
        print(f"   现金: ¥{portfolio['cash']:,.2f}")
        print(f"   总资产: ¥{portfolio['total_assets']:,.2f}")
        print(f"   总收益: ¥{portfolio['total_profit']:,.2f}")
        print(f"   收益率: {portfolio['profit_rate']:+.2f}%")

        positions = portfolio['positions']
        print(f"   持仓数量: {len(positions)}")

        if positions:
            for pos in positions:
                print(f"   • {pos['stock_code']} {pos['stock_name']}: "
                      f"{pos['quantity']}股 @ ¥{pos['cost_price']:.2f} "
                      f"(市值: ¥{pos['market_value']:,.2f})")
        else:
            print("   无持仓记录")

        # 4. 测试现金检查
        print("\n4. 测试现金检查...")
        test_amounts = [1000, 50000, 150000]  # 小额、中等、大额

        for amount in test_amounts:
            is_sufficient, available = portfolio_manager.check_available_cash(ai_id, amount)
            status = "✅ 充足" if is_sufficient else "❌ 不足"
            print(f"   检查 ¥{amount:,} : {status} (可用: ¥{available:,.2f})")

        # 5. 测试卖出数量检查
        print("\n5. 测试卖出数量检查...")

        # 检查现有持仓的卖出能力
        if positions:
            for pos in positions:
                test_quantities = [10, 50, pos['available_quantity'] + 10]

                for qty in test_quantities:
                    is_sufficient, available = portfolio_manager.check_sellable_quantity(
                        ai_id, pos['stock_code'], qty
                    )
                    status = "✅ 可卖" if is_sufficient else "❌ 不足"
                    print(f"   {pos['stock_code']} 卖出{qty}股: {status} (可用: {available})")
        else:
            print("   无持仓，无法测试卖出检查")

        # 6. 测试持仓更新
        print("\n6. 测试持仓更新...")

        # 模拟买入
        test_stock = "000063"
        test_name = "中兴通讯"
        buy_price = 40.0
        buy_quantity = 50
        buy_fee = 25.0

        print(f"   模拟买入: {test_stock} {buy_quantity}股 @ ¥{buy_price:.2f}")

        try:
            portfolio_manager.update_position_on_buy(
                ai_id, test_stock, test_name, buy_price, buy_quantity, buy_fee
            )
            print("   ✅ 买入更新成功")

            # 验证买入结果
            updated_portfolio = portfolio_manager.get_ai_portfolio(ai_id)
            updated_positions = updated_portfolio['positions']
            target_pos = next((p for p in updated_positions if p['stock_code'] == test_stock), None)

            if target_pos:
                print(f"   📊 买入后持仓: {target_pos['quantity']}股 @ ¥{target_pos['cost_price']:.2f}")
                print(f"   💰 现金变化: ¥{updated_portfolio['cash']:.2f} (原: ¥{portfolio['cash']:.2f})")

        except Exception as e:
            print(f"   ❌ 买入更新失败: {str(e)}")

        # 7. 测试卖出（如果有持仓）
        if positions:
            sell_stock = positions[0]['stock_code']
            sell_quantity = min(20, positions[0]['available_quantity'])  # 卖出20股或可用数量

            if sell_quantity > 0:
                print(f"\n   模拟卖出: {sell_stock} {sell_quantity}股 @ ¥{buy_price:.2f}")

                try:
                    portfolio_manager.update_position_on_sell(
                        ai_id, sell_stock, buy_price, sell_quantity, buy_fee
                    )
                    print("   ✅ 卖出更新成功")

                    # 验证卖出结果
                    final_portfolio = portfolio_manager.get_ai_portfolio(ai_id)
                    final_positions = final_portfolio['positions']
                    final_pos = next((p for p in final_positions if p['stock_code'] == sell_stock), None)

                    if final_pos:
                        print(f"   📊 卖出后持仓: {final_pos['quantity']}股")
                        print(f"   💰 现金变化: ¥{final_portfolio['cash']:.2f}")
                    else:
                        print("   📊 持仓已清空")

                except Exception as e:
                    print(f"   ❌ 卖出更新失败: {str(e)}")

        # 8. 最终验证
        print("\n7. 最终验证...")

        final_portfolio = portfolio_manager.get_ai_portfolio(ai_id)
        final_positions = final_portfolio['positions']

        print("✅ 最终持仓状态:")
        print(f"   现金: ¥{final_portfolio['cash']:,.2f}")
        print(f"   总资产: ¥{final_portfolio['total_assets']:,.2f}")
        print(f"   总收益: ¥{final_portfolio['total_profit']:,.2f}")
        print(f"   收益率: {final_portfolio['profit_rate']:+.2f}%")

        if final_positions:
            print("   持仓详情:")
            for pos in final_positions:
                print(f"   • {pos['stock_code']}: {pos['quantity']}股 "
                      f"(可用: {pos['available_quantity']}) @ ¥{pos['cost_price']:.2f}")
        else:
            print("   无持仓")

        print("\n" + "=" * 60)
        print("  持仓管理测试完成！")
        print("=" * 60)

if __name__ == "__main__":
    try:
        test_portfolio_management()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
