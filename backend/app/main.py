from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api.v1 import auth, demo, market
from .services.websocket_manager import ws_manager
import asyncio

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="JADOTA AI API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else settings.cors_origins,
)

# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(demo.router, prefix=settings.api_prefix)
app.include_router(market.router, prefix=settings.api_prefix)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await ws_manager.add_connection(websocket)
    
    try:
        while True:
            # Receive subscription messages
            data = await websocket.receive_text()
            try:
                import json
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

# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "version": "1.0.0"
    }

# Root
@app.get("/")
async def root():
    return {
        "message": "Welcome to JADOTA AI API",
        "docs": "/api/docs",
        "health": "/api/health"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Start WebSocket manager on startup."""
    # Start WebSocket connection in background
    asyncio.create_task(ws_manager.connect())
    print("JADOTA AI API started with WebSocket manager")
