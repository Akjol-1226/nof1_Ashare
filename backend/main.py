"""
FastAPI主应用
"""

# 首先导入代理禁用模块
try:
    import disable_proxy
except:
    pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
from typing import List
import json
from datetime import datetime

from config import settings
from database import init_db, get_db_session
from api.routes import router
from data_service.akshare_client import AKShareClient
from rules.trading_rules import TradingRules
from portfolio.portfolio_manager import PortfolioManager
from trading_engine.order_manager import OrderManager
from trading_engine.matching_engine import MatchingEngine
from ai_service.ai_scheduler import AIScheduler

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 全局变量
scheduler: AIScheduler = None
websocket_clients: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting application...")
    init_db()
    logger.info("Application started")
    
    yield
    
    # 关闭时
    logger.info("Shutting down application...")
    if scheduler:
        scheduler.stop()
    logger.info("Application shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title="nof1.AShare - A股AI模拟交易系统",
    description="AI模拟炒股竞赛平台",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


# ==================== WebSocket ====================

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)


manager = ConnectionManager()


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """市场数据WebSocket"""
    await manager.connect(websocket)
    
    try:
        # 定期推送市场数据
        akshare_client = AKShareClient()
        
        while True:
            # 获取实时行情
            from stock_config import TRADING_STOCKS
            quotes = akshare_client.get_realtime_quotes(TRADING_STOCKS)
            
            await websocket.send_json({
                "type": "market_update",
                "data": {
                    "timestamp": quotes[0].timestamp.isoformat() if quotes else None,
                    "quotes": [q.to_dict() for q in quotes]
                }
            })
            
            await asyncio.sleep(10)  # 每10秒更新一次
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/trading")
async def websocket_trading(websocket: WebSocket):
    """交易数据WebSocket - 事件驱动 + 定期保底"""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "trading_connected",
            "message": "交易WebSocket已连接"
        })

        # 发送初始数据
        with get_db_session() as db:
            ais = db.query(AI).all()
            portfolios = []
            orders = []

            for ai in ais:
                from portfolio.portfolio_manager import PortfolioManager
                from rules.trading_rules import TradingRules
                portfolio_manager = PortfolioManager(db, TradingRules())
                portfolio = portfolio_manager.get_ai_portfolio(ai.id)
                portfolios.append(portfolio)

                from models.models import Order
                ai_orders = db.query(Order).filter(
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

            await websocket.send_json({
                "type": "trading_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "portfolios": portfolios,
                    "orders": orders
                }
            })

        # 定期保底推送（5秒一次）
        while True:
            await asyncio.sleep(5)
            # 这里可以添加定期检查是否有新数据需要推送的逻辑
            # 但主要的数据更新通过事件驱动推送

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/chats")
async def websocket_chats(websocket: WebSocket):
    """AI对话WebSocket - 事件驱动 + 定期保底"""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "chats_connected",
            "message": "AI对话WebSocket已连接"
        })

        # 发送最近的对话历史
        with get_db_session() as db:
            ais = db.query(AI).all()
            chats = []

            for ai in ais:
                from models.models import DecisionLog
                recent_decisions = db.query(DecisionLog).filter(
                    DecisionLog.ai_id == ai.id
                ).order_by(DecisionLog.timestamp.desc()).limit(5).all()

                ai_chats = []
                for decision in recent_decisions:
                    try:
                        import json
                        parsed_decision = json.loads(decision.parsed_decision) if decision.parsed_decision else {}
                        reasoning = parsed_decision.get('reasoning', '无推理信息')

                        ai_chats.append({
                            'id': decision.id,
                            'timestamp': decision.timestamp.isoformat(),
                            'reasoning': reasoning,
                            'actions': parsed_decision.get('actions', []),
                            'latency_ms': decision.latency_ms,
                            'tokens_used': decision.tokens_used,
                            'error': decision.error
                        })
                    except json.JSONDecodeError:
                        continue

                if ai_chats:
                    chats.append({
                        'ai_id': ai.id,
                        'ai_name': ai.name,
                        'chats': ai_chats
                    })

            if chats:
                await websocket.send_json({
                    "type": "chats_update",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "chats": chats
                    }
                })

        # 定期保底推送（3秒一次）
        while True:
            await asyncio.sleep(3)
            # 主要通过事件驱动推送新决策，定期推送作为保底

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/performance")
async def websocket_performance(websocket: WebSocket):
    """AI收益曲线WebSocket"""
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "performance_connected",
            "message": "收益曲线WebSocket已连接"
        })

        # 保持连接
        while True:
            await asyncio.sleep(30)  # 每30秒发送心跳

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ==================== 根路由 ====================

@app.get("/")
def root():
    """根路由"""
    return {
        "name": "nof1.AShare",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ==================== 调度器管理 ====================

@app.post("/api/system/start")
async def start_trading():
    """启动交易系统"""
    global scheduler
    
    if scheduler and scheduler.is_running:
        return {"status": "already_running"}
    
    try:
        with get_db_session() as db:
            # 初始化组件
            akshare_client = AKShareClient()
            trading_rules = TradingRules()
            portfolio_manager = PortfolioManager(db, trading_rules)
            order_manager = OrderManager(db, trading_rules)
            matching_engine = MatchingEngine(
                db, trading_rules, portfolio_manager, akshare_client
            )
            
            # 创建调度器
            scheduler = AIScheduler(
                db,
                akshare_client,
                portfolio_manager,
                order_manager,
                trading_rules,
                decision_interval=settings.ai_decision_interval,
                llm_timeout=settings.llm_timeout
            )
            
            # 启动调度器
            scheduler.start()
        
        return {"status": "started", "message": "Trading system started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/system/stop")
async def stop_trading():
    """停止交易系统"""
    global scheduler
    
    if not scheduler or not scheduler.is_running:
        return {"status": "not_running"}
    
    try:
        scheduler.stop()
        scheduler = None
        
        return {"status": "stopped", "message": "Trading system stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop system: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )


