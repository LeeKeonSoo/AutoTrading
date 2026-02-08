"""
Constants used throughout the trading system.
"""

from enum import Enum


class TradingMode(str, Enum):
    """Trading modes."""
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class OrderSide(str, Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS_LIMIT = "stop_loss_limit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"


class PositionSide(str, Enum):
    """Position sides."""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class TradingAction(str, Enum):
    """LLM trading actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


class Timeframe(str, Enum):
    """Timeframes for candlestick data."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    HOUR_12 = "12h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


# Technical Indicator Parameters
INDICATOR_PARAMS = {
    "RSI": {
        "period": 14,
        "overbought": 70,
        "oversold": 30,
    },
    "MACD": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
    },
    "BOLLINGER_BANDS": {
        "period": 20,
        "std_dev": 2,
    },
    "ATR": {
        "period": 14,
    },
    "SMA": {
        "short": 20,
        "medium": 50,
        "long": 200,
    },
    "EMA": {
        "short": 12,
        "medium": 26,
        "long": 50,
    },
    "STOCHASTIC": {
        "k_period": 14,
        "d_period": 3,
        "overbought": 80,
        "oversold": 20,
    },
}

# Performance Metrics Thresholds
PERFORMANCE_THRESHOLDS = {
    "min_sharpe_ratio": 1.0,
    "max_drawdown_pct": 0.20,  # 20%
    "min_win_rate": 0.45,  # 45%
    "min_profit_factor": 1.5,
}

# API Configuration
API_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,  # seconds
    "timeout": 30,  # seconds
    "rate_limit_per_minute": 1200,
}

# Database
DATABASE_CONFIG = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600,
}

# Logging
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Binance Fee Tiers (as of 2024)
BINANCE_FEES = {
    "VIP0": {
        "maker": 0.001,  # 0.1%
        "taker": 0.001,  # 0.1%
    },
    "VIP1": {
        "maker": 0.0009,
        "taker": 0.001,
    },
    "BNB_DISCOUNT": 0.25,  # 25% discount with BNB
}

# LLM Configuration
LLM_CONFIG = {
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 1.0,
    "system_prompt_version": "v1.0",
}

# Circuit Breaker Settings
CIRCUIT_BREAKER = {
    "max_consecutive_losses": 3,
    "max_daily_loss_pct": 0.10,  # 10%
    "high_volatility_atr_multiplier": 3.0,
    "cooldown_period_hours": 24,
}

# Position Management
POSITION_CONFIG = {
    "min_position_value_usd": 10.0,
    "max_leverage": 1.0,  # No leverage by default
    "partial_close_enabled": True,
    "trailing_stop_activation_pct": 0.03,  # 3% profit
    "trailing_stop_distance_pct": 0.02,  # 2% trailing
}

# Backtesting
BACKTEST_CONFIG = {
    "initial_capital": 10000,  # USDT
    "slippage_pct": 0.0005,  # 0.05%
    "min_periods": 100,  # Minimum data points required
    "walk_forward_train_pct": 0.70,  # 70% train, 30% test
}

# Notification Settings
NOTIFICATION_CONFIG = {
    "notify_on_trade": True,
    "notify_on_error": True,
    "notify_on_daily_summary": True,
    "notify_on_large_pnl_pct": 0.05,  # 5% profit or loss
}
