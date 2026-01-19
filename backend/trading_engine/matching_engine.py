"""
撮合引擎
实现订单撮合逻辑（方案A: 简单撮合，预留方案C接口）
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Tuple, Any
from datetime import datetime
import logging

from models.models import Order, Transaction
from rules.trading_rules import TradingRules
from portfolio.portfolio_manager import PortfolioManager
from data_service.akshare_client import AKShareClient

# 导入WebSocket管理器用于广播
try:
    from main import manager
except ImportError:
    manager = None

logger = logging.getLogger(__name__)


class MatchingEngine:
    """撮合引擎"""
    
    def __init__(
        self,
        db: Session,
        trading_rules: TradingRules,
        portfolio_manager: PortfolioManager,
        akshare_client: AKShareClient
    ):
        """
        初始化
        
        Args:
            db: 数据库会话
            trading_rules: 交易规则引擎
            portfolio_manager: 持仓管理器
            akshare_client: AKShare客户端
        """
        self.db = db
        self.trading_rules = trading_rules
        self.portfolio_manager = portfolio_manager
        self.akshare_client = akshare_client
        logger.info("MatchingEngine initialized")
    
    def match_order(self, order: Order) -> Tuple[bool, str]:
        """
        撮合订单（方案A：简单撮合）
        
        Args:
            order: 订单对象
            
        Returns:
            (是否成功, 消息)
        """
        if order.status != 'pending':
            return False, "Order is not pending"
        
        # 对于卖出订单，先检查持仓
        if order.direction == 'sell':
            is_sufficient, available = self.portfolio_manager.check_sellable_quantity(
                order.ai_id, order.stock_code, order.quantity
            )
            if not is_sufficient:
                return False, f"Insufficient sellable quantity (need: {order.quantity}, available: {available})"

        # 获取当前价格
        stock_info = self.akshare_client.get_stock_info(order.stock_code)
        if not stock_info:
            return False, f"Failed to get stock info for {order.stock_code}"

        current_price = stock_info['price']
        yesterday_close = stock_info['close_yesterday']
        
        # 🔒 价格安全检查：防止数据源异常导致0元成交
        if current_price <= 0:
            logger.error(f"❌ Invalid price data: {order.stock_code} price={current_price}")
            return False, f"Invalid market price ({current_price}) for {order.stock_code}"
        if yesterday_close <= 0:
            logger.warning(f"⚠️ Invalid close_yesterday: {order.stock_code} close_yesterday={yesterday_close}")
            # 昨收价可以允许缺失，但要记录告警

        # 优先尝试获取 Biying 五档盘口，用于更真实的撮合；失败则退化为“最新价 vs 委托价”的简单逻辑
        order_book: Optional[Dict[str, Any]] = None
        try:
            if hasattr(self.akshare_client, "get_order_book"):
                order_book = self.akshare_client.get_order_book(order.stock_code)  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to get order book for {order.stock_code}: {e}")
            order_book = None

        # 确定成交价格
        match_price, reason = self._determine_match_price(order, current_price, order_book)
        if match_price is None:
            return False, reason

        # 验证订单合法性（资金、涨跌停等）
        is_valid, msg = self._validate_order_execution(
            order, match_price, yesterday_close
        )
        if not is_valid:
            from trading_engine.order_manager import OrderManager
            order_manager = OrderManager(self.db, self.trading_rules)
            order_manager.update_order_rejected(order.id, msg)
            return False, msg
        
        # 计算手续费
        fee, fee_detail = self.trading_rules.calculate_commission(
            match_price, order.quantity, order.direction
        )
        
        # 执行交易
        success = self._execute_trade(order, match_price, fee, fee_detail)
        
        if success:
            return True, f"Order matched at {match_price}"
        else:
            return False, "Failed to execute trade"
    
    def _validate_order_execution(
        self,
        order: Order,
        price: float,
        yesterday_close: float
    ) -> Tuple[bool, str]:
        """
        验证订单执行的合法性
        
        Args:
            order: 订单
            price: 成交价格
            yesterday_close: 昨日收盘价
            
        Returns:
            (是否合法, 错误信息)
        """
        # 检查涨跌停
        is_limit, upper, lower = self.trading_rules.check_price_limit(
            order.stock_code, price, yesterday_close
        )
        
        if order.direction == 'buy':
            # 买入时检查资金
            fee, _ = self.trading_rules.calculate_commission(price, order.quantity, 'buy')
            total_cost = price * order.quantity + fee
            is_sufficient, available = self.portfolio_manager.check_available_cash(
                order.ai_id, total_cost
            )
            if not is_sufficient:
                return False, f"Insufficient cash (need: {total_cost:.2f}, available: {available:.2f})"
            
            # 检查是否涨停（涨停价买入可能无法成交）
            if price >= upper * 0.9999:  # 允许小幅偏差
                return False, f"Price at upper limit ({upper:.2f})"
        
        else:  # sell
            # 卖出时检查持仓
            is_sufficient, available = self.portfolio_manager.check_sellable_quantity(
                order.ai_id, order.stock_code, order.quantity
            )
            if not is_sufficient:
                return False, f"Insufficient sellable quantity (need: {order.quantity}, available: {available})"
            
            # 检查是否跌停（跌停可能卖不出）
            if price <= lower:
                return False, f"Price at lower limit ({lower:.2f})"
        
        return True, ""

    def _determine_match_price(
        self,
        order: Order,
        current_price: float,
        order_book: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[float], str]:
        """
        根据最新价 + （可选）五档盘口，确定更合理的成交价。
        优先使用盘口撮合；如果没有盘口数据，则退化为“委托价 vs 最新价”的简单撮合。
        """
        # 🔒 第二道防线：确保输入价格有效
        if current_price <= 0:
            logger.error(f"❌ Invalid current_price in _determine_match_price: {current_price}")
            return None, f"Invalid current price: {current_price}"
        
        # 市价单：如果有盘口，用对手盘一档价；否则用最新价
        if order.order_type == "market":
            if order_book:
                asks = order_book.get("ask_prices") or []
                bids = order_book.get("bid_prices") or []

                if order.direction == "buy" and asks:
                    return float(asks[0]), ""
                if order.direction == "sell" and bids:
                    return float(bids[0]), ""

            # 没有盘口或对应一侧为空，退化为按最新价成交
            return float(current_price), ""

        # 限价单：需要 price
        if order.price is None:
            return None, "Limit order requires price"

        limit_price = float(order.price)

        # 如果没有盘口，退化为：当最新价“穿过”委托价时，以最新价成交
        if not order_book:
            if order.direction == "buy":
                if current_price <= limit_price:
                    # 用户愿意以不高于 limit_price 购买，给他当前更好的价格
                    return float(current_price), ""
                return None, f"Limit order price not met (current: {current_price}, limit: {limit_price})"
            else:  # sell
                if current_price >= limit_price:
                    # 用户愿意以不低于 limit_price 卖出，给他当前更好的价格
                    return float(current_price), ""
                return None, f"Limit order price not met (current: {current_price}, limit: {limit_price})"

        # 有盘口时，用五档盘口撮合
        asks = order_book.get("ask_prices") or []
        bids = order_book.get("bid_prices") or []

        best_ask = float(asks[0]) if asks else None
        best_bid = float(bids[0]) if bids else None

        if order.direction == "buy":
            # 买入：如果限价 >= 卖一，认为吃掉卖一，在卖一价成交（不让用户成交价比委托价更差）
            if best_ask is not None and limit_price >= best_ask:
                return best_ask, ""

            # 如果没有卖盘，则退化为简单逻辑
            if best_ask is None:
                if current_price <= limit_price:
                    return float(current_price), ""
                return None, f"Limit order price not met (current: {current_price}, limit: {limit_price})"

            # 限价在买一和卖一之间 / 未触碰卖一：视为挂单，目前模拟撮合不维护订单簿，因此返回未成交
            return None, (
                f"Limit buy not crossed order book "
                f"(bid1: {best_bid}, ask1: {best_ask}, price: {limit_price})"
            )

        else:  # sell
            # 卖出：如果限价 <= 买一，认为打到买一，在买一价成交
            if best_bid is not None and limit_price <= best_bid:
                return best_bid, ""

            # 如果没有买盘，则退化为简单逻辑
            if best_bid is None:
                if current_price >= limit_price:
                    return float(current_price), ""
                return None, f"Limit order price not met (current: {current_price}, limit: {limit_price})"

            # 限价在买一和卖一之间 / 未触碰买一：视为挂单
            return None, (
                f"Limit sell not crossed order book "
                f"(bid1: {best_bid}, ask1: {best_ask}, price: {limit_price})"
            )
    
    def _execute_trade(
        self,
        order: Order,
        price: float,
        fee: float,
        fee_detail: Dict
    ) -> bool:
        """
        执行交易
        
        Args:
            order: 订单
            price: 成交价格
            fee: 总手续费
            fee_detail: 手续费明细
            
        Returns:
            是否成功
        """
        try:
            # 更新订单状态
            from trading_engine.order_manager import OrderManager
            order_manager = OrderManager(self.db, self.trading_rules)
            order_manager.update_order_filled(order.id, price, order.quantity)
            
            # 创建成交记录
            transaction = Transaction(
                ai_id=order.ai_id,
                order_id=order.id,
                stock_code=order.stock_code,
                stock_name=order.stock_name,
                direction=order.direction,
                price=price,
                quantity=order.quantity,
                amount=price * order.quantity,
                commission=fee_detail['commission'],
                stamp_tax=fee_detail['stamp_tax'],
                transfer_fee=fee_detail['transfer_fee'],
                total_fee=fee,
                created_at=datetime.now()
            )
            self.db.add(transaction)
            
            # 更新持仓
            if order.direction == 'buy':
                self.portfolio_manager.update_position_on_buy(
                    order.ai_id,
                    order.stock_code,
                    order.stock_name,
                    price,
                    order.quantity,
                    fee
                )
            else:  # sell
                self.portfolio_manager.update_position_on_sell(
                    order.ai_id,
                    order.stock_code,
                    price,
                    order.quantity,
                    fee
                )
            
            self.db.commit()

            logger.info(
                f"Trade executed: AI {order.ai_id} {order.direction} "
                f"{order.quantity} {order.stock_code} @ {price} (fee: {fee:.2f})"
            )

            # 立即推送交易更新
            self._broadcast_trade_update(order.ai_id)

            return True
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {str(e)}")
            self.db.rollback()
            return False

    def _broadcast_trade_update(self, ai_id: int):
        """广播交易更新"""
        if not manager:
            return

        try:
            # 获取更新后的持仓和订单信息
            from models.models import AI, Order
            ais = self.db.query(AI).all()
            portfolios = []
            orders = []

            for ai in ais:
                portfolio = self.portfolio_manager.get_ai_portfolio(ai.id)
                portfolios.append(portfolio)

                # 获取活跃订单
                ai_orders = self.db.query(Order).filter(
                    Order.ai_id == ai.id,
                    Order.status.in_(['pending', 'filled', 'rejected'])  # 包含被拒绝的订单
                ).order_by(Order.created_at.desc()).limit(10).all()

                orders.extend([{
                    'id': order.id,
                    'ai_id': order.ai_id,
                    'ai_name': ai.name,
                    'stock_code': order.stock_code,
                    'stock_name': order.stock_name,
                    'direction': order.direction,
                    'quantity': order.quantity,
                    'price': order.price,
                    'status': order.status,
                    'created_at': order.created_at.isoformat()
                } for order in ai_orders])

            # 广播更新
            import asyncio
            asyncio.create_task(manager.broadcast({
                "type": "trading_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "portfolios": portfolios,
                    "orders": orders,
                    "trigger_ai": ai_id  # 标识哪个AI触发了更新
                }
            }))

        except Exception as e:
            logger.error(f"Failed to broadcast trade update: {str(e)}")

    # ==================== 方案C接口预留 ====================
    
    def match_with_slippage(
        self,
        order: Order,
        slippage_rate: float = 0.001
    ) -> Tuple[bool, str]:
        """
        考虑滑点的撮合（方案C）
        
        滑点：市价单成交价格与下单时价格的偏差
        
        Args:
            order: 订单
            slippage_rate: 滑点率
            
        Returns:
            (是否成功, 消息)
        """
        # TODO: 实现考虑滑点的撮合逻辑
        # 1. 根据市场深度和成交量计算滑点
        # 2. 调整成交价格
        # 3. 执行交易
        logger.warning("Slippage matching not implemented yet (Plan C)")
        return False, "Not implemented"
    
    def match_with_volume_limit(
        self,
        order: Order,
        max_volume_rate: float = 0.01
    ) -> Tuple[bool, str]:
        """
        考虑成交量限制的撮合（方案C）
        
        限制：单笔订单不能超过市场总成交量的一定比例
        
        Args:
            order: 订单
            max_volume_rate: 最大成交量比例
            
        Returns:
            (是否成功, 消息)
        """
        # TODO: 实现考虑成交量限制的撮合逻辑
        # 1. 获取股票的当前成交量
        # 2. 检查订单量是否超过限制
        # 3. 如果超过，部分成交或拒绝
        logger.warning("Volume limit matching not implemented yet (Plan C)")
        return False, "Not implemented"


