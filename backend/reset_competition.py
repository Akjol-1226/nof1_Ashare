"""
重置竞赛数据 - 保留AI信息，清空所有交易数据
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI, Position, Order, Transaction, PortfolioSnapshot, DecisionLog


def reset_competition():
    """重置竞赛数据"""
    
    print("=" * 70)
    print("  🔄 重置AI竞赛数据")
    print("=" * 70)
    print()
    
    with get_db_session() as db:
        # 获取所有AI
        ais = db.query(AI).all()
        print(f"📊 找到 {len(ais)} 个AI：")
        for ai in ais:
            print(f"  - {ai.name} (ID: {ai.id})")
        print()
        
        # 确认操作
        print("⚠️  警告：此操作将清空以下数据：")
        print("  1. 所有持仓 (Position)")
        print("  2. 所有订单 (Order)")
        print("  3. 所有成交记录 (Transaction)")
        print("  4. 所有快照 (PortfolioSnapshot)")
        print("  5. 所有决策日志 (DecisionLog)")
        print("  6. 重置所有AI的资金和统计数据")
        print()
        
        confirm = input("确认要重置竞赛数据吗？(输入 'YES' 确认): ")
        if confirm != "YES":
            print("❌ 操作已取消")
            return
        
        print()
        print("开始清空数据...")
        print()
        
        # 统计删除数量
        stats = {}
        
        # 清空持仓
        position_count = db.query(Position).count()
        db.query(Position).delete()
        stats['持仓'] = position_count
        print(f"✅ 清空持仓：{position_count} 条")
        
        # 清空订单
        order_count = db.query(Order).count()
        db.query(Order).delete()
        stats['订单'] = order_count
        print(f"✅ 清空订单：{order_count} 条")
        
        # 清空成交记录
        transaction_count = db.query(Transaction).count()
        db.query(Transaction).delete()
        stats['成交记录'] = transaction_count
        print(f"✅ 清空成交记录：{transaction_count} 条")
        
        # 清空快照
        snapshot_count = db.query(PortfolioSnapshot).count()
        db.query(PortfolioSnapshot).delete()
        stats['快照'] = snapshot_count
        print(f"✅ 清空快照：{snapshot_count} 条")
        
        # 清空决策日志
        decision_count = db.query(DecisionLog).count()
        db.query(DecisionLog).delete()
        stats['决策日志'] = decision_count
        print(f"✅ 清空决策日志：{decision_count} 条")
        
        print()
        print("重置AI状态...")
        print()
        
        # 重置所有AI的状态
        for ai in ais:
            initial_cash = ai.initial_cash if ai.initial_cash else 100000.0
            
            ai.current_cash = initial_cash
            ai.total_assets = initial_cash
            ai.total_profit = 0.0
            ai.profit_rate = 0.0
            ai.trade_count = 0
            ai.win_count = 0
            ai.win_rate = 0.0
            
            print(f"✅ 重置 {ai.name}:")
            print(f"   - 现金: ¥{initial_cash:,.2f}")
            print(f"   - 总资产: ¥{initial_cash:,.2f}")
            print(f"   - 总收益: ¥0.00")
            print(f"   - 收益率: 0.00%")
            print()
        
        # 提交所有更改
        db.commit()
        
        print()
        print("=" * 70)
        print("  ✅ 竞赛数据重置完成！")
        print("=" * 70)
        print()
        print("📊 清空数据汇总：")
        for key, value in stats.items():
            print(f"  - {key}: {value} 条")
        print()
        print(f"🤖 保留 {len(ais)} 个AI，所有AI已重置为初始状态")
        print()
        print("💡 提示：现在可以重新启动系统开始新的竞赛！")
        print()


if __name__ == "__main__":
    reset_competition()
