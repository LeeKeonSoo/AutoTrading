"""
LLM-based trading strategy integrating all components.
"""

import pandas as pd
from typing import Dict, Any, Optional
from loguru import logger

from src.llm.gemini_client import GeminiClient
from src.llm.prompts import SYSTEM_PROMPT, format_market_data_prompt
from src.llm.decision_parser import DecisionParser, TradingDecision
from src.data.market_data import MarketData
from src.config.settings import get_settings


class LLMTradingStrategy:
    """
    Complete LLM-based trading strategy.
    """

    def __init__(
        self,
        market_data: Optional[MarketData] = None,
        gemini_client: Optional[GeminiClient] = None,
    ):
        """
        Initialize LLM trading strategy.

        Args:
            market_data: MarketData instance (creates new if None)
            gemini_client: GeminiClient instance (creates new if None)
        """
        self.settings = get_settings()
        self.market_data = market_data or MarketData()
        self.gemini_client = gemini_client or GeminiClient()
        self.parser = DecisionParser()

        # Trading state
        self.current_position: Optional[Dict[str, Any]] = None
        self.trade_history: list = []

        logger.info("LLMTradingStrategy initialized")

    def analyze_and_decide(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> TradingDecision:
        """
        Analyze market and make trading decision.

        Args:
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)

        Returns:
            TradingDecision
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe

        try:
            # 1. Fetch latest market data
            logger.info(f"Fetching market data for {symbol} ({timeframe})")
            df = self.market_data.fetch_latest_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=200,  # Enough for all indicators
                with_indicators=True,
            )

            # 2. Get market summary
            market_summary = self.market_data.get_market_summary(
                symbol=symbol,
                timeframe=timeframe,
                lookback=100,
            )

            # 3. Get indicator summary
            from src.data.indicators import TechnicalIndicators
            indicators_module = TechnicalIndicators()
            indicator_summary = indicators_module.get_indicator_summary(df)

            # 4. Format prompt
            current_price = market_summary["current_price"]
            prompt = format_market_data_prompt(
                symbol=symbol,
                current_price=current_price,
                market_data=market_summary,
                indicators=indicator_summary,
                current_position=self.current_position,
                recent_trades=self.trade_history[-5:] if self.trade_history else None,
            )

            # 5. Get LLM decision
            logger.info("Requesting decision from Gemini...")
            llm_response = self.gemini_client.generate_trading_decision(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            # 6. Parse and validate
            decision = self.parser.parse(llm_response)
            decision = self.parser.apply_safety_checks(decision)

            logger.info(
                f"Decision: {decision.action.value} "
                f"(confidence: {decision.confidence:.2f})"
            )
            logger.info(f"Reasoning: {decision.reasoning}")

            return decision

        except Exception as e:
            logger.error(f"Error in analyze_and_decide: {e}")
            # Return safe default
            return self.parser.create_hold_decision(
                reason=f"Error occurred: {str(e)[:100]}"
            )

    def update_position(
        self,
        action: str,
        entry_price: float,
        size: float,
    ) -> None:
        """Update current position state."""
        if action in ["BUY", "SELL"]:
            self.current_position = {
                "action": action,
                "entry_price": entry_price,
                "size": size,
                "timestamp": pd.Timestamp.now(),
            }
        elif action == "CLOSE":
            self.current_position = None

    def record_trade(
        self,
        action: str,
        entry_price: float,
        exit_price: Optional[float] = None,
        pnl: float = 0.0,
    ) -> None:
        """Record trade in history."""
        trade = {
            "action": action,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_pct": (pnl / entry_price * 100) if entry_price else 0,
            "timestamp": pd.Timestamp.now(),
        }
        self.trade_history.append(trade)
        logger.info(f"Trade recorded: {action} P&L: ${pnl:+.2f}")


if __name__ == "__main__":
    # Test LLM strategy
    import sys
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    try:
        strategy = LLMTradingStrategy()

        print("\n=== Testing LLM Trading Strategy ===")
        decision = strategy.analyze_and_decide()

        print(f"\n✅ Decision: {decision.action.value}")
        print(f"   Confidence: {decision.confidence:.1%}")
        print(f"   Reasoning: {decision.reasoning}")
        print(f"   Stop Loss: {decision.stop_loss_pct:.1%}")
        print(f"   Take Profit: {decision.take_profit_pct:.1%}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
