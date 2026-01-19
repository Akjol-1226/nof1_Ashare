#!/usr/bin/env python3
"""
数据库迁移：为Position表添加last_trade_date字段
修复T+1可卖数量永远为0的问题
"""

from database import get_db_session
from models.models import Position
from sqlalchemy import text
from datetime import datetime

def migrate():
    """执行迁移"""
    print("=" * 60)
    print("📦 数据库迁移：添加 last_trade_date 字段")
    print("=" * 60)
    
    with get_db_session() as db:
        try:
            # 1. 检查字段是否已存在
            result = db.execute(text("PRAGMA table_info(position)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'last_trade_date' in columns:
                print("✅ last_trade_date 字段已存在，无需迁移")
                return
            
            print("\n📝 添加 last_trade_date 字段...")
            
            # 2. 添加新字段
            db.execute(text("""
                ALTER TABLE position 
                ADD COLUMN last_trade_date DATETIME
            """))
            
            # 3. 将所有existing持仓的last_trade_date初始化为updated_at
            # 这样已有的持仓会在下次get_ai_portfolio时被T+1解锁
            db.execute(text("""
                UPDATE position 
                SET last_trade_date = updated_at
            """))
            
            db.commit()
            
            print("✅ 字段添加成功")
            
            # 4. 验证迁移结果
            positions = db.query(Position).all()
            print(f"\n📊 验证迁移结果：")
            print(f"   总持仓数: {len(positions)}")
            
            for pos in positions[:5]:  # 只显示前5个
                print(f"   - {pos.stock_code}: last_trade_date = {pos.last_trade_date}")
            
            if len(positions) > 5:
                print(f"   ... 还有 {len(positions) - 5} 个持仓")
            
            print("\n✅ 迁移完成！")
            print("\n💡 提示：重启系统后，T+1可卖数量将正常工作")
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            db.rollback()
            raise

if __name__ == "__main__":
    migrate()
