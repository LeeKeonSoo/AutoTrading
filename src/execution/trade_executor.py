"""
Trade execution engine.
Handles order placement and position management.
"""

from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

from src.data.binance_client import BinanceClient
from src.config.settings import get_settings
from src.config.constants import TradingAction, OrderSide
from src.llm.decision_parser import TradingDecision


class TradeExecutor:
    """
    Executes trades on Binance based on decisions.
    """

    def __init__(self, client: Optional[BinanceClient] = None):
        """
        Initialize trade executor.

        Args:
            client: BinanceClient instance (creates new if None)
        """
        self.settings = get_settings()
        self.client = client or BinanceClient()
        self.current_position: Optional[Dict[str, Any]] = None
        self.open_orders: list = []

        logger.info(f"TradeExecutor initialized (mode: {self.settings.trading_mode})")

    def execute_decision(
        self,
        decision: TradingDecision,
        position_size: float,
    ) -> Dict[str, Any]:
        """
        Execute trading decision.

        Args:
            decision: Trading decision from LLM
            position_size: Position size to trade

        Returns:
            Execution result dictionary
        """
        if self.settings.trading_mode == "backtest":
            return self._simulate_execution(decision, position_size)

        # Live/Paper trading
        try:
            if decision.action == TradingAction.BUY:
                return self._execute_buy(decision, position_size)
            elif decision.action == TradingAction.SELL:
                return self._execute_sell(decision, position_size)
            elif decision.action == TradingAction.CLOSE:
                return self._execute_close()
            else:  # HOLD
                return {
                    "status": "hold",
                    "message": "No action taken",
                }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "status": "error",
                "message": str(e),
            }

    def _execute_buy(
        self,
        decision: TradingDecision,
        position_size: float,
    ) -> Dict[str, Any]:
        """Execute BUY order."""
        logger.info(f"Executing BUY: {position_size:.8f} {self.settings.trading_symbol}")

        # Get current price
        ticker = self.client.fetch_ticker(self.settings.trading_symbol)
        current_price = float(ticker["last"])

        # Place market order
        order = self.client.create_market_order(
            side=OrderSide.BUY,
            amount=position_size,
            symbol=self.settings.trading_symbol,
        )

        # Set stop-loss and take-profit
        stop_price = current_price * (1 - decision.stop_loss_pct)
        take_profit_price = current_price * (1 + decision.take_profit_pct)

        logger.info(
            f"Position opened at ${current_price:,.2f} "
            f"(SL: ${stop_price:,.2f}, TP: ${take_profit_price:,.2f})"
        )

        self.current_position = {
            "action": "BUY",
            "entry_price": current_price,
            "size": position_size,
            "stop_loss": stop_price,
            "take_profit": take_profit_price,
            "timestamp": datetime.now(),
            "order_id": order.get("id"),
        }

        return {
            "status": "success",
            "action": "BUY",
            "price": current_price,
            "size": position_size,
            "order": order,
        }

    def _execute_sell(
        self,
        decision: TradingDecision,
        position_size: float,
    ) -> Dict[str, Any]:
        """Execute SELL order (for spot: close long, for futures: open short)."""
        logger.info(f"Executing SELL: {position_size:.8f} {self.settings.trading_symbol}")

        ticker = self.client.fetch_ticker(self.settings.trading_symbol)
        current_price = float(ticker["last"])

        order = self.client.create_market_order(
            side=OrderSide.SELL,
            amount=position_size,
            symbol=self.settings.trading_symbol,
        )

        if self.settings.market_type == "futures":
            # For futures, SELL opens a short position
            stop_price = current_price * (1 + decision.stop_loss_pct)
            take_profit_price = current_price * (1 - decision.take_profit_pct)

            self.current_position = {
                "action": "SELL",
                "entry_price": current_price,
                "size": position_size,
                "stop_loss": stop_price,
                "take_profit": take_profit_price,
                "timestamp": datetime.now(),
                "order_id": order.get("id"),
            }
        else:
            # For spot, SELL closes the position
            self.current_position = None

        return {
            "status": "success",
            "action": "SELL",
            "price": current_price,
            "size": position_size,
            "order": order,
        }

    def _execute_close(self) -> Dict[str, Any]:
        """Close current position."""
        if not self.current_position:
            return {
                "status": "no_position",
                "message": "No position to close",
            }

        logger.info("Closing position")
        position = self.current_position
        ticker = self.client.fetch_ticker(self.settings.trading_symbol)
        current_price = float(ticker["last"])

        # Determine order side
        if position["action"] == "BUY":
            side = OrderSide.SELL
        else:
            side = OrderSide.BUY

        # Close position
        order = self.client.create_market_order(
            side=side,
            amount=position["size"],
            symbol=self.settings.trading_symbol,
        )

        # Calculate P&L
        if position["action"] == "BUY":
            pnl = (current_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - current_price) * position["size"]

        logger.info(f"Position closed. P&L: ${pnl:+,.2f}")

        self.current_position = None

        return {
            "status": "success",
            "action": "CLOSE",
            "entry_price": position["entry_price"],
            "exit_price": current_price,
            "pnl": pnl,
            "order": order,
        }

    def _simulate_execution(
        self,
        decision: TradingDecision,
        position_size: float,
    ) -> Dict[str, Any]:
        """Simulate execution for backtesting."""
        logger.debug(f"Simulating {decision.action.value}")

        # Get current price
        ticker = self.client.fetch_ticker(self.settings.trading_symbol)
        current_price = float(ticker["last"])

        return {
            "status": "simulated",
            "action": decision.action.value,
            "price": current_price,
            "size": position_size,
            "confidence": decision.confidence,
        }

    def check_stop_loss_take_profit(self) -> Optional[str]:
        """
        Check if stop-loss or take-profit is hit.

        Returns:
            "stop_loss", "take_profit", or None
        """
        if not self.current_position:
            return None

        ticker = self.client.fetch_ticker(self.settings.trading_symbol)
        current_price = float(ticker["last"])

        position = self.current_position

        if position["action"] == "BUY":
            if current_price <= position["stop_loss"]:
                logger.warning(f"Stop-loss hit at ${current_price:,.2f}")
                return "stop_loss"
            elif current_price >= position["take_profit"]:
                logger.info(f"Take-profit hit at ${current_price:,.2f}")
                return "take_profit"
        else:  # SHORT position
            if current_price >= position["stop_loss"]:
                logger.warning(f"Stop-loss hit at ${current_price:,.2f}")
                return "stop_loss"
            elif current_price <= position["take_profit"]:
                logger.info(f"Take-profit hit at ${current_price:,.2f}")
                return "take_profit"

        return None

    def get_position_pnl(self) -> Optional[float]:
        """
        Get current unrealized P&L.

        Returns:
            Unrealized P&L or None if no position
        """
        if not self.current_position:
            return None

        ticker = self.client.fetch_ticker(self.settings.trading_symbol)
        current_price = float(ticker["last"])

        position = self.current_position
        if position["action"] == "BUY":
            pnl = (current_price - position["entry_price"]) * position["size"]
        else:
            pnl = (position["entry_price"] - current_price) * position["size"]

        return pnl


if __name__ == "__main__":
    # Test trade executor
    from src.llm.decision_parser import TradingDecision, TradingAction

    executor = TradeExecutor()

    print("\n=== Trade Executor Test ===")
    print(f"Mode: {executor.settings.trading_mode}")
    print(f"Market: {executor.settings.market_type}")

    # Test decision
    decision = TradingDecision(
        action=TradingAction.BUY,
        confidence=0.85,
        reasoning="Test trade",
        stop_loss_pct=0.02,
        take_profit_pct=0.05,
    )

    result = executor.execute_decision(decision, position_size=0.001)
    print(f"\nExecution result:")
    print(f"  Status: {result['status']}")
    print(f"  Action: {result.get('action', 'N/A')}")
    print(f"  Price: ${result.get('price', 0):,.2f}")
