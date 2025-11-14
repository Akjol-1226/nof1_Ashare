#!/usr/bin/env python3
"""
数据库初始化脚本
创建表 + 插入演示AI数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, get_db_session
from models.models import Base, AI
from datetime import datetime

def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("  数据库初始化")
    print("=" * 60)
    
    # 1. 创建所有表
    print("\n1. 创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ 表结构创建完成")
    
    # 2. 插入演示AI
    print("\n2. 插入演示AI数据...")
    
    with get_db_session() as db:
        # 检查是否已有数据
        existing_count = db.query(AI).count()
        if existing_count > 0:
            print(f"   ⚠️  数据库已有 {existing_count} 个AI，跳过初始化")
            return
        
        # 读取Prompt
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
        
        with open(os.path.join(prompts_dir, 'system_prompt.txt'), 'r', encoding='utf-8') as f:
            base_prompt = f.read()
        
        with open(os.path.join(prompts_dir, 'aggressive_prompt.txt'), 'r', encoding='utf-8') as f:
            aggressive_addon = f.read()
        
        with open(os.path.join(prompts_dir, 'conservative_prompt.txt'), 'r', encoding='utf-8') as f:
            conservative_addon = f.read()
        
        with open(os.path.join(prompts_dir, 'balanced_prompt.txt'), 'r', encoding='utf-8') as f:
            balanced_addon = f.read()
        
        # 创建3个演示AI
        demo_ais = [
            AI(
                name="GPT-4 激进型",
                model_type="gpt-4",
                system_prompt=base_prompt + "\n\n" + aggressive_addon,
                temperature=0.8,
                initial_cash=100000.0,
                current_cash=100000.0,
                total_assets=100000.0,
                total_profit=0.0,
                profit_rate=0.0,
                is_active=True,
                created_at=datetime.now()
            ),
            AI(
                name="Claude-3 保守型",
                model_type="claude-3-sonnet",
                system_prompt=base_prompt + "\n\n" + conservative_addon,
                temperature=0.5,
                initial_cash=100000.0,
                current_cash=100000.0,
                total_assets=100000.0,
                total_profit=0.0,
                profit_rate=0.0,
                is_active=True,
                created_at=datetime.now()
            ),
            AI(
                name="DeepSeek 均衡型",
                model_type="deepseek-chat",
                system_prompt=base_prompt + "\n\n" + balanced_addon,
                temperature=0.7,
                initial_cash=100000.0,
                current_cash=100000.0,
                total_assets=100000.0,
                total_profit=0.0,
                profit_rate=0.0,
                is_active=True,
                created_at=datetime.now()
            ),
        ]
        
        for ai in demo_ais:
            db.add(ai)
            print(f"   ✅ 创建AI: {ai.name}")
        
        db.commit()
    
    print("\n" + "=" * 60)
    print("  ✅ 数据库初始化完成！")
    print("=" * 60)
    
    # 3. 验证
    print("\n3. 验证数据...")
    with get_db_session() as db:
        ais = db.query(AI).all()
        print(f"\n   共有 {len(ais)} 个AI:")
        for ai in ais:
            print(f"   - {ai.name} ({ai.model_type})")
            print(f"     初始资金: ¥{ai.initial_cash:,.2f}")
            print(f"     状态: {'激活' if ai.is_active else '未激活'}")
    
    print("\n✨ 初始化成功！现在可以启动交易系统了。\n")

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

