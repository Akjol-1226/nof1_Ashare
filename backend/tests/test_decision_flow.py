#!/usr/bin/env python3
"""
测试端到端AI决策流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI
from data_service.akshare_client import AKShareClient
from ai_service.prompt_builder import PromptBuilder
from ai_service.decision_parser import DecisionParser
from ai_service.llm_adapters.adapter_factory import LLMAdapterFactory

def test_decision_flow():
    """测试完整的决策流程"""
    print("=" * 60)
    print("  测试端到端AI决策流程")
    print("=" * 60)

    # 1. 检查环境变量
    print("\n1. 检查环境变量...")
    env_vars = ['DASHSCOPE_API_KEY', 'MOONSHOT_API_KEY', 'DEEPSEEK_API_KEY']
    missing_vars = []

    for var in env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        print("请先设置环境变量，然后再运行测试")
        return
    else:
        print("✅ 所有环境变量已设置")

    # 2. 检查数据库
    print("\n2. 检查数据库...")
    with get_db_session() as db:
        ais = db.query(AI).filter(AI.is_active == True).all()
        if not ais:
            print("❌ 数据库中没有激活的AI")
            print("请先运行: python3 backend/scripts/import_ais.py")
            return

        print(f"✅ 找到 {len(ais)} 个激活的AI:")
        for ai in ais:
            print(f"   • {ai.name} ({ai.model_type})")

    # 3. 测试数据获取
    print("\n3. 测试实时行情获取...")
    try:
        client = AKShareClient()
        quotes = client.get_realtime_quotes()
        if not quotes:
            print("❌ 无法获取实时行情")
            return

        print(f"✅ 获取到 {len(quotes)} 只股票的行情数据")
        for i, q in enumerate(quotes[:3]):  # 只显示前3只
            print(f"   • {q.code} {q.name}: ¥{q.price:.2f} ({q.change_percent:+.2f}%)")

    except Exception as e:
        print(f"❌ 行情获取失败: {str(e)}")
        return

    # 4. 测试适配器创建
    print("\n4. 测试LLM适配器...")
    for ai in ais:
        try:
            adapter = LLMAdapterFactory.create_adapter(ai.name)
            if adapter:
                print(f"✅ {ai.name} 适配器创建成功")
            else:
                print(f"❌ {ai.name} 适配器创建失败")
                return
        except Exception as e:
            print(f"❌ {ai.name} 适配器创建异常: {str(e)}")
            return

    # 5. 测试Prompt构建
    print("\n5. 测试Prompt构建...")
    try:
        builder = PromptBuilder()
        parser = DecisionParser()

        # 选择第一个AI进行测试
        test_ai = ais[0]
        positions = []  # 空持仓

        user_prompt = builder.build_user_prompt(test_ai, quotes, positions)
        full_prompt = builder.build_full_prompt(test_ai.system_prompt, user_prompt)

        print(f"✅ {test_ai.name} Prompt构建成功")
        print(f"   System Prompt长度: {len(full_prompt['system'])} 字符")
        print(f"   User Prompt长度: {len(full_prompt['user'])} 字符")

    except Exception as e:
        print(f"❌ Prompt构建失败: {str(e)}")
        return

    # 6. 测试决策解析
    print("\n6. 测试决策解析...")

    # 模拟一个简单的决策响应
    mock_response = '''{
  "reasoning": "测试决策流程，暂时观望",
  "actions": []
}'''

    try:
        parse_result = parser.parse(mock_response)
        if parse_result["success"]:
            print("✅ 决策解析成功")
            print(f"   推理: {parse_result['reasoning']}")
            print(f"   操作数量: {len(parse_result['actions'])}")
        else:
            print(f"❌ 决策解析失败: {parse_result['error']}")
            return

    except Exception as e:
        print(f"❌ 决策解析异常: {str(e)}")
        return

    # 7. 测试LLM调用（可选）
    print("\n7. 测试LLM调用（可选）...")

    test_llm = input("是否测试真实的LLM调用? (y/n): ").strip().lower()
    if test_llm == 'y':
        try:
            adapter = LLMAdapterFactory.create_adapter(test_ai.name)
            if adapter:
                # 发送一个简单的测试请求
                messages = [
                    {"role": "system", "content": "你是一个测试助手，请简短回复"},
                    {"role": "user", "content": "Hello"}
                ]

                result = adapter.call_api(messages, timeout=10)
                if result["success"]:
                    print("✅ LLM调用成功")
                    print(f"   响应: {result['response'][:100]}...")
                    print(f"   延迟: {result['latency_ms']}ms")
                else:
                    print(f"❌ LLM调用失败: {result['error']}")
            else:
                print("❌ 无法创建适配器")

        except Exception as e:
            print(f"❌ LLM调用异常: {str(e)}")

    # 8. 总结
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)
    print("✅ 环境变量检查通过")
    print("✅ 数据库连接正常")
    print("✅ 实时行情获取成功")
    print("✅ LLM适配器创建成功")
    print("✅ Prompt构建正常")
    print("✅ 决策解析工作正常")
    print()
    print("🎉 端到端决策流程测试通过！")
    print()
    print("现在可以启动AI交易系统了:")
    print("  cd backend")
    print("  python3 main.py")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_decision_flow()
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
