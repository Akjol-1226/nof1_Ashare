import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.models import AI, Base
from config import settings

def update_prompts():
    # 1. 读取最新的 system_prompt.txt
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts', 'system_prompt.txt')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            new_prompt = f.read()
            print(f"✅ 已读取最新的 system_prompt.txt ({len(new_prompt)} 字符)")
    except Exception as e:
        print(f"❌ 读取 prompt 文件失败: {e}")
        return

    # 2. 连接数据库
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 3. 获取所有 AI
        ais = db.query(AI).all()
        print(f"📋 找到 {len(ais)} 个 AI")

        # 4. 更新 Prompt
        for ai in ais:
            print(f"🔄 正在更新 AI: {ai.name} ...")
            ai.system_prompt = new_prompt
        
        db.commit()
        print("✅ 所有 AI 的 System Prompt 已更新完毕！")
        
    except Exception as e:
        print(f"❌ 更新数据库失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_prompts()
