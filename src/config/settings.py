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
    binance_api_key: Optional[str] = Field(default=None, description="Binance live API key")
    binance_api_secret: Optional[str] = Field(default=None, description="Binance live API secret")
    binance_demo_api_key: Optional[str] = Field(default=None, description="Binance demo API key")
    binance_demo_api_secret: Optional[str] = Field(default=None, description="Binance demo API secret")

    # ============================================
    # Google Gemini API Configuration
    # ============================================
    gemini_api_key: str = Field(..., description="Gemini API key")
    gemini_model: str = Field(
        default="gemini-3-flash-preview",
        description="Gemini model to use"
    )
    gemini_max_tokens: int = Field(default=4096, description="Max tokens per request")
    gemini_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for response generation"
    )

    # ============================================
    # Trading Configuration
    # ============================================
    trading_symbol: str = Field(default="BTC/USDT", description="Trading pair")
    market_type: Literal["spot", "futures"] = Field(
        default="spot",
        description="Market type (spot or futures)"
    )
    leverage: int = Field(
        default=1,
        ge=1,
        le=125,
        description="Leverage for futures trading (1-125x)"
    )
    margin_mode: Literal["isolated", "cross"] = Field(
        default="isolated",
        description="Margin mode for futures"
    )
    trading_mode: Literal["live", "demo", "backtest"] = Field(
        default="demo",
        description="Trading mode: live (real money), demo (Binance Demo Trading), backtest"
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
        return self.trading_mode == "live"

    @property
    def is_demo_mode(self) -> bool:
        """Check if using Binance Demo Trading."""
        return self.trading_mode == "demo"

    @property
    def binance_base_url(self) -> str:
        """Get Binance API base URL."""
        if self.trading_mode == "demo":
            return "https://demo-api.binance.com"
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
            warnings.append("⚠️  WARNING: TRADING_MODE=live. Real money at risk!")

        # Check risk settings
        if self.risk_per_trade > 0.05:
            warnings.append(f"⚠️  High risk per trade: {self.risk_per_trade*100}% (recommended: ≤5%)")

        if self.max_position_size > 0.20:
            warnings.append(f"⚠️  Large max position size: {self.max_position_size*100}% (recommended: ≤20%)")

        if self.min_confidence < 0.60:
            warnings.append(f"⚠️  Low confidence threshold: {self.min_confidence} (recommended: ≥0.6)")

        # Check API keys
        if self.trading_mode == "demo":
            if not self.binance_demo_api_key or not self.binance_demo_api_secret:
                warnings.append("❌ ERROR: Demo API keys not configured!")
            elif "your_" in self.binance_demo_api_key.lower():
                warnings.append("❌ ERROR: Demo API key not configured!")
        elif self.trading_mode == "live":
            if not self.binance_api_key or not self.binance_api_secret:
                warnings.append("❌ ERROR: Binance live API keys not configured!")
            elif "your_" in self.binance_api_key.lower():
                warnings.append("❌ ERROR: Binance live API key not configured!")

        if "your_" in self.gemini_api_key.lower():
            warnings.append("❌ ERROR: Gemini API key not configured!")

        # Check futures trading warnings
        if self.market_type == "futures":
            warnings.append("⚠️  FUTURES TRADING ENABLED - Higher risk of liquidation!")
            if self.leverage > 10:
                warnings.append(f"⚠️  HIGH LEVERAGE: {self.leverage}x - Extreme risk!")
            if self.margin_mode == "cross":
                warnings.append("⚠️  CROSS MARGIN - Entire account balance at risk!")

        return warnings

    def print_summary(self) -> None:
        """Print configuration summary."""
        print("=" * 60)
        print("🤖 Auto Trading Bot - Configuration Summary")
        print("=" * 60)
        print(f"Trading Mode:     {self.trading_mode.upper()} ({'Binance Demo Trading' if self.is_demo_mode else 'LIVE TRADING' if self.is_live_trading else 'Backtest'})")
        print(f"Market Type:      {self.market_type.upper()}")
        if self.market_type == "futures":
            print(f"Leverage:         {self.leverage}x")
            print(f"Margin Mode:      {self.margin_mode.upper()}")
        print(f"Symbol:           {self.trading_symbol}")
        print(f"Timeframe:        {self.trading_timeframe}")
        print(f"Risk per Trade:   {self.risk_per_trade*100}%")
        print(f"Max Position:     {self.max_position_size*100}%")
        print(f"Stop Loss:        {self.default_stop_loss_pct*100}%")
        print(f"Take Profit:      {self.default_take_profit_pct*100}%")
        print(f"Min Confidence:   {self.min_confidence}")
        print(f"LLM Model:        {self.gemini_model}")
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
