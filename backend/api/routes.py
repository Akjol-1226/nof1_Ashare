"""
API路由定义
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models.models import AI, Position, Order, Transaction, DecisionLog
from database import get_db
from stock_config import get_stock_name

router = APIRouter()


# ==================== 数据模型 ====================

class AICreate(BaseModel):
    """创建AI请求"""
    name: str
    model_name: str
    # API Key和base_url从环境变量和ais_config.py读取
    initial_cash: float = 100000.0


class AIResponse(BaseModel):
    """AI响应"""
    id: int
    name: str
    model_name: str
    initial_cash: float
    current_cash: float
    total_assets: float
    is_active: bool
    
    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """持仓响应"""
    stock_code: str
    stock_name: str
    quantity: int
    available_quantity: int
    cost_price: float
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_percent: float
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    stock_code: str
    stock_name: str
    direction: str
    order_type: str
    price: Optional[float]
    quantity: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderWithAIResponse(OrderResponse):
    """带AI信息的订单响应"""
    ai_id: int
    ai_name: str


class TransactionResponse(BaseModel):
    """成交记录响应"""
    id: int
    stock_code: str
    stock_name: str
    direction: str
    price: float
    quantity: int
    amount: float
    total_fee: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class DecisionLogResponse(BaseModel):
    """决策日志响应"""
    id: int
    prompt: str
    response: Optional[str]
    decision: Optional[str]
    stock_code: Optional[str]
    quantity: Optional[int]
    reasoning: Optional[str]
    execution_time: float
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== AI相关接口 ====================

@router.post("/api/ai/register", response_model=AIResponse)
def register_ai(ai_data: AICreate, db: Session = Depends(get_db)):
    """注册AI参赛者"""
    # 检查名称是否已存在
    existing = db.query(AI).filter(AI.name == ai_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="AI name already exists")
    
    ai = AI(
        name=ai_data.name,
        model_name=ai_data.model_name,
        initial_cash=ai_data.initial_cash,
        current_cash=ai_data.initial_cash,
        total_assets=ai_data.initial_cash,
        is_active=True
    )
    
    db.add(ai)
    db.commit()
    db.refresh(ai)
    
    return ai


@router.get("/api/ai/list", response_model=List[AIResponse])
def get_ai_list(db: Session = Depends(get_db)):
    """获取所有AI列表"""
    ais = db.query(AI).all()
    return ais


@router.get("/api/ai/{ai_id}/portfolio")
def get_ai_portfolio(ai_id: int, db: Session = Depends(get_db)):
    """获取AI持仓"""
    ai = db.query(AI).filter(AI.id == ai_id).first()
    if not ai:
        raise HTTPException(status_code=404, detail="AI not found")
    
    positions = db.query(Position).filter(Position.ai_id == ai_id).all()
    
    return {
        "ai_id": ai.id,
        "ai_name": ai.name,
        "cash": ai.current_cash,
        "total_assets": ai.total_assets,
        "positions": [
            {
                "stock_code": p.stock_code,
                "stock_name": get_stock_name(p.stock_code) or p.stock_name or p.stock_code,
                "quantity": p.quantity,
                "available_quantity": p.available_quantity,
                "cost_price": p.cost_price,
                "current_price": p.current_price,
                "market_value": p.market_value,
                "profit_loss": p.profit_loss,
                "profit_loss_percent": p.profit_loss_percent
            }
            for p in positions
        ]
    }


@router.get("/api/ai/{ai_id}/orders", response_model=List[OrderResponse])
def get_ai_orders(ai_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """获取AI订单历史"""
    orders = db.query(Order).filter(
        Order.ai_id == ai_id
    ).order_by(Order.created_at.desc()).limit(limit).all()
    
    return orders


@router.get("/api/ai/{ai_id}/transactions", response_model=List[TransactionResponse])
def get_ai_transactions(ai_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """获取AI成交记录"""
    transactions = db.query(Transaction).filter(
        Transaction.ai_id == ai_id
    ).order_by(Transaction.created_at.desc()).limit(limit).all()
    
    return transactions


@router.get("/api/ai/{ai_id}/decisions", response_model=List[DecisionLogResponse])
def get_ai_decisions(ai_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """获取AI决策日志"""
    logs = db.query(DecisionLog).filter(
        DecisionLog.ai_id == ai_id
    ).order_by(DecisionLog.created_at.desc()).limit(limit).all()
    
    return logs


@router.get("/api/ai/ranking")
def get_ai_ranking(db: Session = Depends(get_db)):
    """获取AI排行榜"""
    ais = db.query(AI).order_by(AI.total_assets.desc()).all()
    
    return [
        {
            "rank": idx + 1,
            "ai_id": ai.id,
            "ai_name": ai.name,
            "total_assets": ai.total_assets,
            "profit_loss": ai.total_assets - ai.initial_cash,
            "return_rate": ((ai.total_assets - ai.initial_cash) / ai.initial_cash * 100) if ai.initial_cash > 0 else 0,
            "is_active": ai.is_active,
            "positions": [
                {
                    "stock_code": p.stock_code,
                    "stock_name": get_stock_name(p.stock_code) or p.stock_name or p.stock_code,
                    "quantity": p.quantity,
                    "available_quantity": p.available_quantity,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "profit_loss": p.profit,
                    "profit_loss_percent": p.profit_rate
                }
                for p in ai.positions
            ]
        }
        for idx, ai in enumerate(ais)
    ]


# ==================== 市场数据接口 ====================

@router.get("/api/market/quotes")
def get_market_quotes(limit: int = 50):
    """获取实时行情"""
    from data_service.akshare_client import AKShareClient
    
    client = AKShareClient()
    quotes = client.get_realtime_quotes()[:limit]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "quotes": [q.to_dict() for q in quotes]
    }


@router.get("/api/market/stocks")
def get_stock_list():
    """获取股票列表"""
    from data_service.akshare_client import AKShareClient
    
    client = AKShareClient()
    stocks = client.get_all_stock_list()
    
    return {
        "total": len(stocks),
        "stocks": [s.to_dict() for s in stocks[:1000]]  # 限制返回数量
    }


@router.get("/api/market/orders", response_model=List[OrderWithAIResponse])
def get_all_orders(limit: int = 100, db: Session = Depends(get_db)):
    """获取全市场最新订单"""
    # 联表查询 AI 信息
    results = db.query(Order, AI.name).join(AI, Order.ai_id == AI.id)\
        .order_by(Order.created_at.desc()).limit(limit).all()
    
    # 手动组装响应
    response_list = []
    for order, ai_name in results:
        order_dict = {
            "id": order.id,
            "stock_code": order.stock_code,
            "stock_name": order.stock_name,
            "direction": order.direction,
            "order_type": order.order_type,
            "price": order.price,
            "quantity": order.quantity,
            "status": order.status,
            "created_at": order.created_at,
            "ai_id": order.ai_id,
            "ai_name": ai_name
        }
        response_list.append(order_dict)
    
    return response_list


# ==================== 系统控制接口 ====================

class SystemStatus(BaseModel):
    """系统状态"""
    is_running: bool
    trading_time: bool
    total_ais: int
    active_ais: int




