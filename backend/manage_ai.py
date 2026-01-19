"""
AI数据管理脚本 - 查看、删除和添加AI
"""

import sys
from database import get_db_session
from models.models import AI, Position, Order, Transaction, PortfolioSnapshot, DecisionLog


def list_all_ai():
    """列出所有AI"""
    with get_db_session() as db:
        ais = db.query(AI).all()
        if not ais:
            print("数据库中没有AI数据")
            return
        
        print("\n当前数据库中的AI列表:")
        print("-" * 100)
        for ai in ais:
            print(f"ID: {ai.id}")
            print(f"名称: {ai.name}")
            print(f"模型类型: {ai.model_name}")
            print(f"初始资金: ¥{ai.initial_cash:,.2f}")
            print(f"当前现金: ¥{ai.current_cash:,.2f}")
            print(f"总资产: ¥{ai.total_assets:,.2f}")
            print(f"总收益: ¥{ai.total_profit:,.2f}")
            print(f"收益率: {ai.profit_rate:.2f}%")
            print(f"交易次数: {ai.trade_count}")
            print(f"胜率: {ai.win_rate:.2f}%")
            print(f"是否激活: {'是' if ai.is_active else '否'}")
            print(f"创建时间: {ai.created_at}")
            print("-" * 100)


def delete_all_ai():
    """删除所有AI及其相关数据"""
    with get_db_session() as db:
        ais = db.query(AI).all()
        if not ais:
            print("数据库中没有AI数据，无需删除")
            return
        
        print(f"\n准备删除 {len(ais)} 个AI及其所有相关数据...")
        
        # 删除所有相关数据
        for ai in ais:
            print(f"正在删除 AI: {ai.name} (ID: {ai.id})")
            
            # 删除决策日志
            decision_count = db.query(DecisionLog).filter(DecisionLog.ai_id == ai.id).count()
            db.query(DecisionLog).filter(DecisionLog.ai_id == ai.id).delete()
            print(f"  - 删除了 {decision_count} 条决策日志")
            
            # 删除持仓快照
            snapshot_count = db.query(PortfolioSnapshot).filter(PortfolioSnapshot.ai_id == ai.id).count()
            db.query(PortfolioSnapshot).filter(PortfolioSnapshot.ai_id == ai.id).delete()
            print(f"  - 删除了 {snapshot_count} 条持仓快照")
            
            # 删除成交记录
            transaction_count = db.query(Transaction).filter(Transaction.ai_id == ai.id).count()
            db.query(Transaction).filter(Transaction.ai_id == ai.id).delete()
            print(f"  - 删除了 {transaction_count} 条成交记录")
            
            # 删除订单
            order_count = db.query(Order).filter(Order.ai_id == ai.id).count()
            db.query(Order).filter(Order.ai_id == ai.id).delete()
            print(f"  - 删除了 {order_count} 条订单")
            
            # 删除持仓
            position_count = db.query(Position).filter(Position.ai_id == ai.id).count()
            db.query(Position).filter(Position.ai_id == ai.id).delete()
            print(f"  - 删除了 {position_count} 条持仓记录")
            
            # 删除AI
            db.delete(ai)
            print(f"  - 删除了 AI: {ai.name}")
        
        db.commit()
        print("\n✅ 所有AI数据已成功删除！")


def add_ai(name, model_name, initial_cash=100000.0):
    """添加新的AI"""
    with get_db_session() as db:
        # 检查是否已存在同名AI
        existing = db.query(AI).filter(AI.name == name).first()
        if existing:
            print(f"❌ 错误: AI '{name}' 已存在！")
            return False
        
        # 创建新AI
        new_ai = AI(
            name=name,
            model_name=model_name,
            initial_cash=initial_cash,
            current_cash=initial_cash,
            total_assets=initial_cash,
            is_active=True
        )
        
        db.add(new_ai)
        db.commit()
        db.refresh(new_ai)
        
        print(f"\n✅ 成功添加 AI: {name}")
        print(f"   ID: {new_ai.id}")
        print(f"   模型类型: {model_name}")
        print(f"   初始资金: ¥{initial_cash:,.2f}")
        return True


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage_ai.py list              # 列出所有AI")
        print("  python manage_ai.py delete            # 删除所有AI")
        print("  python manage_ai.py add <名称> <模型类型> [初始资金]")
        print("\n示例:")
        print("  python manage_ai.py add 'GPT-4交易员' gpt-4 100000")
        print("  python manage_ai.py add 'Claude交易员' claude-3-5-sonnet-20241022 100000")
        print("  python manage_ai.py add 'DeepSeek交易员' deepseek-chat 100000")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_all_ai()
    elif command == "delete":
        confirm = input("\n⚠️  确定要删除所有AI数据吗？此操作不可恢复！(输入 'yes' 确认): ")
        if confirm.lower() == 'yes':
            delete_all_ai()
        else:
            print("已取消删除操作")
    elif command == "add":
        if len(sys.argv) < 4:
            print("❌ 错误: 请提供AI名称和模型类型")
            print("用法: python manage_ai.py add <名称> <模型类型> [初始资金]")
            return
        
        name = sys.argv[2]
        model_type = sys.argv[3]
        initial_cash = float(sys.argv[4]) if len(sys.argv) > 4 else 100000.0
        
        add_ai(name, model_type, initial_cash=initial_cash)
    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: list, delete, add")


if __name__ == "__main__":
    main()
