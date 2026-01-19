"""
FastAPI主应用
"""

# 首先导入代理禁用模块
try:
    import disable_proxy
except:
    pass

# 加载环境变量
from dotenv import load_dotenv
import os
# 加载项目根目录下的 .env 文件
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
from typing import List
import json
import time
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
from models.models import AI, Order, DecisionLog, PortfolioSnapshot

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


# ==================== 调试端点 ====================

@app.get("/api/test")
def test_endpoint():
    """测试端点"""
    print("=== /api/test 端点被调用 ===")
    return {"message": "Test endpoint works", "scheduler": str(scheduler) if 'scheduler' in globals() else "not_defined"}

@app.get("/api/debug/scheduler")
def debug_scheduler():
    """调试：检查scheduler状态"""
    global scheduler
    try:
        return {
            "scheduler_exists": scheduler is not None,
            "scheduler_type": type(scheduler).__name__ if scheduler else None,
            "is_running": scheduler.is_running if scheduler else False,
            "has_thread": scheduler.schedule_thread is not None if scheduler else False,
            "thread_alive": scheduler.schedule_thread.is_alive() if scheduler and scheduler.schedule_thread else False,
            "scheduler_object": str(scheduler) if scheduler else None,
        }
    except Exception as e:
        return {"error": str(e), "scheduler": str(scheduler) if 'scheduler' in globals() else "not_defined"}

@app.post("/api/debug/trigger-decision")
def trigger_decision():
    """手动触发一次AI决策周期"""
    global scheduler
    try:
        if not scheduler or not scheduler.is_running:
            return {"error": "调度器未运行", "is_running": False}
        
        # 手动触发决策
        import threading
        def run_decision():
            scheduler._execute_decision_cycle_sync()
        
        thread = threading.Thread(target=run_decision)
        thread.start()
        
        return {"message": "决策周期已触发", "is_running": True}
    except Exception as e:
        return {"error": str(e)}


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
            
            # 创建管理器实例
            trading_rules = TradingRules()
            portfolio_manager = PortfolioManager(db, trading_rules)

            for ai in ais:
                portfolio = portfolio_manager.get_ai_portfolio(ai.id)
                portfolios.append(portfolio)

                ai_orders = db.query(Order).filter(
                    Order.ai_id == ai.id,
                    Order.status.in_(['pending', 'filled', 'rejected'])  # 包含被拒绝的订单
                ).order_by(Order.created_at.desc()).limit(10).all()

                from stock_config import get_stock_name
                
                orders.extend([{
                    'id': order.id,
                    'ai_id': order.ai_id,
                    'ai_name': ai.name,
                    'stock_code': order.stock_code,
                    'stock_name': get_stock_name(order.stock_code) or order.stock_code,  # 直接映射
                    'direction': order.direction,
                    'quantity': order.quantity,
                    'price': order.price,
                    'status': order.status,
                    'created_at': order.created_at.isoformat()
                } for order in ai_orders])

            # 获取最新行情数据
            from data_service.akshare_client import AKShareClient
            from stock_config import TRADING_STOCKS
            
            data_client = AKShareClient()
            stock_codes = list(TRADING_STOCKS.keys())
            quotes_data = data_client.get_realtime_quotes(stock_codes)
            
            # 转换为前端需要的格式
            quotes = [{
                'code': quote.code,
                'name': quote.name,
                'price': quote.price,
                'change_percent': quote.change_percent
            } for quote in quotes_data]

            await websocket.send_json({
                "type": "trading_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "portfolios": portfolios,
                    "orders": orders,
                    "quotes": quotes  # 添加行情数据
                }
            })

        # 定期保底推送（5秒一次）- 包括最新行情和持仓数据
        while True:
            await asyncio.sleep(5)
            
            # 推送最新数据
            with get_db_session() as db:
                ais = db.query(AI).all()
                portfolios = []
                orders = []
                
                # 创建管理器实例
                trading_rules = TradingRules()
                portfolio_manager = PortfolioManager(db, trading_rules)

                for ai in ais:
                    portfolio = portfolio_manager.get_ai_portfolio(ai.id)
                    portfolios.append(portfolio)

                    ai_orders = db.query(Order).filter(
                        Order.ai_id == ai.id,
                        Order.status.in_(['pending', 'filled', 'rejected'])
                    ).order_by(Order.created_at.desc()).limit(10).all()

                    from stock_config import get_stock_name
                    
                    orders.extend([{
                        'id': order.id,
                        'ai_id': order.ai_id,
                        'ai_name': ai.name,
                        'stock_code': order.stock_code,
                        'stock_name': get_stock_name(order.stock_code) or order.stock_code,
                        'direction': order.direction,
                        'quantity': order.quantity,
                        'price': order.price,
                        'status': order.status,
                        'created_at': order.created_at.isoformat()
                    } for order in ai_orders])

                # 获取最新行情数据
                from data_service.akshare_client import AKShareClient
                from stock_config import TRADING_STOCKS
                
                data_client = AKShareClient()
                stock_codes = list(TRADING_STOCKS.keys())
                quotes_data = data_client.get_realtime_quotes(stock_codes)
                
                # 转换为前端需要的格式
                quotes = [{
                    'code': quote.code,
                    'name': quote.name,
                    'price': quote.price,
                    'change_percent': quote.change_percent
                } for quote in quotes_data]

                await websocket.send_json({
                    "type": "trading_update",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "portfolios": portfolios,
                        "orders": orders,
                        "quotes": quotes  # 持续推送行情数据
                    }
                })

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
                recent_decisions = db.query(DecisionLog).filter(
                    DecisionLog.ai_id == ai.id
                ).order_by(DecisionLog.timestamp.desc()).limit(5).all()

                ai_chats = []
                for decision in recent_decisions:
                    try:
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
    print("🔌 WebSocket /ws/performance 连接请求")
    await manager.connect(websocket)
    print("✅ WebSocket /ws/performance 连接成功")

    try:
        await websocket.send_json({
            "type": "performance_connected",
            "message": "收益曲线WebSocket已连接"
        })

        # 发送初始数据
        with get_db_session() as db:
            ais = db.query(AI).all()

            # 获取所有快照数据（不限制数量，从竞赛开始到现在）
            snapshots = []
            for ai in ais:
                all_snapshots = db.query(PortfolioSnapshot).filter(
                    PortfolioSnapshot.ai_id == ai.id
                ).order_by(PortfolioSnapshot.date.asc()).all()  # 按时间升序

                for snapshot in all_snapshots:
                    snapshots.append({
                        'timestamp': snapshot.date.isoformat(),
                        'ai_id': ai.id,
                        'ai_name': ai.name,
                        'cash': snapshot.cash,
                        'market_value': snapshot.market_value,
                        'total_assets': snapshot.total_assets,
                        'daily_profit_loss': snapshot.daily_profit_loss,
                        'daily_return': snapshot.daily_return,
                        'total_profit_loss': snapshot.total_profit_loss,
                        'total_return': snapshot.total_return
                    })

            # 按时间排序
            snapshots.sort(key=lambda x: x['timestamp'])

            await websocket.send_json({
                "type": "performance_update",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "snapshots": snapshots
                }
            })

        # 保持连接，定期推送最新数据
        while True:
            await asyncio.sleep(30)  # 每30秒推送一次最新数据

            with get_db_session() as db:
                ais = db.query(AI).all()

                snapshots = []
                for ai in ais:
                    # 获取所有快照（从竞赛开始到现在）
                    all_snapshots = db.query(PortfolioSnapshot).filter(
                        PortfolioSnapshot.ai_id == ai.id
                    ).order_by(PortfolioSnapshot.date.asc()).all()

                    for snapshot in all_snapshots:
                        snapshots.append({
                            'timestamp': snapshot.date.isoformat(),
                            'ai_id': ai.id,
                            'ai_name': ai.name,
                            'cash': snapshot.cash,
                            'market_value': snapshot.market_value,
                            'total_assets': snapshot.total_assets,
                            'daily_profit_loss': snapshot.daily_profit_loss,
                            'daily_return': snapshot.daily_return,
                            'total_profit_loss': snapshot.total_profit_loss,
                            'total_return': snapshot.total_return
                        })

                # 按时间排序
                snapshots.sort(key=lambda x: x['timestamp'])

                if snapshots:
                    await websocket.send_json({
                        "type": "performance_update",
                        "data": {
                            "timestamp": datetime.now().isoformat(),
                            "snapshots": snapshots
                        }
                    })

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
async def start_trading(force_run: bool = False):
    """启动交易系统
    
    Args:
        force_run: 是否强制运行（忽略交易时间检查，用于测试）
    """
    global scheduler

    logger.info(f"收到启动交易系统请求（force_run={force_run}）")

    if scheduler and scheduler.is_running:
        logger.info("调度器已在运行")
        return {"status": "already_running"}

    try:
        logger.info("=== 开始初始化交易系统组件 ===")

        # 初始化组件（在session外面）
        logger.info("初始化AKShare客户端...")
        akshare_client = AKShareClient()

        logger.info("初始化交易规则...")
        trading_rules = TradingRules()

        with get_db_session() as db:
            logger.info("初始化投资组合管理器...")
            portfolio_manager = PortfolioManager(db, trading_rules)

            logger.info("初始化订单管理器...")
            order_manager = OrderManager(db, trading_rules)

            logger.info("初始化订单匹配引擎...")
            matching_engine = MatchingEngine(
                db, trading_rules, portfolio_manager, akshare_client
            )

            logger.info("创建AI调度器...")
            # 创建调度器 - 不传递db参数，让它自己管理数据库连接
            scheduler = AIScheduler(
                data_client=akshare_client,
                portfolio_manager=portfolio_manager,
                order_manager=order_manager,
                matching_engine=matching_engine,  # 添加撮合引擎
                trading_rules=trading_rules,
                market_update_interval=15,     # 行情更新：15秒
                decision_interval=1800,        # AI决策：30分钟 = 1800秒
                matching_interval=15,          # 订单撮合：15秒
                llm_timeout=settings.llm_timeout,
                force_run=force_run            # 是否强制运行（测试模式）
            )

            logger.info(f"调度器创建完成，is_running初始状态: {scheduler.is_running}")

            logger.info("启动调度器...")
            # 启动调度器
            try:
                scheduler.start()
                logger.info(f"调度器启动方法调用完成，is_running状态: {scheduler.is_running}")

                # 再次检查状态
                time.sleep(0.1)  # 短暂等待
                logger.info(f"短暂等待后调度器状态: {scheduler.is_running}")

            except Exception as start_error:
                logger.error(f"调度器启动失败: {start_error}", exc_info=True)
                raise start_error

            logger.info(f"最终调度器状态: is_running={scheduler.is_running}")

        logger.info("=== 交易系统启动成功 ===")
        return {"status": "started", "message": "Trading system started successfully", "is_running": scheduler.is_running if scheduler else False}

    except Exception as e:
        logger.error(f"=== 启动交易系统失败 ===", exc_info=True)
        logger.error(f"错误详情: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/system/status")
def get_system_status():
    """获取系统状态"""
    global scheduler

    with get_db_session() as db:
        total_ais = db.query(AI).count()
        active_ais = db.query(AI).filter(AI.is_active == True).count()

    is_running = scheduler.is_running if scheduler else False
    trading_time = TradingRules().check_trading_time()

    logger.info(f"系统状态: is_running={is_running}, trading_time={trading_time}, total_ais={total_ais}, active_ais={active_ais}")

    return {
        "is_running": is_running,
        "trading_time": trading_time,
        "total_ais": total_ais,
        "active_ais": active_ais
    }


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

