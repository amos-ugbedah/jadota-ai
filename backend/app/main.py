from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api.v1 import auth, demo, market, ai, backtest, risk, exchange, live_trading, subscription, admin
from .services.websocket_manager import ws_manager
from .services.price_simulator import price_simulator
from .services.price_updater import price_updater
from .services.subscription_service import subscription_service
from .workers.payment_watcher import payment_watcher
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

# Initialize subscription plans
with engine.connect() as conn:
    from sqlalchemy.orm import Session
    db = Session(bind=conn)
    subscription_service.initialize_plans(db)
    db.close()

app = FastAPI(
    title="JADOTA AI API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else settings.cors_origins,
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(demo.router, prefix=settings.api_prefix)
app.include_router(market.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(backtest.router, prefix=settings.api_prefix)
app.include_router(risk.router, prefix=settings.api_prefix)
app.include_router(exchange.router, prefix=settings.api_prefix)
app.include_router(live_trading.router, prefix=settings.api_prefix)
app.include_router(subscription.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await ws_manager.add_connection(websocket)
    
    prices = price_simulator.get_all_prices()
    for symbol, price in prices.items():
        await websocket.send(json.dumps({
            'type': 'price_update',
            'symbol': symbol,
            'price': float(price),
            'timestamp': datetime.utcnow().isoformat()
        }))
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get('type') == 'subscribe':
                    symbol = message.get('symbol')
                    if symbol:
                        await ws_manager.subscribe_client(websocket, symbol)
                        await websocket.send(json.dumps({
                            'type': 'subscribed',
                            'symbol': symbol,
                            'message': f'Subscribed to {symbol}'
                        }))
                        
                        current_price = price_simulator.get_price(symbol)
                        if current_price:
                            await websocket.send(json.dumps({
                                'type': 'price_update',
                                'symbol': symbol,
                                'price': float(current_price),
                                'timestamp': datetime.utcnow().isoformat()
                            }))
                elif message.get('type') == 'unsubscribe':
                    symbol = message.get('symbol')
                    if symbol:
                        await ws_manager.unsubscribe_client(websocket, symbol)
                        await websocket.send(json.dumps({
                            'type': 'unsubscribed',
                            'symbol': symbol,
                            'message': f'Unsubscribed from {symbol}'
                        }))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON'
                }))
    except WebSocketDisconnect:
        await ws_manager.remove_connection(websocket)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to JADOTA AI API",
        "docs": "/api/docs",
        "health": "/api/health"
    }

@app.on_event("startup")
async def startup_event():
    await price_simulator.start()
    await price_updater.start()
    ws_manager.start()
    await payment_watcher.start()
    logger.info("✅ JADOTA AI API fully started with Admin Dashboard")

@app.on_event("shutdown")
async def shutdown_event():
    price_simulator.stop()
    price_updater.stop()
    ws_manager.stop()
    payment_watcher.stop()
    logger.info("JADOTA AI API shutting down")
