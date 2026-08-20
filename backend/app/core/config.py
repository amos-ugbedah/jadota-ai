from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "JADOTA AI"
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # API
    api_version: str = Field(default="v1", env="API_VERSION")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    frontend_url: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    cors_origins: List[str] = Field(default=["http://localhost:5173"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    
    # Firebase (instead of Supabase)
    firebase_api_key: Optional[str] = Field(None, env="FIREBASE_API_KEY")
    firebase_auth_domain: Optional[str] = Field(None, env="FIREBASE_AUTH_DOMAIN")
    firebase_project_id: Optional[str] = Field(None, env="FIREBASE_PROJECT_ID")
    firebase_storage_bucket: Optional[str] = Field(None, env="FIREBASE_STORAGE_BUCKET")
    firebase_messaging_sender_id: Optional[str] = Field(None, env="FIREBASE_MESSAGING_SENDER_ID")
    firebase_app_id: Optional[str] = Field(None, env="FIREBASE_APP_ID")
    firebase_private_key: Optional[str] = Field(None, env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = Field(None, env="FIREBASE_CLIENT_EMAIL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Encryption
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    # Bitget
    bitget_api_key: Optional[str] = Field(None, env="BITGET_API_KEY")
    bitget_secret: Optional[str] = Field(None, env="BITGET_SECRET")
    bitget_passphrase: Optional[str] = Field(None, env="BITGET_PASSPHRASE")
    bitget_api_base: str = Field(default="https://api.bitget.com", env="BITGET_API_BASE")
    bitget_ws_base: str = Field(default="wss://ws.bitget.com/v1/stream", env="BITGET_WS_BASE")
    bitget_default_symbols: List[str] = Field(
        default=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"],
        env="BITGET_DEFAULT_SYMBOLS"
    )
    
    # Payment
    jadota_wallet_address: str = Field(..., env="JADOTA_WALLET_ADDRESS")
    jadota_wallet_network: str = Field(default="BEP20", env="JADOTA_WALLET_NETWORK")
    min_payment_confirmations: int = Field(default=6, env="MIN_PAYMENT_CONFIRMATIONS")
    
    # Risk Management
    default_max_risk_per_trade: float = Field(default=2.0, env="DEFAULT_MAX_RISK_PER_TRADE")
    default_max_daily_loss: float = Field(default=5.0, env="DEFAULT_MAX_DAILY_LOSS")
    default_max_weekly_loss: float = Field(default=10.0, env="DEFAULT_MAX_WEEKLY_LOSS")
    max_allowed_drawdown: float = Field(default=15.0, env="MAX_ALLOWED_DRAWDOWN")
    
    # Performance Targets
    target_sharpe_ratio: float = Field(default=1.0, env="TARGET_SHARPE_RATIO")
    min_profit_factor: float = Field(default=1.5, env="MIN_PROFIT_FACTOR")
    min_win_rate: float = Field(default=55.0, env="MIN_WIN_RATE")
    max_win_rate: float = Field(default=65.0, env="MAX_WIN_RATE")
    
    # Trading
    max_position_days: int = Field(default=14, env="MAX_POSITION_DAYS")
    min_trade_interval_seconds: int = Field(default=300, env="MIN_TRADE_INTERVAL_SECONDS")
    max_order_retries: int = Field(default=3, env="MAX_ORDER_RETRIES")
    
    # Testing
    paper_trading_min_days: int = Field(default=90, env="PAPER_TRADING_MIN_DAYS")
    min_simulated_trades: int = Field(default=100, env="MIN_SIMULATED_TRADES")
    live_test_initial_amount: float = Field(default=100, env="LIVE_TEST_INITIAL_AMOUNT")
    live_test_days: int = Field(default=30, env="LIVE_TEST_DAYS")
    
    # Email
    smtp_enabled: bool = Field(default=False, env="SMTP_ENABLED")
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(None, env="EMAIL_FROM")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Hugging Face / Render
    hf_space: bool = Field(default=False, env="HF_SPACE")
    use_real_websocket: bool = Field(default=False, env="USE_REAL_WEBSOCKET")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
