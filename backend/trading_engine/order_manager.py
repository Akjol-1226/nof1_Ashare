"""
订单管理器
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime
import logging

from models.models import Order, AI, Transaction
from rules.trading_rules import TradingRules
from typing import List

logger = logging.getLogger(__name__)


class OrderManager:
    """订单管理器"""
    
    def __init__(self, db: Session, trading_rules: TradingRules):
        """
        初始化
        
        Args:
            db: 数据库会话
            trading_rules: 交易规则引擎
        """
        self.db = db
        self.trading_rules = trading_rules
        logger.info("OrderManager initialized")
    
    def create_order(
        self,
        ai_id: int,
        stock_code: str,
        stock_name: str,
        direction: str,
        order_type: str,
        quantity: int,
        price: Optional[float] = None
    ) -> Optional[Order]:
        """
        创建订单
        
        Args:
            ai_id: AI ID
            stock_code: 股票代码
            stock_name: 股票名称
            direction: 交易方向 (buy/sell)
            order_type: 订单类型 (market/limit)
            quantity: 数量
            price: 价格（限价单需要）
            
        Returns:
            创建的订单对象，失败返回None
        """
        # 验证订单基本信息
        is_valid, msg = self.trading_rules.validate_lot_size(quantity)
        if not is_valid:
            logger.warning(f"Invalid order: {msg}")
            return None
        
        if order_type == 'limit' and price is None:
            logger.warning("Limit order requires price")
            return None
        
        # 创建订单
        order = Order(
            ai_id=ai_id,
            stock_code=stock_code,
            stock_name=stock_name,
            direction=direction,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status='pending',
            created_at=datetime.now()
        )
        
        self.db.add(order)
        self.db.commit()
        
        logger.info(f"Created order: AI {ai_id}, {direction} {quantity} {stock_code} @ {price if price else 'market'}")
        return order
    
    def get_order(self, order_id: int) -> Optional[Order]:
        """
        获取订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单对象
        """
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_pending_orders(self, ai_id: Optional[int] = None):
        """
        获取待处理订单
        
        Args:
            ai_id: AI ID，为None则获取所有AI的订单
            
        Returns:
            订单列表
        """
        query = self.db.query(Order).filter(Order.status == 'pending')
        if ai_id is not None:
            query = query.filter(Order.ai_id == ai_id)
        return query.all()
    
    def update_order_filled(
        self,
        order_id: int,
        filled_price: float,
        filled_quantity: int
    ):
        """
        更新订单为已成交
        
        Args:
            order_id: 订单ID
            filled_price: 成交价格
            filled_quantity: 成交数量
        """
        order = self.get_order(order_id)
        if not order:
            return
        
        order.status = 'filled'
        order.filled_price = filled_price
        order.filled_quantity = filled_quantity
        order.filled_at = datetime.now()
        
        self.db.commit()
        logger.info(f"Order {order_id} filled: {filled_quantity} @ {filled_price}")
    
    def update_order_rejected(self, order_id: int, reason: str):
        """
        更新订单为已拒绝
        
        Args:
            order_id: 订单ID
            reason: 拒绝原因
        """
        order = self.get_order(order_id)
        if not order:
            return
        
        order.status = 'rejected'
        self.db.commit()
        logger.info(f"Order {order_id} rejected: {reason}")
    
    def cancel_order(self, order_id: int):
        """
        取消订单
        
        Args:
            order_id: 订单ID
        """
        order = self.get_order(order_id)
        if not order:
            return
        
        if order.status == 'pending':
            order.status = 'cancelled'
            self.db.commit()
            logger.info(f"Order {order_id} cancelled")

    def create_orders_from_decision(self, ai_id: int, actions: List[Dict]) -> List[Order]:
        """
        根据AI决策创建订单列表

        Args:
            ai_id: AI ID
            actions: 决策动作列表，每个动作包含:
                {
                    "action": "buy" | "sell",
                    "stock_code": "000063",
                    "quantity": 100,
                    "price_type": "market",
                    "reason": "原因"
                }

        Returns:
            创建的订单列表（只返回成功的订单）
        """
        orders = []

        for action in actions:
            try:
                # 验证动作格式
                if not self._validate_action(action):
                    logger.warning(f"无效动作格式: {action}")
                    continue

                # 获取股票名称（这里简化，从action中获取或使用默认）
                stock_name = action.get('stock_name', action['stock_code'])

                # 创建订单
                order = self.create_order(
                    ai_id=ai_id,
                    stock_code=action['stock_code'],
                    stock_name=stock_name,
                    direction=action['action'],
                    order_type=action.get('price_type', 'market'),
                    quantity=action['quantity'],
                    price=None if action.get('price_type') == 'market' else action.get('price')
                )

                if order:
                    orders.append(order)
                    logger.info(f"为AI {ai_id} 创建订单: {action['action']} {action['stock_code']} {action['quantity']}股")
                else:
                    logger.warning(f"为AI {ai_id} 创建订单失败: {action}")

            except Exception as e:
                logger.error(f"处理动作异常: {action}, 错误: {str(e)}")
                continue

        logger.info(f"为AI {ai_id} 共创建 {len(orders)} 个订单")
        return orders

    def _validate_action(self, action: Dict) -> bool:
        """
        验证动作格式

        Args:
            action: 动作字典

        Returns:
            是否有效
        """
        required_fields = ['action', 'stock_code', 'quantity']

        # 检查必需字段
        for field in required_fields:
            if field not in action:
                logger.error(f"动作缺少字段: {field}")
                return False

        # 验证action
        if action['action'] not in ['buy', 'sell']:
            logger.error(f"无效的action: {action['action']}")
            return False

        # 验证stock_code
        if not isinstance(action['stock_code'], str) or len(action['stock_code']) != 6:
            logger.error(f"无效的stock_code: {action['stock_code']}")
            return False

        # 验证quantity
        if not isinstance(action['quantity'], int) or action['quantity'] <= 0:
            logger.error(f"无效的quantity: {action['quantity']}")
            return False

        if action['quantity'] % 100 != 0:
            logger.error(f"quantity必须是100的倍数: {action['quantity']}")
            return False

        return True

    def get_ai_orders(self, ai_id: int, limit: int = 100) -> list:
        """
        获取AI的历史订单
        
        Args:
            ai_id: AI ID
            limit: 返回数量限制
            
        Returns:
            订单列表
        """
        return self.db.query(Order).filter(
            Order.ai_id == ai_id
        ).order_by(Order.created_at.desc()).limit(limit).all()


