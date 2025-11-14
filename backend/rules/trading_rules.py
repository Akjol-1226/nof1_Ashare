"""
A股交易规则引擎
实现T+1、涨跌停、最小交易单位、手续费等规则
"""

from datetime import datetime, time
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class TradingRules:
    """A股交易规则"""
    
    def __init__(
        self,
        commission_rate: float = 0.00025,
        stamp_tax_rate: float = 0.001,
        transfer_fee_rate: float = 0.00001,
        min_lot_size: int = 100,
        price_limit_normal: float = 0.10,
        price_limit_st: float = 0.05
    ):
        """
        初始化交易规则
        
        Args:
            commission_rate: 佣金费率（万2.5）
            stamp_tax_rate: 印花税（0.1%，仅卖出）
            transfer_fee_rate: 过户费（万0.1）
            min_lot_size: 最小交易单位（1手=100股）
            price_limit_normal: 普通股票涨跌停限制（10%）
            price_limit_st: ST股票涨跌停限制（5%）
        """
        self.commission_rate = commission_rate
        self.stamp_tax_rate = stamp_tax_rate
        self.transfer_fee_rate = transfer_fee_rate
        self.min_lot_size = min_lot_size
        self.price_limit_normal = price_limit_normal
        self.price_limit_st = price_limit_st
        
        logger.info("TradingRules initialized")
    
    def check_trading_time(self, check_time: Optional[datetime] = None) -> bool:
        """
        检查是否在交易时间内
        
        A股交易时间：
        - 周一至周五
        - 上午：9:30-11:30
        - 下午：13:00-15:00
        
        Args:
            check_time: 检查时间，默认为当前时间
            
        Returns:
            是否在交易时间内
        """
        if check_time is None:
            check_time = datetime.now()
        
        # 检查是否为工作日（周一到周五）
        if check_time.weekday() >= 5:
            return False
        
        current_time = check_time.time()
        
        # 上午交易时间：9:30-11:30
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        
        # 下午交易时间：13:00-15:00
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)
        
        in_morning = morning_start <= current_time <= morning_end
        in_afternoon = afternoon_start <= current_time <= afternoon_end
        
        return in_morning or in_afternoon
    
    def validate_lot_size(self, quantity: int) -> Tuple[bool, str]:
        """
        验证交易数量是否符合最小交易单位
        
        A股必须以100股（1手）为单位交易
        
        Args:
            quantity: 交易数量
            
        Returns:
            (是否合法, 错误信息)
        """
        if quantity <= 0:
            return False, "交易数量必须大于0"
        
        if quantity % self.min_lot_size != 0:
            return False, f"交易数量必须是{self.min_lot_size}股的整数倍"
        
        return True, ""
    
    def check_price_limit(
        self, 
        stock_code: str,
        current_price: float,
        yesterday_close: float
    ) -> Tuple[bool, float, float]:
        """
        检查价格是否触及涨跌停
        
        Args:
            stock_code: 股票代码
            current_price: 当前价格
            yesterday_close: 昨日收盘价
            
        Returns:
            (是否触及涨跌停, 涨停价, 跌停价)
        """
        # 判断是否为ST股票
        is_st = 'ST' in stock_code or stock_code.startswith('*')
        limit = self.price_limit_st if is_st else self.price_limit_normal
        
        # 计算涨跌停价格（保留两位小数）
        upper_limit = round(yesterday_close * (1 + limit), 2)
        lower_limit = round(yesterday_close * (1 - limit), 2)
        
        # 检查是否触及涨跌停
        is_limit = current_price >= upper_limit or current_price <= lower_limit
        
        return is_limit, upper_limit, lower_limit
    
    def calculate_commission(
        self,
        price: float,
        quantity: int,
        direction: str
    ) -> Tuple[float, Dict]:
        """
        计算手续费
        
        手续费包括：
        1. 佣金（买卖双向，最低5元）
        2. 印花税（仅卖出，0.1%）
        3. 过户费（买卖双向，万0.1）
        
        Args:
            price: 成交价格
            quantity: 成交数量
            direction: 交易方向 (buy/sell)
            
        Returns:
            (总手续费, 手续费明细)
        """
        amount = price * quantity
        
        # 1. 佣金（最低5元）
        commission = max(amount * self.commission_rate, 5.0)
        
        # 2. 印花税（仅卖出）
        stamp_tax = amount * self.stamp_tax_rate if direction == 'sell' else 0.0
        
        # 3. 过户费
        transfer_fee = amount * self.transfer_fee_rate
        
        total_fee = commission + stamp_tax + transfer_fee
        
        fee_detail = {
            'commission': round(commission, 2),
            'stamp_tax': round(stamp_tax, 2),
            'transfer_fee': round(transfer_fee, 2),
            'total': round(total_fee, 2)
        }
        
        return round(total_fee, 2), fee_detail
    
    def apply_t1_rule(
        self,
        buy_date: datetime,
        sell_date: datetime
    ) -> bool:
        """
        应用T+1规则
        
        当日买入的股票，次日才能卖出
        
        Args:
            buy_date: 买入日期
            sell_date: 卖出日期
            
        Returns:
            是否可以卖出
        """
        # 比较日期（忽略时间）
        buy_day = buy_date.date()
        sell_day = sell_date.date()
        
        return sell_day > buy_day
    
    def validate_order(
        self,
        stock_code: str,
        price: float,
        quantity: int,
        direction: str,
        available_cash: float = None,
        available_quantity: int = None,
        yesterday_close: float = None
    ) -> Tuple[bool, str]:
        """
        综合验证订单是否合法
        
        Args:
            stock_code: 股票代码
            price: 价格
            quantity: 数量
            direction: 方向 (buy/sell)
            available_cash: 可用资金（买入时需要）
            available_quantity: 可卖数量（卖出时需要）
            yesterday_close: 昨日收盘价（用于检查涨跌停）
            
        Returns:
            (是否合法, 错误信息)
        """
        # 1. 验证交易数量
        is_valid, msg = self.validate_lot_size(quantity)
        if not is_valid:
            return False, msg
        
        # 2. 检查价格是否合理
        if price <= 0:
            return False, "价格必须大于0"
        
        # 3. 检查涨跌停（如果提供了昨日收盘价）
        if yesterday_close is not None:
            is_limit, upper, lower = self.check_price_limit(
                stock_code, price, yesterday_close
            )
            if direction == 'buy' and price >= upper:
                return False, f"价格达到涨停板限制（{upper}元）"
            if direction == 'sell' and price <= lower:
                return False, f"价格达到跌停板限制（{lower}元）"
        
        # 4. 买入时检查资金
        if direction == 'buy' and available_cash is not None:
            fee, _ = self.calculate_commission(price, quantity, direction)
            total_cost = price * quantity + fee
            if total_cost > available_cash:
                return False, f"可用资金不足（需要{total_cost:.2f}元，可用{available_cash:.2f}元）"
        
        # 5. 卖出时检查持仓
        if direction == 'sell' and available_quantity is not None:
            if quantity > available_quantity:
                return False, f"可卖数量不足（需要{quantity}股，可卖{available_quantity}股）"
        
        return True, ""


