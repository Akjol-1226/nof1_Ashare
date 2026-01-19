"""
更新所有AI的初始资金为50万
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from models.models import AI

def update_initial_cash(new_initial_cash=500000.0):
    """更新所有AI的初始资金"""
    
    print("=" * 70)
    print(f"  💰 更新AI初始资金为 ¥{new_initial_cash:,.2f}")
    print("=" * 70)
    print()
    
    with get_db_session() as db:
        # 获取所有AI
        ais = db.query(AI).all()
        print(f"📊 找到 {len(ais)} 个AI")
        print()
        
        # 更新每个AI
        for ai in ais:
            old_initial_cash = ai.initial_cash
            old_current_cash = ai.current_cash
            old_total_assets = ai.total_assets
            
            # 更新初始资金
            ai.initial_cash = new_initial_cash
            ai.current_cash = new_initial_cash
            ai.total_assets = new_initial_cash
            
            # 重置收益数据
            ai.total_profit = 0.0
            ai.profit_rate = 0.0
            
            print(f"✅ {ai.name}:")
            print(f"   旧初始资金: ¥{old_initial_cash:,.2f} → 新初始资金: ¥{new_initial_cash:,.2f}")
            print(f"   现金: ¥{old_current_cash:,.2f} → ¥{new_initial_cash:,.2f}")
            print(f"   总资产: ¥{old_total_assets:,.2f} → ¥{new_initial_cash:,.2f}")
            print()
        
        # 提交更改
        db.commit()
        
        print("=" * 70)
        print(f"  ✅ 所有AI初始资金已更新为 ¥{new_initial_cash:,.2f}")
        print("=" * 70)
        print()

if __name__ == "__main__":
    # 可以从命令行参数指定金额
    new_cash = float(sys.argv[1]) if len(sys.argv) > 1 else 500000.0
    update_initial_cash(new_cash)
