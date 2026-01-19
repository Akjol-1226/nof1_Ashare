#!/usr/bin/env python3
"""
从配置文件导入AI到数据库
API Key不存数据库，运行时从环境变量读取
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI
from ais_config import AI_CONFIGS
from datetime import datetime

def import_ais():
    """从配置文件导入AI"""
    print("=" * 60)
    print("  从配置导入AI")
    print("=" * 60)
    
    # 读取prompt模板
    prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts')
    
    with open(os.path.join(prompts_dir, 'system_prompt.txt'), 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    strategy_prompts = {}
    for strategy_name in ['aggressive', 'conservative', 'balanced']:
        with open(os.path.join(prompts_dir, f'{strategy_name}_prompt.txt'), 'r', encoding='utf-8') as f:
            strategy_prompts[strategy_name] = f.read()
    
    with get_db_session() as db:
        imported_count = 0
        skipped_count = 0
        
        for config in AI_CONFIGS:
            # 检查是否已存在
            existing = db.query(AI).filter_by(name=config['name']).first()
            if existing:
                print(f"\n⚠️  跳过: {config['name']} (已存在)")
                skipped_count += 1
                continue
            
            # 检查环境变量
            api_key_env = config.get('api_key_env')
            if api_key_env and not os.getenv(api_key_env):
                print(f"\n⚠️  警告: {config['name']} 的环境变量 {api_key_env} 未设置")
                print(f"    提示: export {api_key_env}='your-api-key'")
            
            # 构建system_prompt
            strategy = config.get('strategy', 'balanced')
            system_prompt = base_prompt + "\n\n" + strategy_prompts.get(strategy, strategy_prompts['balanced'])
            
            # 创建AI（API Key从环境变量读取）
            ai = AI(
                name=config['name'],
                model_name=config['model_name'],
                system_prompt=system_prompt,
                temperature=config.get('temperature', 0.7),
                initial_cash=config.get('initial_cash', 100000.0),
                current_cash=config.get('initial_cash', 100000.0),
                total_assets=config.get('initial_cash', 100000.0),
                is_active=True,
                created_at=datetime.now()
            )
            
            db.add(ai)
            imported_count += 1
            print(f"\n✅ 导入: {config['name']}")
            print(f"   模型: {config['model_name']}")
            print(f"   策略: {config.get('strategy', 'balanced')}")
            print(f"   温度: {config.get('temperature', 0.7)}")
            print(f"   资金: ¥{config.get('initial_cash', 100000):,.0f}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print(f"  导入完成！")
        print(f"  成功: {imported_count} | 跳过: {skipped_count}")
        print("=" * 60)
        
        # 显示所有AI
        print("\n当前AI列表:")
        all_ais = db.query(AI).all()
        for ai in all_ais:
            print(f"  {ai.id}. {ai.name} ({ai.model_name})")
        
        # 提示设置环境变量
        print("\n💡 重要：运行前请设置环境变量:")
        for config in AI_CONFIGS:
            api_key_env = config.get('api_key_env')
            if api_key_env:
                print(f"   export {api_key_env}='your-api-key'")

if __name__ == "__main__":
    try:
        import_ais()
    except Exception as e:
        print(f"\n❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()

