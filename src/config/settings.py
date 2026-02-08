"""
Settings management using Pydantic for type-safe configuration.
"""

from typing import Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # Binance API Configuration
    # ============================================
    binance_api_key: str = Field(..., description="Binance API key")
    binance_api_secret: str = Field(..., description="Binance API secret")
    binance_testnet: bool = Field(default=True, description="Use Binance testnet")

    # ============================================
    # Anthropic API Configuration
    # ============================================
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20240620",
        description="Claude model to use"
    )
    anthropic_max_tokens: int = Field(default=4096, description="Max tokens per request")

    # ============================================
    # Trading Configuration
    # ============================================
    trading_symbol: str = Field(default="BTC/USDT", description="Trading pair")
    trading_mode: Literal["backtest", "paper", "live"] = Field(
        default="backtest",
        description="Trading mode"
    )
    trading_timeframe: str = Field(default="1h", description="Timeframe for analysis")

    # ============================================
    # Risk Management
    # ============================================
    risk_per_trade: float = Field(
        default=0.02,
        ge=0.001,
        le=0.10,
        description="Risk per trade (0.02 = 2%)"
    )
    max_position_size: float = Field(
        default=0.05,
        ge=0.01,
        le=1.0,
        description="Max position size (0.05 = 5%)"
    )
    max_daily_loss: float = Field(
        default=0.10,
        ge=0.01,
        le=0.50,
        description="Max daily loss (0.10 = 10%)"
    )
    max_open_positions: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Max open positions"
    )
    default_stop_loss_pct: float = Field(
        default=0.02,
        ge=0.005,
        le=0.20,
        description="Default stop loss percentage"
    )
    default_take_profit_pct: float = Field(
        default=0.05,
        ge=0.01,
        le=0.50,
        description="Default take profit percentage"
    )
    min_confidence: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for LLM decisions"
    )

    # ============================================
    # Backtesting Configuration
    # ============================================
    backtest_initial_capital: float = Field(
        default=10000,
        ge=100,
        description="Initial capital for backtesting"
    )
    backtest_start_date: str = Field(
        default="2024-01-01",
        description="Backtest start date (YYYY-MM-DD)"
    )
    backtest_end_date: str = Field(
        default="now",
        description="Backtest end date (YYYY-MM-DD or 'now')"
    )
    trading_fee: float = Field(
        default=0.001,
        ge=0.0,
        le=0.01,
        description="Trading fee (0.001 = 0.1%)"
    )
    slippage: float = Field(
        default=0.0005,
        ge=0.0,
        le=0.01,
        description="Slippage (0.0005 = 0.05%)"
    )

    # ============================================
    # Database Configuration
    # ============================================
    database_url: str = Field(
        default="sqlite:///data/trading.db",
        description="Database connection URL"
    )

    # ============================================
    # Monitoring & Notifications
    # ============================================
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Telegram chat ID")
    enable_telegram: bool = Field(default=False, description="Enable Telegram notifications")

    email_enabled: bool = Field(default=False, description="Enable email notifications")
    email_host: Optional[str] = Field(default=None, description="Email SMTP host")
    email_port: Optional[int] = Field(default=587, description="Email SMTP port")
    email_username: Optional[str] = Field(default=None, description="Email username")
    email_password: Optional[str] = Field(default=None, description="Email password")
    email_to: Optional[str] = Field(default=None, description="Email recipient")

    # ============================================
    # Logging Configuration
    # ============================================
    log_level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="logs/trading.log", description="Log file path")
    log_max_size: int = Field(default=10, description="Max log file size (MB)")
    log_backup_count: int = Field(default=5, description="Number of backup log files")

    # ============================================
    # Advanced Settings
    # ============================================
    api_rate_limit: int = Field(
        default=1200,
        ge=60,
        description="API rate limit (requests per minute)"
    )
    api_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Retry attempts for failed API calls"
    )
    api_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="API timeout (seconds)"
    )
    cache_expiration: int = Field(
        default=60,
        ge=0,
        description="Cache expiration for market data (seconds)"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # ============================================
    # Validators
    # ============================================

    @field_validator("trading_symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate trading symbol format."""
        if "/" not in v:
            raise ValueError("Trading symbol must be in format 'BASE/QUOTE' (e.g., 'BTC/USDT')")
        return v.upper()

    @field_validator("backtest_start_date", "backtest_end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format."""
        if v.lower() != "now":
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in format YYYY-MM-DD or 'now'")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    # ============================================
    # Computed Properties
    # ============================================

    @property
    def is_live_trading(self) -> bool:
        """Check if running in live trading mode."""
        return self.trading_mode == "live" and not self.binance_testnet

    @property
    def is_testnet(self) -> bool:
        """Check if using testnet."""
        return self.binance_testnet

    @property
    def binance_base_url(self) -> str:
        """Get Binance API base URL."""
        if self.binance_testnet:
            return "https://testnet.binance.vision"
        return "https://api.binance.com"

    @property
    def telegram_enabled_valid(self) -> bool:
        """Check if Telegram is properly configured."""
        return (
            self.enable_telegram
            and self.telegram_bot_token is not None
            and self.telegram_chat_id is not None
        )

    @property
    def email_enabled_valid(self) -> bool:
        """Check if email is properly configured."""
        return (
            self.email_enabled
            and self.email_host is not None
            and self.email_username is not None
            and self.email_password is not None
            and self.email_to is not None
        )

    # ============================================
    # Methods
    # ============================================

    def get_backtest_end_datetime(self) -> datetime:
        """Get backtest end date as datetime object."""
        if self.backtest_end_date.lower() == "now":
            return datetime.now()
        return datetime.strptime(self.backtest_end_date, "%Y-%m-%d")

    def get_backtest_start_datetime(self) -> datetime:
        """Get backtest start date as datetime object."""
        return datetime.strptime(self.backtest_start_date, "%Y-%m-%d")

    def validate_settings(self) -> list[str]:
        """
        Validate all settings and return list of warnings/errors.

        Returns:
            List of warning/error messages
        """
        warnings = []

        # Check for live trading warnings
        if self.is_live_trading:
            warnings.append("⚠️  WARNING: Live trading mode enabled! Real money at risk!")

        # Check risk settings
        if self.risk_per_trade > 0.05:
            warnings.append(f"⚠️  High risk per trade: {self.risk_per_trade*100}% (recommended: ≤5%)")

        if self.max_position_size > 0.20:
            warnings.append(f"⚠️  Large max position size: {self.max_position_size*100}% (recommended: ≤20%)")

        if self.min_confidence < 0.60:
            warnings.append(f"⚠️  Low confidence threshold: {self.min_confidence} (recommended: ≥0.6)")

        # Check API keys
        if not self.binance_testnet and self.is_live_trading:
            if "your_" in self.binance_api_key.lower():
                warnings.append("❌ ERROR: Binance API key not configured!")

        if "your_" in self.anthropic_api_key.lower():
            warnings.append("❌ ERROR: Anthropic API key not configured!")

        return warnings

    def print_summary(self) -> None:
        """Print configuration summary."""
        print("=" * 60)
        print("🤖 Auto Trading Bot - Configuration Summary")
        print("=" * 60)
        print(f"Trading Mode:     {self.trading_mode.upper()}")
        print(f"Testnet:          {self.binance_testnet}")
        print(f"Symbol:           {self.trading_symbol}")
        print(f"Timeframe:        {self.trading_timeframe}")
        print(f"Risk per Trade:   {self.risk_per_trade*100}%")
        print(f"Max Position:     {self.max_position_size*100}%")
        print(f"Stop Loss:        {self.default_stop_loss_pct*100}%")
        print(f"Take Profit:      {self.default_take_profit_pct*100}%")
        print(f"Min Confidence:   {self.min_confidence}")
        print(f"LLM Model:        {self.anthropic_model}")
        print("=" * 60)

        # Print warnings
        warnings = self.validate_settings()
        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  {warning}")
            print()


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings singleton.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings


if __name__ == "__main__":
    # Test settings loading
    settings = get_settings()
    settings.print_summary()
