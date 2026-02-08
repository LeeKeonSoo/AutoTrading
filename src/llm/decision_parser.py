"""
Parse and validate LLM trading decisions.
Ensures all decisions meet safety and sanity checks before execution.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from src.config.constants import TradingAction
from src.config.settings import get_settings


class TradingDecision(BaseModel):
    """
    Validated trading decision from LLM.
    """

    action: TradingAction = Field(..., description="Trading action to take")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0-1)")
    reasoning: str = Field(..., min_length=10, description="Explanation for the decision")
    stop_loss_pct: float = Field(
        default=0.02,
        ge=0.005,
        le=0.20,
        description="Stop loss percentage (0.005-0.20)"
    )
    take_profit_pct: float = Field(
        default=0.05,
        ge=0.01,
        le=0.50,
        description="Take profit percentage (0.01-0.50)"
    )
    position_size_multiplier: float = Field(
        default=1.0,
        ge=0.1,
        le=1.0,
        description="Position size multiplier (0.1-1.0)"
    )

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, v: Any) -> str:
        """Validate and normalize action."""
        if isinstance(v, str):
            v = v.upper().strip()
            # Map common variations
            if v in ["BUY", "LONG", "ENTER_LONG"]:
                return "BUY"
            elif v in ["SELL", "SHORT", "ENTER_SHORT"]:
                return "SELL"
            elif v in ["HOLD", "WAIT", "DO_NOTHING"]:
                return "HOLD"
            elif v in ["CLOSE", "EXIT", "CLOSE_POSITION"]:
                return "CLOSE"
        return str(v)

    @field_validator("take_profit_pct")
    @classmethod
    def validate_take_profit(cls, v: float, info) -> float:
        """Ensure take profit is larger than stop loss."""
        if "stop_loss_pct" in info.data:
            stop_loss = info.data["stop_loss_pct"]
            if v <= stop_loss:
                logger.warning(
                    f"Take profit ({v}) should be > stop loss ({stop_loss}). "
                    f"Adjusting to {stop_loss * 2}"
                )
                return stop_loss * 2
        return v

    def should_execute(self, min_confidence: Optional[float] = None) -> bool:
        """
        Check if decision should be executed based on confidence threshold.

        Args:
            min_confidence: Minimum confidence threshold (uses setting if None)

        Returns:
            True if decision should be executed
        """
        settings = get_settings()
        threshold = min_confidence or settings.min_confidence

        # HOLD and CLOSE can be executed at any confidence
        if self.action in [TradingAction.HOLD, TradingAction.CLOSE]:
            return True

        # BUY and SELL need high confidence
        if self.confidence >= threshold:
            return True

        logger.info(
            f"Decision confidence ({self.confidence:.2f}) below threshold ({threshold:.2f}). "
            f"Defaulting to HOLD."
        )
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "position_size_multiplier": self.position_size_multiplier,
        }


class DecisionParser:
    """
    Parse and validate LLM responses into TradingDecision objects.
    """

    def __init__(self):
        """Initialize parser."""
        self.settings = get_settings()
        logger.debug("DecisionParser initialized")

    def parse(self, llm_response: Dict[str, Any]) -> TradingDecision:
        """
        Parse LLM response into validated TradingDecision.

        Args:
            llm_response: Raw response dictionary from LLM

        Returns:
            Validated TradingDecision

        Raises:
            ValueError: If response is invalid
        """
        try:
            decision = TradingDecision(**llm_response)
            logger.info(
                f"Parsed decision: {decision.action.value} "
                f"(confidence: {decision.confidence:.2f})"
            )
            return decision
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Response was: {llm_response}")
            raise ValueError(f"Invalid LLM response format: {e}")

    def apply_safety_checks(self, decision: TradingDecision) -> TradingDecision:
        """
        Apply additional safety checks and adjustments.

        Args:
            decision: TradingDecision to check

        Returns:
            Adjusted TradingDecision
        """
        # Check if confidence is too low
        if not decision.should_execute():
            logger.warning(
                f"Confidence {decision.confidence:.2f} too low for {decision.action}. "
                f"Overriding to HOLD."
            )
            decision.action = TradingAction.HOLD
            decision.reasoning = (
                f"[AUTO-OVERRIDE] {decision.reasoning} "
                f"(Original action: {decision.action.value}, but confidence too low)"
            )

        # Adjust position size based on confidence
        if decision.confidence < 0.8:
            original_size = decision.position_size_multiplier
            decision.position_size_multiplier = min(
                original_size,
                decision.confidence
            )
            if original_size != decision.position_size_multiplier:
                logger.info(
                    f"Reduced position size from {original_size:.2f} to "
                    f"{decision.position_size_multiplier:.2f} based on confidence"
                )

        # Tighten stop-loss if confidence is low
        if decision.confidence < 0.75 and decision.action in [TradingAction.BUY, TradingAction.SELL]:
            original_sl = decision.stop_loss_pct
            decision.stop_loss_pct = max(0.015, original_sl * 0.8)  # 20% tighter
            if original_sl != decision.stop_loss_pct:
                logger.info(
                    f"Tightened stop-loss from {original_sl*100:.1f}% to "
                    f"{decision.stop_loss_pct*100:.1f}% due to lower confidence"
                )

        return decision

    def create_hold_decision(self, reason: str = "No clear signal") -> TradingDecision:
        """
        Create a default HOLD decision.

        Args:
            reason: Reason for holding

        Returns:
            TradingDecision with HOLD action
        """
        return TradingDecision(
            action=TradingAction.HOLD,
            confidence=0.5,
            reasoning=reason,
        )

    def create_emergency_close_decision(
        self,
        reason: str = "Emergency stop triggered"
    ) -> TradingDecision:
        """
        Create an emergency CLOSE decision.

        Args:
            reason: Reason for emergency close

        Returns:
            TradingDecision with CLOSE action
        """
        return TradingDecision(
            action=TradingAction.CLOSE,
            confidence=1.0,
            reasoning=f"[EMERGENCY] {reason}",
            stop_loss_pct=0.0,  # Immediate close
            take_profit_pct=0.0,
            position_size_multiplier=1.0,
        )


if __name__ == "__main__":
    # Test decision parser
    import json

    parser = DecisionParser()

    # Test valid decision
    print("\n=== Test 1: Valid BUY Decision ===")
    response1 = {
        "action": "BUY",
        "confidence": 0.85,
        "reasoning": "Strong uptrend with RSI oversold and MACD bullish crossover",
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.05,
        "position_size_multiplier": 0.8,
    }
    decision1 = parser.parse(response1)
    decision1 = parser.apply_safety_checks(decision1)
    print(json.dumps(decision1.to_dict(), indent=2))
    print(f"Should execute: {decision1.should_execute()}")

    # Test low confidence
    print("\n=== Test 2: Low Confidence (should convert to HOLD) ===")
    response2 = {
        "action": "BUY",
        "confidence": 0.5,
        "reasoning": "Weak signal, mixed indicators",
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.04,
        "position_size_multiplier": 0.5,
    }
    decision2 = parser.parse(response2)
    decision2 = parser.apply_safety_checks(decision2)
    print(json.dumps(decision2.to_dict(), indent=2))
    print(f"Should execute: {decision2.should_execute()}")

    # Test HOLD decision
    print("\n=== Test 3: HOLD Decision ===")
    decision3 = parser.create_hold_decision("Waiting for clearer signal")
    print(json.dumps(decision3.to_dict(), indent=2))

    # Test emergency close
    print("\n=== Test 4: Emergency CLOSE ===")
    decision4 = parser.create_emergency_close_decision("Max daily loss reached")
    print(json.dumps(decision4.to_dict(), indent=2))

    # Test invalid decision (will raise error)
    print("\n=== Test 5: Invalid Decision (should fail) ===")
    try:
        response5 = {
            "action": "INVALID_ACTION",
            "confidence": 1.5,  # Invalid: > 1.0
            "reasoning": "Test",
        }
        decision5 = parser.parse(response5)
    except ValueError as e:
        print(f"✅ Correctly rejected invalid decision: {e}")
