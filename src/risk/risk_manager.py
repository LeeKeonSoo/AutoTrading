"""
Risk management system for protecting capital.
"""

from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime, timedelta

from src.config.settings import get_settings
from src.llm.decision_parser import TradingDecision
from src.config.constants import TradingAction


class RiskManager:
    """
    Manages risk across all trading operations.
    """

    def __init__(self):
        """Initialize risk manager."""
        self.settings = get_settings()
        self.daily_pnl: float = 0.0
        self.daily_reset_time: datetime = datetime.now()
        self.consecutive_losses: int = 0
        self.is_trading_halted: bool = False

        logger.info("RiskManager initialized")

    def validate_decision(
        self,
        decision: TradingDecision,
        account_balance: float,
        current_position: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, str]:
        """
        Validate if decision passes risk checks.

        Args:
            decision: Trading decision to validate
            account_balance: Current account balance
            current_position: Current position (if any)

        Returns:
            (is_valid, reason) tuple
        """
        # Reset daily P&L if new day
        self._check_daily_reset()

        # Check if trading is halted
        if self.is_trading_halted:
            return False, "Trading halted due to risk limits"

        # Check daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / account_balance
        if daily_loss_pct >= self.settings.max_daily_loss:
            self.is_trading_halted = True
            logger.error(
                f"Daily loss limit reached: {daily_loss_pct:.1%} "
                f"(limit: {self.settings.max_daily_loss:.1%})"
            )
            return False, "Daily loss limit exceeded"

        # Check consecutive losses
        if self.consecutive_losses >= 3:
            logger.warning(f"3 consecutive losses - being cautious")
            if decision.action in [TradingAction.BUY, TradingAction.SELL]:
                if decision.confidence < 0.85:
                    return False, "Confidence too low after consecutive losses"

        # Validate position size
        if decision.action in [TradingAction.BUY, TradingAction.SELL]:
            max_position_value = account_balance * self.settings.max_position_size
            # This is a simplified check - actual implementation would calculate real position size
            logger.debug(f"Max position value: ${max_position_value:,.2f}")

        return True, "Risk checks passed"

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_pct: float,
    ) -> float:
        """
        Calculate position size based on risk parameters.

        Args:
            account_balance: Current account balance
            entry_price: Entry price
            stop_loss_pct: Stop loss percentage

        Returns:
            Position size in base currency
        """
        # Risk per trade in dollars
        risk_amount = account_balance * self.settings.risk_per_trade

        # Position size calculation
        # risk_amount = position_size * entry_price * stop_loss_pct
        # position_size = risk_amount / (entry_price * stop_loss_pct)
        position_size = risk_amount / (entry_price * stop_loss_pct)

        # Apply max position size limit
        max_position_size = (
            account_balance * self.settings.max_position_size / entry_price
        )
        position_size = min(position_size, max_position_size)

        # Apply leverage if futures
        if self.settings.market_type == "futures":
            position_size *= self.settings.leverage

        logger.info(
            f"Calculated position size: {position_size:.8f} "
            f"(risk: ${risk_amount:.2f}, SL: {stop_loss_pct:.1%})"
        )

        return position_size

    def update_daily_pnl(self, pnl: float) -> None:
        """
        Update daily P&L tracking.

        Args:
            pnl: Profit/loss from trade
        """
        self.daily_pnl += pnl

        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        logger.info(
            f"Daily P&L: ${self.daily_pnl:+.2f} "
            f"(Consecutive losses: {self.consecutive_losses})"
        )

    def _check_daily_reset(self) -> None:
        """Reset daily counters if new day."""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            logger.info("New day - resetting daily P&L and trading halt")
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.is_trading_halted = False
            self.daily_reset_time = now

    def get_risk_status(self) -> Dict[str, Any]:
        """
        Get current risk status.

        Returns:
            Dictionary with risk metrics
        """
        return {
            "daily_pnl": self.daily_pnl,
            "consecutive_losses": self.consecutive_losses,
            "trading_halted": self.is_trading_halted,
            "max_daily_loss": self.settings.max_daily_loss,
        }


if __name__ == "__main__":
    # Test risk manager
    from src.llm.decision_parser import TradingDecision, TradingAction

    risk_mgr = RiskManager()

    # Test decision validation
    decision = TradingDecision(
        action=TradingAction.BUY,
        confidence=0.85,
        reasoning="Test trade",
    )

    is_valid, reason = risk_mgr.validate_decision(
        decision=decision,
        account_balance=10000,
    )
    print(f"\nDecision valid: {is_valid} ({reason})")

    # Test position sizing
    position_size = risk_mgr.calculate_position_size(
        account_balance=10000,
        entry_price=50000,
        stop_loss_pct=0.02,
    )
    print(f"Position size: {position_size:.8f} BTC")
    print(f"Position value: ${position_size * 50000:,.2f}")

    # Test daily P&L tracking
    risk_mgr.update_daily_pnl(-100)
    risk_mgr.update_daily_pnl(-50)
    risk_mgr.update_daily_pnl(200)
    print(f"\nRisk status: {risk_mgr.get_risk_status()}")
