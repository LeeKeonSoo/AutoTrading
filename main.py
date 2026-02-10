#!/usr/bin/env python3
"""
Main entry point for the Auto Trading Bot.
"""

import sys
import time
from loguru import logger
from datetime import datetime

from src.config.settings import get_settings
from src.strategy.llm_strategy import LLMTradingStrategy
from src.risk.risk_manager import RiskManager
from src.execution.trade_executor import TradeExecutor
from src.data.binance_client import BinanceClient


def setup_logging():
    """Configure logging."""
    settings = get_settings()

    logger.remove()  # Remove default handler

    # Console output
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    # File output
    logger.add(
        settings.log_file,
        level="DEBUG",
        rotation=f"{settings.log_max_size} MB",
        retention=settings.log_backup_count,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info("Logging configured")


def run_trading_bot():
    """Main trading bot loop."""
    settings = get_settings()

    # Print configuration
    settings.print_summary()

    # Validate settings
    warnings = settings.validate_settings()
    if any("ERROR" in w for w in warnings):
        logger.error("Critical configuration errors found. Exiting.")
        return

    # Initialize components
    logger.info("Initializing trading bot components...")

    client = BinanceClient()
    if not client.check_connection():
        logger.error("Failed to connect to Binance. Exiting.")
        return

    strategy = LLMTradingStrategy(
        market_data=None,  # Will create its own
        gemini_client=None,  # Will create its own
    )

    risk_manager = RiskManager()
    executor = TradeExecutor(client=client)

    logger.info("✅ All components initialized successfully")

    # Get initial account balance
    quote_currency = settings.trading_symbol.split("/")[1]
    balance = None
    try:
        spot_balance = client.fetch_balance("spot")
        spot_free = float(spot_balance.get("free", {}).get(quote_currency, 0))
        logger.info(f"Spot free balance: {spot_free:,.2f} {quote_currency}")
    except Exception as e:
        logger.warning(f"Failed to fetch spot balance: {e}")
        spot_free = 0.0

    try:
        futures_balance = client.fetch_balance("future")
        futures_free = float(futures_balance.get("free", {}).get(quote_currency, 0))
        logger.info(f"Futures free balance: {futures_free:,.2f} {quote_currency}")
    except Exception as e:
        logger.warning(f"Failed to fetch futures balance: {e}")
        futures_free = 0.0

    if settings.market_type == "futures":
        balance = futures_balance if "futures_balance" in locals() else None
        account_balance = futures_free
    else:
        balance = spot_balance if "spot_balance" in locals() else None
        account_balance = spot_free

    logger.info(f"Account balance: {account_balance:,.2f} {quote_currency}")

    if account_balance <= 0:
        logger.error("Insufficient balance. Exiting.")
        return

    # Main trading loop
    logger.info("🚀 Starting trading loop...")
    logger.info(f"Mode: {settings.trading_mode.upper()}")
    logger.info(f"Market: {settings.market_type.upper()}")
    logger.info(f"Symbol: {settings.trading_symbol}")
    logger.info(f"Timeframe: {settings.trading_timeframe}")

    iteration = 0
    while True:
        try:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration #{iteration} - {datetime.now()}")
            logger.info(f"{'='*60}")

            # Check stop-loss / take-profit
            if executor.current_position:
                sl_tp = executor.check_stop_loss_take_profit()
                if sl_tp:
                    logger.warning(f"{sl_tp.upper()} triggered!")
                    result = executor._execute_close()
                    if result["status"] == "success":
                        risk_manager.update_daily_pnl(result["pnl"])
                        strategy.record_trade(
                            action="CLOSE",
                            entry_price=result["entry_price"],
                            exit_price=result["exit_price"],
                            pnl=result["pnl"],
                        )

            # Get trading decision from LLM
            decision = strategy.analyze_and_decide()

            logger.info(f"\n📊 Decision: {decision.action.value}")
            logger.info(f"   Confidence: {decision.confidence:.1%}")
            logger.info(f"   Reasoning: {decision.reasoning}")

            # Validate decision with risk manager
            is_valid, reason = risk_manager.validate_decision(
                decision=decision,
                account_balance=account_balance,
                current_position=executor.current_position,
            )

            if not is_valid:
                logger.warning(f"⚠️  Decision rejected: {reason}")
                time.sleep(60)  # Wait before next iteration
                continue

            # Calculate position size
            if decision.action.value in ["BUY", "SELL"]:
                current_price = strategy.market_data.get_current_price()
                position_size = risk_manager.calculate_position_size(
                    account_balance=account_balance,
                    entry_price=current_price,
                    stop_loss_pct=decision.stop_loss_pct,
                )

                # Execute trade
                logger.info(f"\n💰 Executing {decision.action.value}...")
                result = executor.execute_decision(decision, position_size)

                if result["status"] == "success":
                    logger.success(f"✅ Trade executed successfully!")
                    logger.info(f"   Price: ${result['price']:,.2f}")
                    logger.info(f"   Size: {result['size']:.8f}")

                    strategy.update_position(
                        action=decision.action.value,
                        entry_price=result["price"],
                        size=result["size"],
                    )
                else:
                    logger.error(f"❌ Trade execution failed: {result.get('message')}")

            # Show current position
            if executor.current_position:
                pnl = executor.get_position_pnl()
                logger.info(f"\n📍 Current Position:")
                logger.info(f"   Type: {executor.current_position['action']}")
                logger.info(f"   Entry: ${executor.current_position['entry_price']:,.2f}")
                logger.info(f"   Size: {executor.current_position['size']:.8f}")
                logger.info(f"   Unrealized P&L: ${pnl:+,.2f}")

            # Show risk status
            risk_status = risk_manager.get_risk_status()
            logger.info(f"\n⚖️  Risk Status:")
            logger.info(f"   Daily P&L: ${risk_status['daily_pnl']:+,.2f}")
            logger.info(f"   Consecutive Losses: {risk_status['consecutive_losses']}")
            logger.info(f"   Trading Halted: {risk_status['trading_halted']}")

            # Wait before next iteration
            # In real trading, this should be the timeframe duration
            if settings.trading_mode == "backtest":
                logger.info("\n⏸️  Backtest mode - stopping after one iteration")
                break
            else:
                wait_seconds = 3600  # 1 hour for 1h timeframe
                logger.info(f"\n⏳ Waiting {wait_seconds}s until next analysis...")
                time.sleep(wait_seconds)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Interrupted by user. Shutting down...")
            break
        except Exception as e:
            logger.exception(f"❌ Error in main loop: {e}")
            time.sleep(60)  # Wait before retrying

    logger.info("🛑 Trading bot stopped")


def main():
    """Entry point."""
    try:
        setup_logging()
        logger.info("=" * 60)
        logger.info("🤖 AUTO TRADING BOT STARTING")
        logger.info("=" * 60)

        run_trading_bot()

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
