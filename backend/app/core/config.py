from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import secrets


class Settings(BaseSettings):
    """
    Application settings.

    pydantic-settings v2 automatically maps env vars to fields (case-insensitive).
    Real env vars (Render) override .env file values.
    """

    # ============================================
    # Application
    # ============================================
    app_name: str = "JADOTA AI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # ============================================
    # API
    # ============================================
    api_version: str = "v1"
    api_prefix: str = "/api/v1"
    frontend_url: str = "http://localhost:3000"

    cors_origins: Union[str, List[str]] = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    allowed_hosts: Union[str, List[str]] = "*"

    # ============================================
    # Database
    # ============================================
    database_url: str = "sqlite:///./jadota.db"
    database_pool_size: int = 20

    # ============================================
    # Telegram
    # ============================================
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_group_chat_id: Optional[str] = None

    # ============================================
    # Admin bootstrap
    # ============================================
    admin_bootstrap_key: Optional[str] = None

    # ============================================
    # Firebase — All optional
    # ============================================
    firebase_api_key: Optional[str] = None
    firebase_auth_domain: Optional[str] = None
    firebase_project_id: Optional[str] = None
    firebase_storage_bucket: Optional[str] = None
    firebase_messaging_sender_id: Optional[str] = None
    firebase_app_id: Optional[str] = None
    firebase_measurement_id: Optional[str] = None
    firebase_private_key_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    firebase_client_id: Optional[str] = None
    firebase_auth_uri: Optional[str] = None
    firebase_token_uri: Optional[str] = None
    firebase_auth_provider_cert_url: Optional[str] = None
    firebase_client_cert_url: Optional[str] = None

    # ============================================
    # Redis
    # ============================================
    redis_url: str = "redis://localhost:6379/0"

    # ============================================
    # JWT
    # ============================================
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24  # 24 hours
    jwt_refresh_token_expire_days: int = 7

    # ============================================
    # Encryption
    # ============================================
    encryption_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # ============================================
    # Bitget
    # ============================================
    bitget_api_key: Optional[str] = None
    bitget_secret: Optional[str] = None
    bitget_passphrase: Optional[str] = None
    bitget_api_base: str = "https://api.bitget.com"
    bitget_ws_base: str = "wss://ws.bitget.com/v1/stream"
    bitget_default_symbols: Union[str, List[str]] = (
        "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT"
    )

    # ============================================
    # Payment
    # ============================================
    jadota_wallet_address: str = (
        "0xa0ec55ce3f6916571695d5b8d8e507887a405782"
    )
    jadota_wallet_network: str = "BEP20"
    min_payment_confirmations: int = 6

    # 🔥 Blockchain verification API keys — OPTIONAL
    # Priority order for BEP20: NodeReal → BscScan → manual admin approval
    # Priority order for ERC20: Etherscan → manual admin approval
    # If missing, payments fall back to admin manual approval.
    nodereal_api_key: Optional[str] = None     # https://dashboard.nodereal.io
    bscscan_api_key: Optional[str] = None      # https://bscscan.com/myapikey (deprecated)
    etherscan_api_key: Optional[str] = None    # https://etherscan.io/myapikey

    # ============================================
    # Risk Management
    # ============================================
    default_max_risk_per_trade: float = 2.0
    default_max_daily_loss: float = 5.0
    default_max_weekly_loss: float = 10.0
    max_allowed_drawdown: float = 15.0

    # ============================================
    # Performance Targets
    # ============================================
    target_sharpe_ratio: float = 1.0
    min_profit_factor: float = 1.5
    min_win_rate: float = 55.0
    max_win_rate: float = 65.0

    # ============================================
    # Trading
    # ============================================
    max_position_days: int = 14
    min_trade_interval_seconds: int = 300
    max_order_retries: int = 3

    # ============================================
    # Testing
    # ============================================
    paper_trading_min_days: int = 90
    min_simulated_trades: int = 100
    live_test_initial_amount: float = 100
    live_test_days: int = 30

    # ============================================
    # Email
    # ============================================
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    # ============================================
    # Logging
    # ============================================
    log_level: str = "INFO"

    # ============================================
    # Hugging Face / Render
    # ============================================
    hf_space: bool = False
    use_real_websocket: bool = False

    # ============================================
    # Helper Properties — Parse to lists
    # ============================================
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, str):
            if self.cors_origins == "*":
                return ["*"]
            return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return list(self.cors_origins)

    @property
    def allowed_hosts_list(self) -> List[str]:
        if isinstance(self.allowed_hosts, str):
            if self.allowed_hosts == "*":
                return ["*"]
            return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        return list(self.allowed_hosts)

    @property
    def bitget_default_symbols_list(self) -> List[str]:
        if isinstance(self.bitget_default_symbols, str):
            return [s.strip() for s in self.bitget_default_symbols.split(",") if s.strip()]
        return list(self.bitget_default_symbols)

    # ============================================
    # pydantic-settings v2 config
    # ============================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ============================================
# Create settings instance
# ============================================
settings = Settings()


# ============================================
# Helper Functions
# ============================================
def get_cors_origins() -> List[str]:
    return settings.cors_origins_list


def get_allowed_hosts() -> List[str]:
    return settings.allowed_hosts_list


def get_bitget_symbols() -> List[str]:
    return settings.bitget_default_symbols_list


def is_production() -> bool:
    return settings.app_env.lower() == "production"


def is_development() -> bool:
    return settings.app_env.lower() == "development"


def is_staging() -> bool:
    return settings.app_env.lower() == "staging"


def get_database_url() -> str:
    return settings.database_url


def is_sqlite() -> bool:
    return "sqlite" in settings.database_url


def is_postgres() -> bool:
    return "postgresql" in settings.database_url