"""
持仓管理器
处理持仓更新、资金检查、可卖数量计算等
"""

from sqlalchemy.orm import Session, joinedload
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
        # 使用 joinedload 预加载 positions，确保在一个事务快照中读取 AI 和持仓
        # 解决并发交易时的读写不一致导致资产波动的问题
        ai = self.db.query(AI).options(joinedload(AI.positions)).filter(AI.id == ai_id).first()
        if not ai:
            return {}
        
        # refresh 会导致 joinedload 的 positions 失效并触发懒加载，反而破坏了原子性
        # 所以删除了 refresh
        
        positions = ai.positions
        
        # T+1解锁逻辑（已提取到独立方法）
        self.update_available_quantity_daily(ai.id)
        
        # 刷新位置信息以获取可能的更新
        # 注意：由于update_available_quantity_daily可能修改了DB但未刷新当前session中的对象，
        # 我们最好重新查询或依赖ORM的Identity Map。
        # 这里positions变量关联的对象应该已经被更新了（如果在同一个session中）
            
            
        # 计算总收益和收益率（基于当前总资产）
        # 注意：这里使用 ai.current_cash 和 positions 的最新状态，它们是原子的
        total_profit = ai.total_assets - ai.initial_cash
        profit_rate = (total_profit / ai.initial_cash) * 100 if ai.initial_cash > 0 else 0.0

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
        from stock_config import get_stock_name
        
        # 直接通过stock_code映射获取stock_name
        # 1. 优先使用DB里的名称（前提是它不等于代码，说明是有效的中文名）
        # 2. 如果DB里存的是代码（旧数据脏数据），则回退查配置
        db_name = position.stock_name
        if db_name and db_name != position.stock_code:
            stock_name = db_name
        else:
            stock_name = get_stock_name(position.stock_code) or position.stock_code
        
        return {
            'stock_code': position.stock_code,
            'stock_name': stock_name,  # 使用映射后的名称
            'quantity': position.quantity,
            'available_quantity': position.available_quantity,
            'cost_price': position.avg_cost,  # 兼容性字段名
            'avg_cost': position.avg_cost,
            'current_price': position.current_price,
            'market_value': position.market_value,
            'profit_loss': position.profit,  # 兼容性字段名
            'profit_loss_percent': position.profit_rate,  # 兼容性字段名
            'profit': position.profit,
            'profit_rate': position.profit_rate
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
            position.last_trade_date = datetime.now()  # 更新最后交易日期
            
            # 更新市值和盈亏
            position.market_value = position.quantity * position.current_price
            cost_basis = position.avg_cost * position.quantity
            position.profit = position.market_value - cost_basis
            if cost_basis > 0:
                position.profit_rate = (position.profit / cost_basis) * 100
            else:
                position.profit_rate = 0.0
        else:
            # 创建新持仓
            avg_cost = (price * quantity + fee) / quantity
            market_value = quantity * price
            cost_basis = avg_cost * quantity
            profit = market_value - cost_basis
            profit_rate = (profit / cost_basis) * 100 if cost_basis > 0 else 0.0
            
            position = Position(
                ai_id=ai_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                available_quantity=0,  # T+1，当日买入不可卖
                avg_cost=avg_cost,
                current_price=price,
                market_value=market_value,
                profit=profit,
                profit_rate=profit_rate,
                last_trade_date=datetime.now()  # 设置最后交易日期
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
        position.last_trade_date = datetime.now()  # 更新最后交易日期
        
        # 如果持仓清零，删除记录
        if position.quantity == 0:
            self.db.delete(position)
        else:
            # 更新市值和盈亏
            position.market_value = position.quantity * position.current_price
            cost_basis = position.avg_cost * position.quantity
            position.profit = position.market_value - cost_basis
            if cost_basis > 0:
                position.profit_rate = (position.profit / cost_basis) * 100
            else:
                position.profit_rate = 0.0
        
        # 更新AI的现金
        ai = self.db.query(AI).filter(AI.id == ai_id).first()
        ai.current_cash += (price * quantity - fee)
        
        self.db.commit()
        logger.info(f"AI {ai_id} sold {quantity} shares of {stock_code} at {price}")
    
        """
        每日更新可卖数量（T+1结算）
        
        根据交易日期检查：
        如果持仓的最后交易日期是"今天之前"，说明经过了一个交易日，
        此时应该将所有冻结的持仓解锁（变为可用）。
        
        Args:
            ai_id: AI ID
        """
        # 注意：这里需要确保查询出的对象在这个session中被跟踪
        positions = self.db.query(Position).filter(Position.ai_id == ai_id).all()
        
        dirty = False
        today = date.today()
        
        for pos in positions:
            # 如果有持仓，且可用数小于总数
            if pos.quantity > 0 and pos.available_quantity < pos.quantity:
                # 检查日期：使用last_trade_date
                # 如果last_trade_date为空，假设是旧数据，默认解锁
                is_past = False
                if pos.last_trade_date:
                    if pos.last_trade_date.date() < today:
                        is_past = True
                else:
                    # 无日期数据的旧持仓，默认解锁
                    is_past = True
                
                if is_past:
                    pos.available_quantity = pos.quantity
                    dirty = True
                    logger.info(f"🔓 T+1解锁: AI {pos.ai_id} {pos.stock_code} {pos.quantity}股 (Last Trade: {pos.last_trade_date})")
        
        if dirty:
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
                # 计算盈亏：市值 - 成本
                cost_basis = position.avg_cost * position.quantity
                position.profit = position.market_value - cost_basis
                
                # 计算盈亏比例
                if cost_basis > 0:
                    position.profit_rate = (position.profit / cost_basis) * 100
                else:
                    position.profit_rate = 0.0
                
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


