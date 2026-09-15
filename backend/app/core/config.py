from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os
import secrets

class Settings(BaseSettings):
    # ============================================
    # Application
    # ============================================
    app_name: str = "JADOTA AI"
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(
        default=secrets.token_urlsafe(32),
        env="SECRET_KEY"
    )
    
    # ============================================
    # API
    # ============================================
    api_version: str = Field(default="v1", env="API_VERSION")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # 🔥 FIX: Use Union type to handle both string and list
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
        env="CORS_ORIGINS"
    )
    
    allowed_hosts: Union[str, List[str]] = Field(
        default="*",
        env="ALLOWED_HOSTS"
    )
    
    # ============================================
    # Database
    # ============================================
    database_url: str = Field(
        default="sqlite:///./jadota.db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    
    # ============================================
    # Firebase - All optional
    # ============================================
    firebase_api_key: Optional[str] = Field(None, env="FIREBASE_API_KEY")
    firebase_auth_domain: Optional[str] = Field(None, env="FIREBASE_AUTH_DOMAIN")
    firebase_project_id: Optional[str] = Field(None, env="FIREBASE_PROJECT_ID")
    firebase_storage_bucket: Optional[str] = Field(None, env="FIREBASE_STORAGE_BUCKET")
    firebase_messaging_sender_id: Optional[str] = Field(None, env="FIREBASE_MESSAGING_SENDER_ID")
    firebase_app_id: Optional[str] = Field(None, env="FIREBASE_APP_ID")
    firebase_measurement_id: Optional[str] = Field(None, env="FIREBASE_MEASUREMENT_ID")
    firebase_private_key_id: Optional[str] = Field(None, env="FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: Optional[str] = Field(None, env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = Field(None, env="FIREBASE_CLIENT_EMAIL")
    firebase_client_id: Optional[str] = Field(None, env="FIREBASE_CLIENT_ID")
    firebase_auth_uri: Optional[str] = Field(None, env="FIREBASE_AUTH_URI")
    firebase_token_uri: Optional[str] = Field(None, env="FIREBASE_TOKEN_URI")
    firebase_auth_provider_cert_url: Optional[str] = Field(None, env="FIREBASE_AUTH_PROVIDER_CERT_URL")
    firebase_client_cert_url: Optional[str] = Field(None, env="FIREBASE_CLIENT_CERT_URL")
    
    # ============================================
    # Redis
    # ============================================
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # ============================================
    # JWT
    # ============================================
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(
        default=60 * 24,  # 24 hours
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        env="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # ============================================
    # Encryption
    # ============================================
    encryption_key: str = Field(
        default=secrets.token_urlsafe(32),
        env="ENCRYPTION_KEY"
    )
    
    # ============================================
    # Bitget
    # ============================================
    bitget_api_key: Optional[str] = Field(None, env="BITGET_API_KEY")
    bitget_secret: Optional[str] = Field(None, env="BITGET_SECRET")
    bitget_passphrase: Optional[str] = Field(None, env="BITGET_PASSPHRASE")
    bitget_api_base: str = Field(default="https://api.bitget.com", env="BITGET_API_BASE")
    bitget_ws_base: str = Field(default="wss://ws.bitget.com/v1/stream", env="BITGET_WS_BASE")
    bitget_default_symbols: Union[str, List[str]] = Field(
        default="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT",
        env="BITGET_DEFAULT_SYMBOLS"
    )
    
    # ============================================
    # Payment
    # ============================================
    jadota_wallet_address: Optional[str] = Field(
        default="0x0000000000000000000000000000000000000000",
        env="JADOTA_WALLET_ADDRESS"
    )
    jadota_wallet_network: str = Field(default="BEP20", env="JADOTA_WALLET_NETWORK")
    min_payment_confirmations: int = Field(default=6, env="MIN_PAYMENT_CONFIRMATIONS")
    
    # ============================================
    # Risk Management
    # ============================================
    default_max_risk_per_trade: float = Field(default=2.0, env="DEFAULT_MAX_RISK_PER_TRADE")
    default_max_daily_loss: float = Field(default=5.0, env="DEFAULT_MAX_DAILY_LOSS")
    default_max_weekly_loss: float = Field(default=10.0, env="DEFAULT_MAX_WEEKLY_LOSS")
    max_allowed_drawdown: float = Field(default=15.0, env="MAX_ALLOWED_DRAWDOWN")
    
    # ============================================
    # Performance Targets
    # ============================================
    target_sharpe_ratio: float = Field(default=1.0, env="TARGET_SHARPE_RATIO")
    min_profit_factor: float = Field(default=1.5, env="MIN_PROFIT_FACTOR")
    min_win_rate: float = Field(default=55.0, env="MIN_WIN_RATE")
    max_win_rate: float = Field(default=65.0, env="MAX_WIN_RATE")
    
    # ============================================
    # Trading
    # ============================================
    max_position_days: int = Field(default=14, env="MAX_POSITION_DAYS")
    min_trade_interval_seconds: int = Field(default=300, env="MIN_TRADE_INTERVAL_SECONDS")
    max_order_retries: int = Field(default=3, env="MAX_ORDER_RETRIES")
    
    # ============================================
    # Testing
    # ============================================
    paper_trading_min_days: int = Field(default=90, env="PAPER_TRADING_MIN_DAYS")
    min_simulated_trades: int = Field(default=100, env="MIN_SIMULATED_TRADES")
    live_test_initial_amount: float = Field(default=100, env="LIVE_TEST_INITIAL_AMOUNT")
    live_test_days: int = Field(default=30, env="LIVE_TEST_DAYS")
    
    # ============================================
    # Email
    # ============================================
    smtp_enabled: bool = Field(default=False, env="SMTP_ENABLED")
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(None, env="EMAIL_FROM")
    
    # ============================================
    # Logging
    # ============================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ============================================
    # Hugging Face / Render
    # ============================================
    hf_space: bool = Field(default=False, env="HF_SPACE")
    use_real_websocket: bool = Field(default=False, env="USE_REAL_WEBSOCKET")
    
    # ============================================
    # 🔥 Helper Properties - Parse to lists
    # ============================================
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.cors_origins, str):
            if self.cors_origins == "*":
                return ["*"]
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return self.cors_origins
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a list"""
        if isinstance(self.allowed_hosts, str):
            if self.allowed_hosts == "*":
                return ["*"]
            return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        return self.allowed_hosts
    
    @property
    def bitget_default_symbols_list(self) -> List[str]:
        """Get Bitget symbols as a list"""
        if isinstance(self.bitget_default_symbols, str):
            return [s.strip() for s in self.bitget_default_symbols.split(",") if s.strip()]
        return self.bitget_default_symbols

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

# ============================================
# Create settings instance
# ============================================
settings = Settings()

# ============================================
# Helper Functions
# ============================================
def get_cors_origins() -> List[str]:
    """Get CORS origins as a list"""
    return settings.cors_origins_list

def get_allowed_hosts() -> List[str]:
    """Get allowed hosts as a list"""
    return settings.allowed_hosts_list

def get_bitget_symbols() -> List[str]:
    """Get Bitget symbols as a list"""
    return settings.bitget_default_symbols_list

def is_production() -> bool:
    """Check if running in production"""
    return settings.app_env.lower() == "production"

def is_development() -> bool:
    """Check if running in development"""
    return settings.app_env.lower() == "development"

def is_staging() -> bool:
    """Check if running in staging"""
    return settings.app_env.lower() == "staging"

# ============================================
# Database URL Helper
# ============================================
def get_database_url() -> str:
    """Get the database URL"""
    return settings.database_url

def is_sqlite() -> bool:
    """Check if using SQLite"""
    return "sqlite" in settings.database_url

def is_postgres() -> bool:
    """Check if using PostgreSQL"""
    return "postgresql" in settings.database_url