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

router = APIRouter()


# ==================== 数据模型 ====================

class AICreate(BaseModel):
    """创建AI请求"""
    name: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
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
        api_key=ai_data.api_key,
        base_url=ai_data.base_url,
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
                "stock_name": p.stock_name,
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
            "is_active": ai.is_active
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


# ==================== 系统控制接口 ====================

class SystemStatus(BaseModel):
    """系统状态"""
    is_running: bool
    trading_time: bool
    total_ais: int
    active_ais: int


@router.get("/api/system/status", response_model=SystemStatus)
def get_system_status(db: Session = Depends(get_db)):
    """获取系统状态"""
    from rules.trading_rules import TradingRules
    
    trading_rules = TradingRules()
    total_ais = db.query(AI).count()
    active_ais = db.query(AI).filter(AI.is_active == True).count()
    
    return SystemStatus(
        is_running=False,  # TODO: 从调度器获取状态
        trading_time=trading_rules.check_trading_time(),
        total_ais=total_ais,
        active_ais=active_ais
    )


@router.post("/api/system/start")
def start_system():
    """启动交易系统"""
    # TODO: 启动调度器
    return {"message": "System start command sent"}


@router.post("/api/system/stop")
def stop_system():
    """停止交易系统"""
    # TODO: 停止调度器
    return {"message": "System stop command sent"}


