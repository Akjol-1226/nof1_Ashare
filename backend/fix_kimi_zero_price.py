"""
修复寒武纪(688256)的0元成交异常数据

问题：
- Order ID 157: 限价 1258.0 买入寒武纪，但 filled_price 被错误记录为 0.0
- Transaction ID 152: 成交价格为 0.0，导致持仓成本价异常低（0.01元）
- 导致盈利计算暴涨 150,000 倍

修复方案：
- 将成交价格修正为限价委托价 1258.0
- 重新计算持仓成本价、市值和盈亏
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import AI, Order, Transaction, Position
from datetime import datetime

# 数据库路径（使用绝对路径）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nof1_ashare.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

def fix_kimi_transaction():
    """修复 Kimi 的寒武纪异常成交记录"""
    session = Session()
    
    try:
        print("\n" + "="*60)
        print("🔧 开始修复 Kimi 寒武纪 0元成交异常")
        print("="*60)
        
        # 1. 检查订单
        order = session.query(Order).filter(Order.id == 157).first()
        if not order:
            print("❌ 未找到 Order ID 157")
            return
        
        print(f"\n📋 订单信息 (ID: {order.id}):")
        print(f"   AI: {order.ai_id} ({order.stock_code})")
        print(f"   委托价格: ¥{order.price:.2f}")
        print(f"   ❌ 当前成交价: ¥{order.filled_price:.2f}")
        
        # 确定修正价格（使用限价委托价）
        correct_price = order.price  # 1258.0
        print(f"\n✅ 修正成交价为: ¥{correct_price:.2f}")
        
        # 2. 修正 Order 记录
        order.filled_price = correct_price
        print(f"\n✓ 更新 Order.filled_price = {correct_price}")
        
        # 3. 修正 Transaction 记录
        transaction = session.query(Transaction).filter(Transaction.id == 152).first()
        if transaction:
            print(f"\n📝 交易记录 (ID: {transaction.id}):")
            print(f"   ❌ 旧价格: ¥{transaction.price:.2f}")
            print(f"   ❌ 旧金额: ¥{transaction.amount:.2f}")
            
            transaction.price = correct_price
            transaction.amount = correct_price * transaction.quantity  # 1258.0 * 500
            
            print(f"   ✅ 新价格: ¥{transaction.price:.2f}")
            print(f"   ✅ 新金额: ¥{transaction.amount:.2f}")
        
        # 4. 重新计算持仓成本
        position = session.query(Position).filter(
            Position.ai_id == 2,
            Position.stock_code == '688256'
        ).first()
        
        if position:
            print(f"\n📊 持仓信息 ({position.stock_code}):")
            print(f"   数量: {position.quantity} 股")
            print(f"   ❌ 旧成本价: ¥{position.avg_cost:.2f}")
            
            # 重新计算成本价 = (价格 * 数量 + 手续费) / 数量
            quantity = position.quantity  # 500
            fee = transaction.total_fee if transaction else 5.0  # 5元
            new_avg_cost = (correct_price * quantity + fee) / quantity
            
            position.avg_cost = new_avg_cost
            position.market_value = position.current_price * quantity
            
            # 重新计算盈亏
            cost_basis = new_avg_cost * quantity
            position.profit = position.market_value - cost_basis
            if cost_basis > 0:
                position.profit_rate = (position.profit / cost_basis) * 100
            else:
                position.profit_rate = 0.0
            
            print(f"   ✅ 新成本价: ¥{position.avg_cost:.2f}")
            print(f"   当前价: ¥{position.current_price:.2f}")
            print(f"   市值: ¥{position.market_value:,.2f}")
            print(f"   盈亏: ¥{position.profit:,.2f} ({position.profit_rate:.2f}%)")
        
        # 5. 重新计算 AI 的资金状况
        ai = session.query(AI).filter(AI.id == 2).first()
        if ai:
            # 重新计算应该扣除的资金（买入时应该扣除的金额）
            # 原本扣除了: 0 * 500 + 5 = 5 元
            # 应该扣除: 1258 * 500 + 5 = 629,005 元
            # 差额: 629,000 元需要补扣
            
            old_cost = 0 * 500 + 5  # 当初按0元成交扣的
            correct_cost = correct_price * 500 + fee  # 应该扣的
            refund_amount = old_cost - correct_cost  # 需要退还的（负数表示需要补扣）
            
            print(f"\n💰 AI 资金调整:")
            print(f"   当前现金: ¥{ai.current_cash:,.2f}")
            print(f"   需补扣: ¥{-refund_amount:,.2f}")
            
            ai.current_cash += refund_amount
            
            # 重新计算总资产（现金 + 所有持仓市值）
            positions = session.query(Position).filter(Position.ai_id == 2).all()
            total_market_value = sum(p.market_value for p in positions)
            ai.total_assets = ai.current_cash + total_market_value
            
            # 重新计算收益
            ai.total_profit = ai.total_assets - ai.initial_cash
            ai.profit_rate = (ai.total_profit / ai.initial_cash) * 100 if ai.initial_cash > 0 else 0.0
            
            print(f"   ✅ 修正后现金: ¥{ai.current_cash:,.2f}")
            print(f"   总资产: ¥{ai.total_assets:,.2f}")
            print(f"   总收益: ¥{ai.total_profit:,.2f} ({ai.profit_rate:.2f}%)")
        
        # 6. 提交所有修改
        session.commit()
        
        print("\n" + "="*60)
        print("✅ 修复完成！")
        print("="*60)
        
        # 7. 验证修复结果
        print("\n🔍 验证修复结果:")
        verify_order = session.query(Order).filter(Order.id == 157).first()
        verify_trans = session.query(Transaction).filter(Transaction.id == 152).first()
        verify_pos = session.query(Position).filter(
            Position.ai_id == 2, Position.stock_code == '688256'
        ).first()
        
        print(f"   Order.filled_price: ¥{verify_order.filled_price:.2f}")
        print(f"   Transaction.price: ¥{verify_trans.price:.2f}")
        print(f"   Position.avg_cost: ¥{verify_pos.avg_cost:.2f}")
        print(f"   Position.profit_rate: {verify_pos.profit_rate:.2f}%")
        
        print("\n✓ 数据已修复并验证通过！\n")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    fix_kimi_transaction()
