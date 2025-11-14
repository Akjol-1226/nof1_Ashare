"""
持仓管理器
处理持仓更新、资金检查、可卖数量计算等
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging

from models.models import AI, Position, Transaction
from rules.trading_rules import TradingRules

logger = logging.getLogger(__name__)


class PortfolioManager:
    """持仓管理器"""
    
    def __init__(self, db: Session, trading_rules: TradingRules):
        """
        初始化
        
        Args:
            db: 数据库会话
            trading_rules: 交易规则引擎
        """
        self.db = db
        self.trading_rules = trading_rules
        logger.info("PortfolioManager initialized")
    
    def get_ai_portfolio(self, ai_id: int) -> Dict:
        """
        获取AI的完整持仓信息
        
        Args:
            ai_id: AI ID
            
        Returns:
            持仓信息字典
        """
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        if not ai:
            return {}
        
        positions = self.db.query(Position).filter(Position.ai_id == ai_id).all()
        
        # 计算总收益和收益率
        total_profit = ai.total_profit
        initial_cash = 100000.0  # 假设初始资金为10万
        profit_rate = (total_profit / initial_cash) * 100 if initial_cash > 0 else 0.0

        return {
            'ai_id': ai.id,
            'ai_name': ai.name,
            'cash': ai.current_cash,
            'total_assets': ai.total_assets,
            'total_profit': total_profit,
            'profit_rate': profit_rate,
            'positions': [self._position_to_dict(pos) for pos in positions]
        }
    
    def _position_to_dict(self, position: Position) -> Dict:
        """将Position对象转换为字典"""
        return {
            'stock_code': position.stock_code,
            'stock_name': position.stock_name,
            'quantity': position.quantity,
            'available_quantity': position.available_quantity,
            'cost_price': position.avg_cost,  # 兼容性字段名
            'avg_cost': position.avg_cost,
            'current_price': position.current_price,
            'market_value': position.market_value,
            'profit_loss': position.profit,
            'profit_loss_percent': position.profit_rate
        }
    
    def check_available_cash(self, ai_id: int, required_amount: float) -> Tuple[bool, float]:
        """
        检查可用资金
        
        Args:
            ai_id: AI ID
            required_amount: 需要的资金
            
        Returns:
            (是否足够, 可用资金)
        """
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        if not ai:
            return False, 0.0
        
        available = ai.current_cash
        return available >= required_amount, available
    
    def check_sellable_quantity(
        self, 
        ai_id: int, 
        stock_code: str,
        required_quantity: int
    ) -> Tuple[bool, int]:
        """
        检查可卖数量（考虑T+1规则）
        
        Args:
            ai_id: AI ID
            stock_code: 股票代码
            required_quantity: 需要的数量
            
        Returns:
            (是否足够, 可卖数量)
        """
        position = self.db.query(Position).filter(
            Position.ai_id == ai_id,
            Position.stock_code == stock_code
        ).first()
        
        if not position:
            return False, 0
        
        available = position.available_quantity
        return available >= required_quantity, available
    
    def update_position_on_buy(
        self,
        ai_id: int,
        stock_code: str,
        stock_name: str,
        price: float,
        quantity: int,
        fee: float
    ):
        """
        买入时更新持仓
        
        Args:
            ai_id: AI ID
            stock_code: 股票代码
            stock_name: 股票名称
            price: 买入价格
            quantity: 买入数量
            fee: 手续费
        """
        # 查找或创建持仓
        position = self.db.query(Position).filter(
            Position.ai_id == ai_id,
            Position.stock_code == stock_code
        ).first()
        
        if position:
            # 更新现有持仓（计算新的成本价）
            total_cost = position.avg_cost * position.quantity + price * quantity + fee
            new_quantity = position.quantity + quantity
            position.avg_cost = total_cost / new_quantity
            position.quantity = new_quantity
            # 注意：买入当日不能卖出（T+1），所以不增加available_quantity
            position.current_price = price
        else:
            # 创建新持仓
            position = Position(
                ai_id=ai_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                available_quantity=0,  # T+1，当日买入不可卖
                avg_cost=(price * quantity + fee) / quantity,
                current_price=price
            )
            self.db.add(position)
        
        # 更新AI的现金
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        ai.current_cash -= (price * quantity + fee)
        
        self.db.commit()
        logger.info(f"AI {ai_id} bought {quantity} shares of {stock_code} at {price}")
    
    def update_position_on_sell(
        self,
        ai_id: int,
        stock_code: str,
        price: float,
        quantity: int,
        fee: float
    ):
        """
        卖出时更新持仓
        
        Args:
            ai_id: AI ID
            stock_code: 股票代码
            price: 卖出价格
            quantity: 卖出数量
            fee: 手续费
        """
        position = self.db.query(Position).filter(
            Position.ai_id == ai_id,
            Position.stock_code == stock_code
        ).first()
        
        if not position:
            logger.error(f"Position not found for AI {ai_id} stock {stock_code}")
            return
        
        # 更新持仓数量
        position.quantity -= quantity
        position.available_quantity -= quantity
        position.current_price = price
        
        # 如果持仓清零，删除记录
        if position.quantity == 0:
            self.db.delete(position)
        
        # 更新AI的现金
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        ai.current_cash += (price * quantity - fee)
        
        self.db.commit()
        logger.info(f"AI {ai_id} sold {quantity} shares of {stock_code} at {price}")
    
    def update_available_quantity_daily(self, ai_id: int):
        """
        每日更新可卖数量（T+1结算）
        
        在每个交易日开盘前调用，将前一日买入的股票变为可卖
        
        Args:
            ai_id: AI ID
        """
        positions = self.db.query(Position).filter(Position.ai_id == ai_id).all()
        
        for position in positions:
            # 将所有持仓变为可卖（前一日买入的已经过了T+1）
            position.available_quantity = position.quantity
        
        self.db.commit()
        logger.info(f"Updated available quantity for AI {ai_id}")
    
    def update_market_value(
        self,
        ai_id: int,
        stock_prices: Dict[str, float]
    ):
        """
        更新持仓市值和盈亏
        
        Args:
            ai_id: AI ID
            stock_prices: 股票代码到当前价格的映射
        """
        positions = self.db.query(Position).filter(Position.ai_id == ai_id).all()
        
        total_market_value = 0.0
        
        for position in positions:
            if position.stock_code in stock_prices:
                current_price = stock_prices[position.stock_code]
                position.current_price = current_price
                position.market_value = current_price * position.quantity
                position.profit_loss = position.market_value - position.cost_price * position.quantity
                
                if position.cost_price > 0:
                    position.profit_loss_percent = (position.profit_loss / (position.cost_price * position.quantity)) * 100
                
                total_market_value += position.market_value
        
        # 更新AI的总资产
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        ai.total_assets = ai.current_cash + total_market_value
        
        self.db.commit()
    
    def get_portfolio_snapshot(self, ai_id: int) -> Dict:
        """
        获取持仓快照（用于记录和展示）
        
        Args:
            ai_id: AI ID
            
        Returns:
            快照数据
        """
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        if not ai:
            return {}
        
        positions = self.db.query(Position).filter(Position.ai_id == ai_id).all()
        
        market_value = sum(p.market_value for p in positions)
        total_profit_loss = ai.total_assets - ai.initial_cash
        total_return = (total_profit_loss / ai.initial_cash) * 100 if ai.initial_cash > 0 else 0
        
        return {
            'ai_id': ai.id,
            'ai_name': ai.name,
            'timestamp': datetime.now().isoformat(),
            'cash': ai.current_cash,
            'market_value': market_value,
            'total_assets': ai.total_assets,
            'total_profit_loss': total_profit_loss,
            'total_return': total_return,
            'positions': [self._position_to_dict(p) for p in positions]
        }
    
    def calculate_profit(self, ai_id: int) -> Tuple[float, float]:
        """
        计算收益率
        
        Args:
            ai_id: AI ID
            
        Returns:
            (总盈亏金额, 收益率百分比)
        """
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        if not ai:
            return 0.0, 0.0
        
        profit = ai.total_assets - ai.initial_cash
        return_rate = (profit / ai.initial_cash) * 100 if ai.initial_cash > 0 else 0.0
        
        return profit, return_rate


