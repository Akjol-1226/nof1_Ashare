"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class AI(Base):
    """AI交易者模型"""
    __tablename__ = 'ai'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    model_name = Column(String(50), nullable=False)  # gpt-4, claude-3, deepseek
    # API Key从环境变量读取，不存储在数据库中
    system_prompt = Column(Text)  # 系统提示词
    temperature = Column(Float, default=0.7)  # 生成温度
    
    # 资金相关
    initial_cash = Column(Float, default=100000.0)
    current_cash = Column(Float, default=100000.0)
    total_assets = Column(Float, default=100000.0)  # 总资产（现金+持仓市值）
    total_profit = Column(Float, default=0.0)  # 总收益
    profit_rate = Column(Float, default=0.0)  # 收益率(%)
    
    # 交易统计
    trade_count = Column(Integer, default=0)  # 交易次数
    win_count = Column(Integer, default=0)  # 盈利次数
    win_rate = Column(Float, default=0.0)  # 胜率(%)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    positions = relationship("Position", back_populates="ai")
    orders = relationship("Order", back_populates="ai")
    transactions = relationship("Transaction", back_populates="ai")
    snapshots = relationship("PortfolioSnapshot", back_populates="ai")
    decision_logs = relationship("DecisionLog", back_populates="ai")


class Position(Base):
    """持仓模型"""
    __tablename__ = 'position'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_id = Column(Integer, ForeignKey('ai.id'), nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100))
    
    quantity = Column(Integer, default=0)  # 总持仓数量
    available_quantity = Column(Integer, default=0)  # 可卖数量（T+1）
    avg_cost = Column(Float, default=0.0)  # 平均成本价
    current_price = Column(Float, default=0.0)  # 当前价
    market_value = Column(Float, default=0.0)  # 市值
    profit = Column(Float, default=0.0)  # 浮动盈亏
    profit_rate = Column(Float, default=0.0)  # 盈亏比例(%)
    
    # T+1相关：记录最后一次交易（买入/卖出）的日期
    # 注意：这个字段只在买入/卖出时更新，市值更新不影响它
    last_trade_date = Column(DateTime, default=datetime.now)  # 最后交易日期
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 最后更新时间
    
    # 关系
    ai = relationship("AI", back_populates="positions")


class Order(Base):
    """订单模型"""
    __tablename__ = 'order'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_id = Column(Integer, ForeignKey('ai.id'), nullable=False)
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100))
    
    direction = Column(String(10), nullable=False)  # buy/sell
    order_type = Column(String(10), nullable=False)  # market/limit
    price = Column(Float)  # 限价单价格
    quantity = Column(Integer, nullable=False)
    
    status = Column(String(20), default='pending')  # pending/filled/cancelled/rejected
    filled_quantity = Column(Integer, default=0)
    filled_price = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.now)
    filled_at = Column(DateTime)
    
    # 关系
    ai = relationship("AI", back_populates="orders")


class Transaction(Base):
    """成交记录模型"""
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_id = Column(Integer, ForeignKey('ai.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('order.id'))
    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100))
    
    direction = Column(String(10), nullable=False)  # buy/sell
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)  # 成交金额
    
    commission = Column(Float, default=0.0)  # 佣金
    stamp_tax = Column(Float, default=0.0)  # 印花税
    transfer_fee = Column(Float, default=0.0)  # 过户费
    total_fee = Column(Float, default=0.0)  # 总手续费
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    ai = relationship("AI", back_populates="transactions")


class PortfolioSnapshot(Base):
    """持仓快照模型（每日记录）"""
    __tablename__ = 'portfolio_snapshot'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_id = Column(Integer, ForeignKey('ai.id'), nullable=False)
    
    date = Column(DateTime, nullable=False)
    cash = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)  # 持仓市值
    total_assets = Column(Float, default=0.0)  # 总资产
    
    daily_profit_loss = Column(Float, default=0.0)  # 当日盈亏
    daily_return = Column(Float, default=0.0)  # 当日收益率
    total_profit_loss = Column(Float, default=0.0)  # 累计盈亏
    total_return = Column(Float, default=0.0)  # 累计收益率
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    ai = relationship("AI", back_populates="snapshots")


class DecisionLog(Base):
    """AI决策日志模型"""
    __tablename__ = 'decision_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_id = Column(Integer, ForeignKey('ai.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    
    # 市场和持仓快照
    market_data = Column(JSON)  # 当时的市场数据快照
    portfolio_data = Column(JSON)  # 当时的持仓数据快照
    
    # LLM交互
    llm_prompt = Column(Text)  # 完整的Prompt（System + User）
    llm_response = Column(Text)  # LLM原始响应
    parsed_decision = Column(JSON)  # 解析后的JSON: {reasoning, actions}
    
    # 执行结果
    orders_generated = Column(JSON)  # 生成的订单列表
    execution_result = Column(JSON)  # 执行结果（成功/失败）
    
    # 性能指标
    latency_ms = Column(Integer)  # LLM响应延迟（毫秒）
    tokens_used = Column(Integer)  # Token消耗
    
    # 错误信息
    error = Column(Text)  # 错误信息
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    ai = relationship("AI", back_populates="decision_logs")


