#!/usr/bin/env python3
"""
快速添加AI的脚本
从ais_config.py读取配置并批量添加AI
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from models.models import AI
from ais_config import AI_CONFIGS


def add_ais_from_config():
    """从配置文件批量添加AI"""
    print("\n" + "=" * 80)
    print("📋 从配置文件添加AI")
    print("=" * 80)
    
    with get_db_session() as db:
        added_count = 0
        skipped_count = 0
        
        for config in AI_CONFIGS:
            name = config['name']
            model_name = config['model_name']
            initial_cash = config.get('initial_cash', 100000.0)
            
            # 检查是否已存在
            existing = db.query(AI).filter(AI.name == name).first()
            if existing:
                print(f"⏭️  跳过 '{name}' (已存在)")
                skipped_count += 1
                continue
            
            # 创建新AI (API Key从环境变量读取，不存储在数据库)
            new_ai = AI(
                name=name,
                model_name=model_name,
                initial_cash=initial_cash,
                current_cash=initial_cash,
                total_assets=initial_cash,
                temperature=config.get('temperature', 0.7),
                system_prompt=config.get('system_prompt'),
                is_active=True
            )
            
            db.add(new_ai)
            added_count += 1
            
            # 检查环境变量是否设置
            api_key_env = config.get('api_key_env')
            api_key_status = "✅ 已设置" if os.getenv(api_key_env) else "❌ 未设置"
            
            print(f"✅ 添加 '{name}'")
            print(f"   模型: {model_name}")
            print(f"   初始资金: ¥{initial_cash:,.2f}")
            print(f"   温度: {config.get('temperature', 0.7)}")
            print(f"   环境变量 {api_key_env}: {api_key_status}")
            print()
        
        db.commit()
        
        print("=" * 80)
        print(f"📊 添加完成: 成功 {added_count} 个, 跳过 {skipped_count} 个")
        print("=" * 80)
        print()


def list_all_ais():
    """列出所有AI"""
    with get_db_session() as db:
        ais = db.query(AI).all()
        
        if not ais:
            print("\n数据库中没有AI数据\n")
            return
        
        print("\n" + "=" * 80)
        print(f"📋 当前数据库中的AI列表 (共 {len(ais)} 个)")
        print("=" * 80)
        
        for ai in ais:
            print(f"\n🤖 ID: {ai.id} | {ai.name}")
            print(f"   模型: {ai.model_name}")
            print(f"   资金: ¥{ai.current_cash:,.2f} / ¥{ai.initial_cash:,.2f}")
            print(f"   总资产: ¥{ai.total_assets:,.2f}")
            print(f"   收益: ¥{ai.total_profit:,.2f} ({ai.profit_rate:.2f}%)")
            print(f"   交易: {ai.trade_count} 次 | 胜率: {ai.win_rate:.2f}%")
            print(f"   状态: {'🟢 激活' if ai.is_active else '🔴 停用'}")
        
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_all_ais()
    else:
        add_ais_from_config()
        print("\n查看AI列表:")
        list_all_ais()
