"""
AI调度器
管理AI决策流程的定时调度和执行
重构版：分离行情更新、AI决策、订单撮合为三个独立任务
"""

import asyncio
import logging
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from database import get_db_session
from models.models import AI, DecisionLog, PortfolioSnapshot, Order
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
from trading_engine.matching_engine import MatchingEngine
from portfolio.portfolio_manager import PortfolioManager
from rules.trading_rules import TradingRules

logger = logging.getLogger(__name__)


class AIScheduler:
    """AI决策调度器（重构版）
    
    三个独立的定时任务：
    1. 行情更新任务（15秒）：获取并缓存最新行情
    2. AI决策任务（30分钟）：调用LLM生成交易决策
    3. 订单撮合任务（15秒）：处理所有pending订单
    """

    def __init__(
        self, 
        db=None, 
        data_client=None, 
        portfolio_manager=None, 
        order_manager=None,
        matching_engine=None,
        trading_rules=None, 
        market_update_interval=15,      # 行情更新间隔：15秒
        decision_interval=1800,          # AI决策间隔：30分钟 = 1800秒
        matching_interval=15,            # 订单撮合间隔：15秒
        llm_timeout=30,
        force_run=False                  # 强制运行（忽略交易时间检查，用于测试）
    ):
        self.db = db
        self.is_running = False
        self.data_client = data_client or AKShareClient()
        self.prompt_builder = PromptBuilder()
        self.decision_parser = DecisionParser()
        self.trading_rules = trading_rules or TradingRules()
        self.order_manager = order_manager
        self.portfolio_manager = portfolio_manager
        self.matching_engine = matching_engine
        
        # 时间间隔配置
        self.market_update_interval = market_update_interval
        self.decision_interval = decision_interval
        self.matching_interval = matching_interval
        self.llm_timeout = llm_timeout
        self.force_run = force_run  # 强制运行开关

        # 缓存适配器实例
        self.adapters_cache = {}

        # 三个独立的线程
        self.market_thread = None
        self.decision_thread = None
        self.matching_thread = None
        
        # 共享数据：最新行情缓存
        self.latest_quotes = []
        self.quotes_lock = threading.Lock()

    def _is_trading_time(self) -> bool:
        """检查当前是否在交易时间
        
        Returns:
            True: 在交易时间内
            False: 不在交易时间内
        """
        if self.force_run:
            return True  # 强制运行模式，忽略交易时间检查
        
        return self.trading_rules.check_trading_time()
    
    def _get_next_trading_time_info(self) -> str:
        """获取下一个交易时段的信息（用于日志）"""
        from datetime import datetime, time
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        # 周末
        if weekday >= 5:
            days_until_monday = 7 - weekday
            return f"周末休市，{days_until_monday}天后（周一 09:30）开市"
        
        # 工作日
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)
        
        if current_time < morning_start:
            return f"盘前，今日 09:30 开市"
        elif morning_start <= current_time <= morning_end:
            return "上午交易时段"
        elif morning_end < current_time < afternoon_start:
            return "午休，13:00 继续交易"
        elif afternoon_start <= current_time <= afternoon_end:
            return "下午交易时段"
        else:
            return "已收盘，明日 09:30 开市"
    
    def start(self):
        """启动调度器（启动三个独立任务）"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return

        self.is_running = True
        logger.info("=" * 60)
        logger.info("🚀 AI调度器启动（重构版 - 三任务分离）")
        if self.force_run:
            logger.warning("⚠️  强制运行模式：已禁用交易时间检查")
        else:
            logger.info(f"⏰ 交易时间检查：已启用（仅在A股开市时运行）")
            logger.info(f"📅 当前状态：{self._get_next_trading_time_info()}")
        logger.info("=" * 60)
        
        # 先立即执行一次行情更新（初始化数据）
        print("📊 初始化：获取初始行情数据...")
        try:
            self._update_market_data()
            print(f"✅ 初始行情获取成功：{len(self.latest_quotes)} 只股票")
        except Exception as e:
            print(f"⚠️  初始行情获取失败: {e}")
        
        # 启动三个独立线程
        self.market_thread = threading.Thread(
            target=self._market_update_loop,
            name="MarketUpdateThread",
            daemon=True
        )
        self.decision_thread = threading.Thread(
            target=self._ai_decision_loop,
            name="AIDecisionThread",
            daemon=True
        )
        self.matching_thread = threading.Thread(
            target=self._order_matching_loop,
            name="OrderMatchingThread",
            daemon=True
        )
        
        self.market_thread.start()
        self.decision_thread.start()
        self.matching_thread.start()
        
        logger.info(f"✅ 行情更新线程已启动（间隔 {self.market_update_interval}秒）")
        logger.info(f"✅ AI决策线程已启动（间隔 {self.decision_interval}秒 = {self.decision_interval//60}分钟）")
        logger.info(f"✅ 订单撮合线程已启动（间隔 {self.matching_interval}秒）")
        logger.info("=" * 60)
        
        print(f"🟢 行情更新线程：每 {self.market_update_interval} 秒更新一次")
        print(f"🤖 AI决策线程：每 {self.decision_interval//60} 分钟决策一次")
        print(f"💹 订单撮合线程：每 {self.matching_interval} 秒撮合一次")

    def stop(self):
        """停止调度器（停止所有三个任务）"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("AI调度器正在停止...")

        # 等待所有线程结束
        threads = [
            ("行情更新", self.market_thread),
            ("AI决策", self.decision_thread),
            ("订单撮合", self.matching_thread)
        ]
        
        for name, thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"{name}线程已停止")

        logger.info("AI调度器已完全停止")

    # ==================== 任务1：行情更新（15秒） ====================
    
    def _market_update_loop(self):
        """行情更新任务循环（15秒一次，闭市时暂停）"""
        logger.info("📊 行情更新任务已启动")
        
        while self.is_running:
            try:
                # 检查是否在交易时间
                if not self._is_trading_time():
                    if not hasattr(self, '_market_last_pause_log') or \
                       time.time() - self._market_last_pause_log > 3600:  # 每小时只记录一次
                        logger.info(f"📊 行情更新暂停（{self._get_next_trading_time_info()}）")
                        self._market_last_pause_log = time.time()
                    time.sleep(60)  # 闭市时每分钟检查一次
                    continue
                
                start_time = time.time()
                self._update_market_data()
                elapsed = time.time() - start_time
                
                logger.debug(f"行情更新完成，耗时 {elapsed:.2f}秒")
                
                # 等待下一个周期
                time.sleep(max(0, self.market_update_interval - elapsed))
                
            except Exception as e:
                logger.error(f"行情更新任务异常: {e}")
                time.sleep(5)
        
        logger.info("📊 行情更新任务已停止")
    
    def _update_market_data(self):
        """更新行情数据（存到缓存）并更新所有AI的资产"""
        from stock_config import TRADING_STOCKS
        stock_codes = list(TRADING_STOCKS.keys())
        
        quotes = self.data_client.get_realtime_quotes(stock_codes)
        
        if quotes:
            with self.quotes_lock:
                self.latest_quotes = quotes
            logger.info(f"✅ 行情更新成功：{len(quotes)} 只股票")
            
            # 更新所有AI的持仓市值和总资产
            self._update_all_ai_assets(quotes)
        else:
            logger.warning("⚠️  行情更新失败：未获取到数据")
    
    def _update_all_ai_assets(self, quotes: List):
        """根据最新行情更新所有AI的持仓市值和总资产
        
        Args:
            quotes: 最新行情数据列表
        """
        try:
            # 构建股票代码到价格的映射
            stock_prices = {}
            for quote in quotes:
                stock_prices[quote.code] = quote.price
            
            # 更新每个AI的持仓市值
            with get_db_session() as db:
                ais = db.query(AI).all()
                
                for ai in ais:
                    try:
                        # 使用portfolio_manager更新市值
                        if self.portfolio_manager:
                            # 注意：portfolio_manager的db session可能不同，需要创建新实例
                            from portfolio.portfolio_manager import PortfolioManager
                            temp_pm = PortfolioManager(db, self.trading_rules)
                            temp_pm.update_market_value(ai.id, stock_prices)
                        
                    except Exception as e:
                        logger.error(f"更新AI {ai.id} 资产失败: {e}")
                        continue
                
                logger.debug(f"✅ 已更新 {len(ais)} 个AI的资产数据")
                
                # 更新完资产后，立即保存快照
                self._save_realtime_snapshots(db)
                
        except Exception as e:
            logger.error(f"批量更新AI资产失败: {e}")
    
    def _save_realtime_snapshots(self, db: Session):
        """保存实时快照（行情更新时）"""
        try:
            from models.models import Position
            from datetime import datetime
            
            ais = db.query(AI).all()
            
            for ai in ais:
                try:
                    # 计算当前总资产（现金+持仓市值）
                    total_assets = ai.current_cash
                    positions = db.query(Position).filter(Position.ai_id == ai.id).all()
                    market_value = sum(pos.market_value for pos in positions)
                    total_assets += market_value
                    
                    # 创建快照
                    snapshot = PortfolioSnapshot(
                        ai_id=ai.id,
                        date=datetime.now(),
                        cash=ai.current_cash,
                        market_value=market_value,
                        total_assets=total_assets,
                        daily_profit_loss=0.0,  # 暂不计算日收益
                        daily_return=0.0,
                        total_profit_loss=total_assets - (ai.initial_cash or 100000.0),
                        total_return=((total_assets - (ai.initial_cash or 100000.0)) / (ai.initial_cash or 100000.0)) * 100
                    )
                    db.add(snapshot)
                    
                except Exception as e:
                    logger.error(f"保存AI {ai.name}快照失败: {e}")
                    continue
            
            db.commit()
            logger.debug(f"✅ 已保存 {len(ais)} 个AI的实时快照")
            
        except Exception as e:
            logger.error(f"保存实时快照失败: {e}")
            db.rollback()
    
    # ==================== 任务2：AI决策（30分钟） ====================
    
    def _ai_decision_loop(self):
        """AI决策任务循环（30分钟一次，闭市时暂停）"""
        logger.info("🤖 AI决策任务已启动")
        
        # 首次启动延迟10秒，等待行情数据准备好
        time.sleep(10)
        
        while self.is_running:
            try:
                # 检查是否在交易时间
                if not self._is_trading_time():
                    if not hasattr(self, '_decision_last_pause_log') or \
                       time.time() - self._decision_last_pause_log > 3600:
                        logger.info(f"🤖 AI决策暂停（{self._get_next_trading_time_info()}）")
                        self._decision_last_pause_log = time.time()
                    time.sleep(300)  # 闭市时每5分钟检查一次
                    continue
                
                start_time = time.time()
                self._execute_ai_decisions()
                elapsed = time.time() - start_time
                
                logger.info(f"✅ AI决策周期完成，耗时 {elapsed:.2f}秒")
                
                # 等待下一个周期
                time.sleep(max(0, self.decision_interval - elapsed))
                
            except Exception as e:
                logger.error(f"AI决策任务异常: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # 出错后等待1分钟
        
        logger.info("🤖 AI决策任务已停止")
    
    def _execute_ai_decisions(self):
        """执行所有AI的决策"""
        logger.info("=" * 60)
        logger.info("🤖 开始AI决策周期")
        logger.info("=" * 60)
        
        # 获取当前行情（从缓存）
        with self.quotes_lock:
            quotes = self.latest_quotes.copy()
        
        if not quotes:
            logger.warning("⚠️  无行情数据，跳过本次决策")
            return
        
        # 获取所有激活的AI
        with get_db_session() as db:
            active_ais = db.query(AI).filter(AI.is_active == True).all()
            logger.info(f"📋 找到 {len(active_ais)} 个激活的AI")
            
            for ai in active_ais:
                try:
                    logger.info(f"🤖 处理 AI: {ai.name}")
                    self._process_single_ai_decision(ai, quotes, db)
                except Exception as e:
                    logger.error(f"❌ AI {ai.name} 决策失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 保存资产快照
            self._save_portfolio_snapshots_sync(db)
        
        logger.info("=" * 60)
    
    # ==================== 任务3：订单撮合（15秒） ====================
    
    def _order_matching_loop(self):
        """订单撮合任务循环（15秒一次，闭市时暂停）"""
        logger.info("💹 订单撮合任务已启动")
        
        # 首次启动延迟5秒
        time.sleep(5)
        
        while self.is_running:
            try:
                # 检查是否在交易时间
                if not self._is_trading_time():
                    if not hasattr(self, '_matching_last_pause_log') or \
                       time.time() - self._matching_last_pause_log > 3600:
                        logger.info(f"💹 订单撮合暂停（{self._get_next_trading_time_info()}）")
                        self._matching_last_pause_log = time.time()
                    time.sleep(60)  # 闭市时每分钟检查一次
                    continue
                
                start_time = time.time()
                matched_count = self._match_pending_orders()
                elapsed = time.time() - start_time
                
                if matched_count > 0:
                    logger.info(f"✅ 撮合完成：{matched_count} 个订单，耗时 {elapsed:.2f}秒")
                
                # 等待下一个周期
                time.sleep(max(0, self.matching_interval - elapsed))
                
            except Exception as e:
                logger.error(f"订单撮合任务异常: {e}")
                time.sleep(5)
        
        logger.info("💹 订单撮合任务已停止")
    
    def _match_pending_orders(self) -> int:
        """撮合所有pending状态的订单
        
        Returns:
            撮合成功的订单数量
        """
        if not self.matching_engine:
            logger.warning("⚠️  撮合引擎未初始化")
            return 0
        
        matched_count = 0
        
        with get_db_session() as db:
            # 查询所有pending订单
            pending_orders = db.query(Order).filter(Order.status == 'pending').all()
            
            if not pending_orders:
                return 0
            
            logger.debug(f"📋 发现 {len(pending_orders)} 个待撮合订单")
            
            for order in pending_orders:
                try:
                    # 创建临时撮合引擎实例（使用当前db session）
                    from trading_engine.matching_engine import MatchingEngine
                    temp_matching_engine = MatchingEngine(
                        db, 
                        self.trading_rules,
                        self.portfolio_manager,
                        self.data_client
                    )
                    
                    success, message = temp_matching_engine.match_order(order)
                    
                    if success:
                        matched_count += 1
                        logger.info(f"✅ 订单 #{order.id} 撮合成功: {order.direction} {order.quantity} {order.stock_code}")
                    else:
                        logger.debug(f"订单 #{order.id} 暂未撮合: {message}")
                        
                except Exception as e:
                    logger.error(f"❌ 订单 #{order.id} 撮合异常: {e}")
        
        return matched_count
    
    # ==================== 旧版方法（保留兼容） ====================
    
    def _run_schedule_loop(self):
        """运行调度循环（线程版本）"""
        logger.info("调度循环线程已启动")
        print("🧵 调度循环线程已启动")

        # 立即执行一次测试决策周期
        print("🧪 线程中立即执行测试决策周期...")
        try:
            self._execute_decision_cycle_sync()
            print("✅ 线程中测试决策周期执行成功")
        except Exception as e:
            print(f"❌ 线程中测试决策周期执行失败: {e}")
            import traceback
            traceback.print_exc()

        while self.is_running:
            try:
                print(f"🔄 准备执行决策周期 - {time.strftime('%H:%M:%S')}")

                # 直接执行同步版本的决策周期
                print("⚙️ 执行决策周期...")
                self._execute_decision_cycle_sync()
                print("✅ 决策周期完成")

                print(f"⏰ 等待{self.decision_interval}秒...")
                # 等待下一个周期
                time.sleep(self.decision_interval)

            except Exception as e:
                print(f"❌ 调度循环异常: {str(e)}")
                logger.error(f"调度循环异常: {str(e)}")
                time.sleep(5)  # 出错后等待5秒再试

        print("🛑 调度循环线程已结束")
        logger.info("调度循环线程已结束")

    def _execute_decision_cycle_sync(self):
        """同步版本的决策周期执行"""
        cycle_start = time.time()

        try:
            logger.info("=== 开始AI决策周期（同步版本） ===")
            print(f"🔄 AI决策周期开始执行（同步） - {time.strftime('%H:%M:%S')}")

            # 1. 获取实时行情
            print("📊 正在获取实时行情数据...")
            quotes = self.data_client.get_realtime_quotes()
            if not quotes:
                print("❌ 无法获取实时行情，跳过本次周期")
                logger.warning("无法获取实时行情，跳过本次周期")
                return

            print(f"✅ 获取到 {len(quotes)} 只股票的行情数据")
            logger.info(f"获取到 {len(quotes)} 只股票的行情数据")

            print("🔍 开始遍历AI...")
            # 2. 遍历所有激活的AI
            with get_db_session() as db:
                active_ais = db.query(AI).filter(AI.is_active == True).all()
                print(f"📋 找到 {len(active_ais)} 个激活的AI")

                for ai in active_ais:
                    try:
                        print(f"🤖 开始处理AI {ai.name}的决策...")
                        self._process_ai_decision_sync(ai, quotes, db)
                        print(f"✅ AI {ai.name}决策处理完成")
                    except Exception as e:
                        print(f"❌ 处理AI {ai.name}决策失败: {str(e)}")
                        logger.error(f"处理AI {ai.name} 决策失败: {str(e)}")
                        continue

            # 3. 保存组合快照（每次决策周期都保存）
            self._save_portfolio_snapshots_sync(db)

            cycle_time = time.time() - cycle_start
            print(f"🎯 决策周期完成，耗时: {cycle_time:.2f}秒")
            logger.info(f"决策周期完成，耗时: {cycle_time:.2f}秒")

        except Exception as e:
            print(f"❌ 决策周期执行失败: {str(e)}")
            logger.error(f"决策周期执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e  # 重新抛出异常，让调用方知道失败了

    def _process_single_ai_decision(self, ai: AI, quotes: List, db: Session):
        """处理单个AI的决策（包含历史K线数据）"""
        decision_start = time.time()

        try:
            # 🔄 刷新AI对象，确保获取最新的现金余额（防止使用旧缓存数据）
            db.refresh(ai)
            logger.debug(f"🔄 刷新AI对象: {ai.name}, 当前现金: ¥{ai.current_cash:,.2f}")
            
            # [Fix] 在获取持仓前，先执行T+1结算检查
            # 确保如果过了T+1，持仓状态是"可卖"
            try:
                from portfolio.portfolio_manager import PortfolioManager
                temp_pm = PortfolioManager(db, self.trading_rules)
                temp_pm.update_available_quantity_daily(ai.id)
            except Exception as e:
                logger.error(f"执行T+1结算失败: {e}")

            # 1. 获取持仓信息
            from models.models import Position
            positions = db.query(Position).filter(Position.ai_id == ai.id).all()
            
            # 2. 获取所有可交易股票的近5日K线数据
            logger.info(f"📊 获取历史K线数据...")
            historical_klines = {}
            from stock_config import TRADING_STOCKS
            
            for stock_code in TRADING_STOCKS.keys():
                klines = self.data_client.get_historical_klines(
                    stock_code=stock_code,
                    interval='d',     # 日线
                    adjust='n',       # 不复权
                    days=5            # 最近5天
                )
                if klines:
                    historical_klines[stock_code] = klines
            
            logger.info(f"✅ 获取到 {len(historical_klines)} 只股票的历史K线")
            
            # 3. 构建用户提示词（包含历史K线）
            user_prompt = self.prompt_builder.build_user_prompt(
                ai, quotes, positions, historical_klines
            )
            logger.debug(f"📄 用户Prompt长度: {len(user_prompt)} 字符")

            # 4. 构建完整Prompt (现在System Prompt也会在内部自动构建)
            full_prompt = self.prompt_builder.build_full_prompt(user_prompt=user_prompt)
            prompt_text = f"System: {full_prompt['system']}\n\nUser: {full_prompt['user']}"
            
            # 6. 转换为messages格式
            messages = [
                {"role": "system", "content": full_prompt['system']},
                {"role": "user", "content": full_prompt['user']}
            ]

            # 7. 调用LLM
            logger.info(f"🧠 调用LLM进行决策...")
            try:
                adapter = self._get_adapter(ai.name)
                if adapter:
                    llm_result = adapter.call_api(messages, temperature=ai.temperature)
                    llm_response = llm_result.get('response') or ''
                    logger.info(f"📤 LLM响应长度: {len(llm_response)} 字符")
                else:
                    logger.warning("❌ 适配器创建失败")
                    llm_response = '{"reasoning": "适配器创建失败", "actions": []}'
            except Exception as e:
                logger.error(f"❌ LLM调用失败: {str(e)}")
                llm_response = '{"reasoning": "LLM调用失败", "actions": []}'

            # 8. 解析决策
            logger.info(f"🔍 解析LLM响应...")
            logger.info(f"📄 LLM实际响应内容：{llm_response}")
            decision = self.decision_parser.parse(llm_response)
            
            if decision.get('success'):
                actions = decision.get('actions', [])
                logger.info(f"🎯 解析成功: {len(actions)} 个动作")
            else:
                logger.error(f"❌ 解析失败: {decision.get('error')}")
                actions = []

            # 9. 生成订单
            logger.info(f"📋 生成交易订单...")
            try:
                orders = self.order_manager.create_orders_from_decision(ai.id, actions)
                logger.info(f"✅ 生成 {len(orders)} 个订单")
            except Exception as e:
                logger.error(f"❌ 订单生成失败: {str(e)}")
                orders = []

            # 10. 保存决策日志（增强：保存账户快照）
            import json
            
            # 计算当前收益信息
            total_profit_snapshot = ai.total_assets - ai.initial_cash
            profit_rate_snapshot = (total_profit_snapshot / ai.initial_cash * 100) if ai.initial_cash > 0 else 0.0
            
            decision_log = DecisionLog(
                ai_id=ai.id,
                market_data={"quotes_count": len(quotes), "historical_klines": len(historical_klines)},
                portfolio_data={
                    "ai_id": ai.id, 
                    "positions_count": len(positions),
                    # 新增：保存账户快照，用于调试
                    "cash": ai.current_cash,
                    "total_assets": ai.total_assets,
                    "total_profit": total_profit_snapshot,
                    "profit_rate": profit_rate_snapshot
                },
                llm_prompt=prompt_text[:2000],  # 保存前2000字符
                llm_response=llm_response,
                parsed_decision=json.dumps(decision, ensure_ascii=False),
                orders_generated=json.dumps([{
                    "stock_code": o.stock_code, 
                    "direction": o.direction, 
                    "quantity": o.quantity
                } for o in orders], ensure_ascii=False),
                execution_result={"orders_created": len(orders)},
                latency_ms=int((time.time() - decision_start) * 1000),
                tokens_used=len(prompt_text.split()) + len(llm_response.split()),
            )
            db.add(decision_log)
            db.commit()

            logger.info(f"✅ AI {ai.name} 决策处理完成")

        except Exception as e:
            logger.error(f"❌ 处理AI {ai.name} 决策时发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
    
    # ==================== 保留旧版本的方法（兼容性） ====================
    
    def _process_ai_decision_sync(self, ai: AI, quotes: List, db: Session):
        """同步版本的AI决策处理（旧版，已废弃，保留兼容）"""
        # 直接调用新版方法
        self._process_single_ai_decision(ai, quotes, db)

    def _save_portfolio_snapshots_sync(self, db: Session):
        """同步版本的组合快照保存"""
        print("📊 保存组合快照...")
        try:
            from models.models import PortfolioSnapshot, Position
            ais = db.query(AI).all()

            for ai in ais:
                try:
                    # 计算当前总资产
                    total_assets = ai.current_cash
                    positions = db.query(Position).filter(Position.ai_id == ai.id).all()
                    for position in positions:
                        total_assets += position.market_value

                    # 创建快照
                    snapshot = PortfolioSnapshot(
                        ai_id=ai.id,
                        date=datetime.now(),
                        cash=ai.current_cash,
                        market_value=total_assets - ai.current_cash,
                        total_assets=total_assets,
                        daily_profit_loss=0.0,  # 暂时设为0
                        daily_return=0.0,
                        total_profit_loss=total_assets - 100000.0,  # 假设初始资金10万
                        total_return=(total_assets - 100000.0) / 100000.0 * 100
                    )
                    db.add(snapshot)

                except Exception as e:
                    print(f"❌ 保存AI {ai.name}快照失败: {str(e)}")
                    continue

            db.commit()
            print("✅ 组合快照保存完成")

        except Exception as e:
            print(f"❌ 保存组合快照失败: {str(e)}")
            db.rollback()

    async def _schedule_loop(self):
        """调度主循环（异步版本，保留用于兼容性）"""
        while self.is_running:
            try:
                await self._execute_decision_cycle_async()
                await asyncio.sleep(self.decision_interval)

            except Exception as e:
                logger.error(f"调度循环异常: {str(e)}")
                await asyncio.sleep(5)  # 出错后等待5秒再试

    async def _execute_decision_cycle_async(self):
        """执行一次完整的决策周期"""
        cycle_start = time.time()

        try:
            logger.info("=== 开始AI决策周期 ===")
            print(f"🔄 AI决策周期开始执行 - {time.strftime('%H:%M:%S')}")

            # 1. 获取实时行情
            print("📊 正在获取实时行情数据...")
            quotes = self.data_client.get_realtime_quotes()
            if not quotes:
                print("❌ 无法获取实时行情，跳过本次周期")
                logger.warning("无法获取实时行情，跳过本次周期")
                return

            print(f"✅ 获取到 {len(quotes)} 只股票的行情数据")
            logger.info(f"获取到 {len(quotes)} 只股票的行情数据")

            print("🔍 开始遍历AI...")
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
        """
        print(f"🤖 开始处理AI {ai.name}的决策...")
        logger.info(f"开始处理AI {ai.name}的决策")
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
                user_prompt=user_prompt
            )

            # 3. 获取LLM适配器
            adapter = self._get_adapter(ai.model_name, ai.name)
            if not adapter:
                logger.error(f"无法获取适配器: {ai.model_name}")
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