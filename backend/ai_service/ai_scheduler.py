"""
AI调度器
管理AI决策流程的定时调度和执行
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from database import get_db_session
from models.models import AI, DecisionLog, PortfolioSnapshot
from data_service.akshare_client import AKShareClient
from ai_service.prompt_builder import PromptBuilder
from ai_service.decision_parser import DecisionParser
from ai_service.llm_adapters.adapter_factory import LLMAdapterFactory

# 导入WebSocket管理器用于广播
try:
    from main import manager
except ImportError:
    manager = None
from trading_engine.order_manager import OrderManager
from portfolio.portfolio_manager import PortfolioManager
from rules.trading_rules import TradingRules

logger = logging.getLogger(__name__)


class AIScheduler:
    """AI决策调度器"""

    def __init__(self):
        self.is_running = False
        self.data_client = AKShareClient()
        self.prompt_builder = PromptBuilder()
        self.decision_parser = DecisionParser()
        self.trading_rules = TradingRules()
        self.order_manager = None
        self.portfolio_manager = None

        # 缓存适配器实例
        self.adapters_cache = {}

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return

        self.is_running = True
        logger.info("AI调度器已启动")

        # 创建管理器实例（稍后在循环中传入db）

        # 开始调度循环
        asyncio.create_task(self._schedule_loop())

    def stop(self):
        """停止调度器"""
        self.is_running = False
        logger.info("AI调度器已停止")

    async def _schedule_loop(self):
        """调度主循环"""
        while self.is_running:
            try:
                await self._execute_decision_cycle()
                await asyncio.sleep(10)  # 每10秒执行一次

            except Exception as e:
                logger.error(f"调度循环异常: {str(e)}")
                await asyncio.sleep(5)  # 出错后等待5秒再试

    async def _execute_decision_cycle(self):
        """执行一次完整的决策周期"""
        cycle_start = time.time()

        try:
            logger.info("=== 开始AI决策周期 ===")

            # 1. 获取实时行情
            quotes = self.data_client.get_realtime_quotes()
            if not quotes:
                logger.warning("无法获取实时行情，跳过本次周期")
                return

            logger.info(f"获取到 {len(quotes)} 只股票的行情数据")

            # 2. 遍历所有激活的AI
            with get_db_session() as db:
                active_ais = db.query(AI).filter(AI.is_active == True).all()

                for ai in active_ais:
                    try:
                        await self._process_ai_decision(ai, quotes, db)
                    except Exception as e:
                        logger.error(f"处理AI {ai.name} 决策失败: {str(e)}")
                        continue

            # 3. 保存组合快照
            self._save_portfolio_snapshots(db)

            cycle_time = time.time() - cycle_start
            logger.info(f"决策周期完成，耗时: {cycle_time:.2f}秒")
        except Exception as e:
            logger.error(f"决策周期执行失败: {str(e)}")

    async def _process_ai_decision(self, ai: AI, quotes: List, db: Session):
        """
        处理单个AI的决策过程

        Args:
            ai: AI对象
            quotes: 实时行情
            db: 数据库会话
        """
        decision_start = time.time()

        try:
            logger.info(f"处理AI: {ai.name}")

            # 1. 构建用户Prompt
            portfolio_manager = PortfolioManager(db, self.trading_rules)
            portfolio = portfolio_manager.get_ai_portfolio(ai.id)
            positions = portfolio.get('positions', [])
            user_prompt = self.prompt_builder.build_user_prompt(ai, quotes, positions)

            # 2. 构建完整Prompt
            full_prompt = self.prompt_builder.build_full_prompt(
                ai.system_prompt,
                user_prompt
            )

            # 3. 获取LLM适配器
            adapter = self._get_adapter(ai.model_type, ai.name)
            if not adapter:
                logger.error(f"无法获取适配器: {ai.model_type}")
                return

            # 4. 调用LLM
            messages = [
                {"role": "system", "content": full_prompt["system"]},
                {"role": "user", "content": full_prompt["user"]}
            ]

            llm_result = adapter.call_api(
                messages=messages,
                temperature=ai.temperature,
                timeout=30
            )

            if not llm_result["success"]:
                logger.error(f"LLM调用失败: {llm_result['error']}")
                return

            # 5. 解析决策
            parse_result = self.decision_parser.parse(llm_result["response"])

            if not parse_result["success"]:
                logger.error(f"决策解析失败: {parse_result['error']}")
                return

            # 6. 生成订单
            orders = []
            if parse_result["actions"]:
                order_manager = OrderManager(db, self.trading_rules)
                orders = order_manager.create_orders_from_decision(
                    ai.id, parse_result["actions"]
                )

            # 7. 保存决策日志
            decision_log = DecisionLog(
                ai_id=ai.id,
                timestamp=datetime.now(),
                market_data=self._serialize_quotes(quotes),
                portfolio_data=self._serialize_positions(positions),
                llm_prompt=full_prompt["system"] + "\n\n" + full_prompt["user"],
                llm_response=llm_result["response"],
                parsed_decision={
                    "reasoning": parse_result["reasoning"],
                    "actions": parse_result["actions"]
                },
                orders_generated=self._serialize_orders(orders),
                execution_result={"status": "success", "orders_created": len(orders)},
                latency_ms=llm_result["latency_ms"],
                tokens_used=llm_result.get("tokens_used"),
                error=None
            )

            db.add(decision_log)

            decision_time = time.time() - decision_start
            logger.info(f"AI {ai.name} 决策完成 - 耗时: {decision_time:.2f}s, 订单: {len(orders)}")

            # 立即推送决策更新
            self._broadcast_decision_update(ai, decision_log)

        except Exception as e:
            logger.error(f"处理AI {ai.name} 决策异常: {str(e)}")

            # 记录错误决策日志
            try:
                error_log = DecisionLog(
                    ai_id=ai.id,
                    timestamp=datetime.now(),
                    market_data=self._serialize_quotes(quotes),
                    portfolio_data="{}",
                    llm_prompt="",
                    llm_response="",
                    parsed_decision={},
                    orders_generated=[],
                    execution_result={"status": "error"},
                    latency_ms=int((time.time() - decision_start) * 1000),
                    tokens_used=None,
                    error=str(e)
                )
                db.add(error_log)
            except:
                pass

    def _get_adapter(self, ai_name: str):
        """
        获取或创建适配器实例

        Args:
            ai_name: AI名称

        Returns:
            适配器实例
        """
        cache_key = ai_name

        if cache_key in self.adapters_cache:
            return self.adapters_cache[cache_key]

        adapter = LLMAdapterFactory.create_adapter(ai_name)
        if adapter:
            self.adapters_cache[cache_key] = adapter

        return adapter

    def _save_portfolio_snapshots(self, db: Session):
        """保存所有AI的组合快照"""
        try:
            ais = db.query(AI).filter(AI.is_active == True).all()

            for ai in ais:
                portfolio_manager = PortfolioManager(db, self.trading_rules)
                portfolio = portfolio_manager.get_ai_portfolio(ai.id)
                positions = portfolio.get('positions', [])
                positions_data = self._serialize_positions(positions)

                snapshot = PortfolioSnapshot(
                    ai_id=ai.id,
                    timestamp=datetime.now(),
                    cash=ai.current_cash,
                    total_assets=ai.total_assets,
                    positions=positions_data
                )

                db.add(snapshot)

        except Exception as e:
            logger.error(f"保存组合快照失败: {str(e)}")

    def _serialize_quotes(self, quotes: List) -> str:
        """序列化行情数据"""
        return str([{
            "code": q.code,
            "name": q.name,
            "price": q.price,
            "change_percent": q.change_percent
        } for q in quotes])

    def _serialize_positions(self, positions: List) -> str:
        """序列化持仓数据"""
        return str([{
            "stock_code": p.stock_code,
            "quantity": p.quantity,
            "avg_cost": p.avg_cost,
            "current_price": p.current_price,
            "profit_rate": p.profit_rate
        } for p in positions])

    def _serialize_orders(self, orders: List) -> str:
        """序列化订单数据"""
        return str([{
            "stock_code": o.stock_code,
            "order_type": o.order_type,
            "quantity": o.quantity,
            "price": o.price,
            "status": o.status
        } for o in orders])

    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "cached_adapters": len(self.adapters_cache),
            "active_adapters": list(self.adapters_cache.keys())
        }

    def _broadcast_decision_update(self, ai: AI, decision_log: DecisionLog):
        """广播AI决策更新"""
        if not manager:
            return

        try:
            # 构建推送数据
            import json
            parsed_decision = json.loads(decision_log.parsed_decision) if isinstance(decision_log.parsed_decision, str) else decision_log.parsed_decision

            chat_data = {
                'ai_id': ai.id,
                'ai_name': ai.name,
                'chats': [{
                    'id': decision_log.id,
                    'timestamp': decision_log.timestamp.isoformat(),
                    'reasoning': parsed_decision.get('reasoning', '无推理信息'),
                    'actions': parsed_decision.get('actions', []),
                    'latency_ms': decision_log.latency_ms,
                    'tokens_used': decision_log.tokens_used,
                    'error': decision_log.error
                }]
            }

            # 广播决策更新
            import asyncio
            asyncio.create_task(manager.broadcast({
                "type": "chats_update",
                "data": {
                    "timestamp": decision_log.timestamp.isoformat(),
                    "chats": [chat_data]
                }
            }))

            logger.info(f"广播AI {ai.name} 决策更新")

        except Exception as e:
            logger.error(f"Failed to broadcast decision update: {str(e)}")