#!/usr/bin/env python3
"""
测试决策日志记录功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_session
from models.models import AI, DecisionLog, Order
from data_service.akshare_client import AKShareClient
from portfolio.portfolio_manager import PortfolioManager
from rules.trading_rules import TradingRules
import json

def test_decision_logging():
    """测试决策日志记录功能"""
    print("=" * 60)
    print("  测试决策日志记录")
    print("=" * 60)

    with get_db_session() as db:
        # 1. 初始化组件
        print("\n1. 初始化组件...")
        trading_rules = TradingRules()
        akshare_client = AKShareClient()
        print("✅ 组件初始化完成")

        # 2. 检查AI
        ai = db.query(AI).first()
        if not ai:
            print("\n❌ 需要先创建AI")
            return
        ai_id = ai.id
        ai_name = ai.name

        print(f"\n2. 找到AI: {ai_name} (ID: {ai_id})")

        # 3. 获取市场数据
        print("\n3. 获取市场数据...")
        stock_codes = ["000063", "300750", "600703", "002594", "688256", "600276"]
        quotes = akshare_client.get_realtime_quotes(stock_codes)

        if not quotes:
            print("❌ 无法获取市场数据")
            return

        print(f"✅ 获取到 {len(quotes)} 只股票的实时数据")

        # 4. 手动创建决策日志
        print("\n4. 测试决策日志记录...")

        # 模拟决策数据
        mock_decision = {
            "reasoning": "基于技术分析和市场趋势，决定买入中兴通讯并卖出宁德时代",
            "actions": [
                {
                    "action": "buy",
                    "stock_code": "000063",
                    "quantity": 100,
                    "price_type": "market",
                    "reason": "股价处于低位，有反弹机会"
                },
                {
                    "action": "sell",
                    "stock_code": "300750",
                    "quantity": 50,
                    "price_type": "market",
                    "reason": "股价过高，存在调整风险"
                }
            ]
        }

        # 获取当前持仓快照
        from portfolio.portfolio_manager import PortfolioManager
        portfolio_manager = PortfolioManager(db, trading_rules)
        portfolio_data = portfolio_manager.get_ai_portfolio(ai_id)

        # 创建决策日志
        decision_log = DecisionLog(
            ai_id=ai_id,
            market_data=json.dumps({q.code: {
                'price': q.price,
                'change_percent': q.change_percent,
                'volume': q.volume
            } for q in quotes}),
            portfolio_data=json.dumps({
                'cash': portfolio_data['cash'],
                'total_assets': portfolio_data['total_assets'],
                'positions': portfolio_data['positions']
            }),
            llm_prompt="模拟的完整Prompt内容...",
            llm_response=json.dumps(mock_decision),
            parsed_decision=json.dumps(mock_decision),
            orders_generated=json.dumps(mock_decision['actions']),
            execution_result=json.dumps({
                'success': True,
                'orders_created': 2,
                'message': '决策执行成功'
            }),
            latency_ms=1250,
            tokens_used=450,
            error=None
        )

        db.add(decision_log)
        db.commit()

        print("✅ 决策日志已记录")

        # 5. 验证日志记录
        print("\n5. 验证决策日志...")

        # 查询刚创建的日志
        saved_log = db.query(DecisionLog).filter(
            DecisionLog.id == decision_log.id
        ).first()

        if not saved_log:
            print("❌ 决策日志未找到")
            return

        print("✅ 决策日志查询成功")
        print(f"   日志ID: {saved_log.id}")
        print(f"   AI ID: {saved_log.ai_id}")
        print(f"   时间戳: {saved_log.timestamp}")
        print(f"   延迟: {saved_log.latency_ms}ms")
        print(f"   Token使用: {saved_log.tokens_used}")

        # 验证JSON字段
        try:
            market_data = json.loads(saved_log.market_data)
            portfolio_data = json.loads(saved_log.portfolio_data)
            parsed_decision = json.loads(saved_log.parsed_decision)
            orders_generated = json.loads(saved_log.orders_generated)
            execution_result = json.loads(saved_log.execution_result)

            print("✅ JSON字段解析成功")

            # 显示决策内容
            print(f"   推理: {parsed_decision['reasoning'][:50]}...")
            print(f"   动作数量: {len(parsed_decision['actions'])}")

            # 验证市场数据
            if len(market_data) == len(quotes):
                print("✅ 市场数据完整")
            else:
                print(f"⚠️  市场数据不完整: 期望{len(quotes)}, 实际{len(market_data)}")

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return

        # 6. 测试错误日志记录
        print("\n6. 测试错误日志记录...")

        error_log = DecisionLog(
            ai_id=ai_id,
            market_data=json.dumps({}),
            portfolio_data=json.dumps({}),
            llm_prompt="错误测试Prompt",
            llm_response=None,
            parsed_decision=None,
            orders_generated=None,
            execution_result=json.dumps({
                'success': False,
                'message': 'LLM调用失败'
            }),
            latency_ms=0,
            tokens_used=0,
            error="网络连接超时"
        )

        db.add(error_log)
        db.commit()

        print("✅ 错误日志已记录")

        # 7. 统计日志
        print("\n7. 决策日志统计...")

        total_logs = db.query(DecisionLog).filter(DecisionLog.ai_id == ai_id).count()
        error_logs = db.query(DecisionLog).filter(
            DecisionLog.ai_id == ai_id,
            DecisionLog.error.isnot(None)
        ).count()
        success_logs = total_logs - error_logs

        print(f"✅ AI {ai_name} 的决策日志统计:")
        print(f"   总日志数: {total_logs}")
        print(f"   成功日志: {success_logs}")
        print(f"   错误日志: {error_logs}")

        # 8. 测试日志关联
        print("\n8. 测试日志与订单关联...")

        # 查询最近的成功日志
        recent_logs = db.query(DecisionLog).filter(
            DecisionLog.ai_id == ai_id,
            DecisionLog.error.is_(None)
        ).order_by(DecisionLog.timestamp.desc()).limit(3).all()

        for log in recent_logs:
            orders_count = db.query(Order).filter(
                Order.ai_id == ai_id,
                Order.created_at >= log.timestamp
            ).count()

            print(f"   日志 {log.id}: 生成了 {orders_count} 个订单")

        print("\n" + "=" * 60)
        print("  决策日志记录测试完成！")
        print("  验证了以下功能:")
        print("  • 决策日志的创建和存储")
        print("  • JSON字段的序列化和解析")
        print("  • 市场数据和持仓数据的快照")
        print("  • 错误日志的记录")
        print("  • 日志统计功能")
        print("  • 日志与订单的关联")
        print("=" * 60)

if __name__ == "__main__":
    try:
        test_decision_logging()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
