"""
撮合引擎
实现订单撮合逻辑（方案A: 简单撮合，预留方案C接口）
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Tuple
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

        # 确定成交价格
        if order.order_type == 'market':
            # 市价单：按当前价成交
            match_price = current_price
        else:
            # 限价单：检查是否满足价格条件
            if order.direction == 'buy' and current_price <= order.price:
                match_price = order.price  # 以限价成交
            elif order.direction == 'sell' and current_price >= order.price:
                match_price = order.price  # 以限价成交
            else:
                return False, f"Limit order price not met (current: {current_price}, limit: {order.price})"

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
                    Order.status.in_(['pending', 'filled'])
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


