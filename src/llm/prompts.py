"""
Prompt templates for LLM trading decisions.
These prompts guide the AI to make informed trading decisions.
"""

from typing import Dict, Any, Optional
from datetime import datetime


SYSTEM_PROMPT = """You are an expert cryptocurrency trading analyst with deep knowledge of technical analysis, risk management, and market psychology.

Your role is to analyze market data and make informed trading decisions for BTC/USDT trading on Binance.

CORE TRADING PRINCIPLES:
1. **Risk Management First**: Protecting capital is more important than maximizing profits
2. **Follow the Trend**: Trade with the trend, not against it
3. **Patience**: Only trade when there are clear, high-probability signals
4. **Discipline**: Always use stop-losses and take-profits
5. **No Emotion**: Base decisions purely on data and analysis

DECISION FRAMEWORK:
- **BUY**: Enter a long position when bullish signals align
- **SELL**: Close long position or enter short when bearish signals align
- **HOLD**: Maintain current position when conditions are neutral
- **CLOSE**: Exit position immediately if risk conditions are met

You MUST respond with VALID JSON in this exact format:
{
  "action": "BUY|SELL|HOLD|CLOSE",
  "confidence": 0.0-1.0,
  "reasoning": "Clear explanation of your analysis (2-3 sentences)",
  "stop_loss_pct": 0.01-0.10,
  "take_profit_pct": 0.02-0.20,
  "position_size_multiplier": 0.3-1.0
}

CONFIDENCE LEVELS:
- 0.9-1.0: Very strong signal, all indicators align
- 0.7-0.9: Strong signal, most indicators align
- 0.5-0.7: Moderate signal, some indicators align
- 0.3-0.5: Weak signal, mixed indicators
- 0.0-0.3: Very weak signal, conflicting indicators

IMPORTANT:
- Only recommend BUY/SELL with confidence >= 0.7
- Use HOLD for confidence < 0.7 unless risk conditions require CLOSE
- Set tighter stop-loss in high volatility
- Set wider take-profit in strong trends
- Reduce position_size_multiplier when confidence is lower
"""


def format_market_data_prompt(
    symbol: str,
    current_price: float,
    market_data: Dict[str, Any],
    indicators: Dict[str, Any],
    current_position: Optional[Dict[str, Any]] = None,
    recent_trades: Optional[list] = None,
) -> str:
    """
    Format market data into a prompt for the LLM.

    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')
        current_price: Current market price
        market_data: Dictionary with OHLCV data
        indicators: Dictionary with technical indicators
        current_position: Current position info (optional)
        recent_trades: Recent trade history (optional)

    Returns:
        Formatted prompt string
    """

    # Extract key data
    price_change_pct = market_data.get("price_change_pct", 0)
    volume_24h = market_data.get("volume_24h", 0)
    high_24h = market_data.get("high_24h", current_price)
    low_24h = market_data.get("low_24h", current_price)

    # Technical indicators
    rsi = indicators.get("rsi", 50)
    rsi_signal = indicators.get("rsi_signal", "neutral")
    macd = indicators.get("macd", 0)
    macd_signal = indicators.get("macd_signal", 0)
    macd_signal_direction = indicators.get("macd_signal_direction", "neutral")
    trend = indicators.get("trend", "unknown")

    sma_20 = indicators.get("sma_20", current_price)
    sma_50 = indicators.get("sma_50", current_price)
    ema_12 = indicators.get("ema_12", current_price)

    bb_upper = indicators.get("bb_upper", current_price * 1.02)
    bb_lower = indicators.get("bb_lower", current_price * 0.98)
    bb_position = "middle"
    if current_price > bb_upper * 0.99:
        bb_position = "upper band"
    elif current_price < bb_lower * 1.01:
        bb_position = "lower band"

    atr = indicators.get("atr", current_price * 0.02)
    volatility_pct = (atr / current_price) * 100

    # Support/Resistance
    support = indicators.get("support", low_24h)
    resistance = indicators.get("resistance", high_24h)
    distance_to_support_pct = indicators.get("distance_to_support_pct", 0)
    distance_to_resistance_pct = indicators.get("distance_to_resistance_pct", 0)

    # Build prompt
    prompt = f"""=== MARKET ANALYSIS REQUEST ===
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CURRENT MARKET:
- Symbol: {symbol}
- Price: ${current_price:,.2f}
- 24h Change: {price_change_pct:+.2f}%
- 24h High: ${high_24h:,.2f}
- 24h Low: ${low_24h:,.2f}
- 24h Volume: ${volume_24h:,.2f}

TECHNICAL INDICATORS:
- Trend: {trend.upper()}
- RSI(14): {rsi:.1f} ({rsi_signal})
  → Interpretation: {"Overbought - potential sell signal" if rsi > 70 else "Oversold - potential buy signal" if rsi < 30 else "Neutral zone"}

- MACD: {macd:.2f}
- MACD Signal: {macd_signal:.2f}
- MACD Status: {macd_signal_direction.upper()}
  → Interpretation: {"Bullish momentum" if macd > macd_signal else "Bearish momentum"}

- Moving Averages:
  * SMA(20): ${sma_20:,.2f} - Price is {"ABOVE" if current_price > sma_20 else "BELOW"}
  * SMA(50): ${sma_50:,.2f} - Price is {"ABOVE" if current_price > sma_50 else "BELOW"}
  * EMA(12): ${ema_12:,.2f}
  → Interpretation: {"Strong uptrend" if current_price > sma_20 > sma_50 else "Strong downtrend" if current_price < sma_20 < sma_50 else "Sideways/uncertain"}

- Bollinger Bands:
  * Upper: ${bb_upper:,.2f}
  * Lower: ${bb_lower:,.2f}
  * Position: Price near {bb_position}
  → Interpretation: {"Overbought zone" if bb_position == "upper band" else "Oversold zone" if bb_position == "lower band" else "Normal range"}

- Volatility:
  * ATR: ${atr:,.2f}
  * Volatility: {volatility_pct:.2f}%
  → Interpretation: {"High volatility - use wider stops" if volatility_pct > 3 else "Low volatility - tighter stops acceptable"}

SUPPORT & RESISTANCE:
- Support: ${support:,.2f} ({distance_to_support_pct:.1f}% below)
- Resistance: ${resistance:,.2f} ({distance_to_resistance_pct:.1f}% above)
"""

    # Add current position info
    if current_position:
        entry_price = current_position.get("entry_price", current_price)
        position_size = current_position.get("size", 0)
        unrealized_pnl = current_position.get("unrealized_pnl", 0)
        unrealized_pnl_pct = ((current_price - entry_price) / entry_price) * 100

        prompt += f"""
CURRENT POSITION:
- Status: OPEN
- Entry Price: ${entry_price:,.2f}
- Size: {position_size:.8f} {symbol.split('/')[0]}
- Current P&L: ${unrealized_pnl:+,.2f} ({unrealized_pnl_pct:+.2f}%)
- Holding Time: {current_position.get('holding_time', 'N/A')}

POSITION MANAGEMENT CONSIDERATIONS:
- Should we take profit now?
- Should we move stop-loss to break-even?
- Is the trend still in our favor?
"""
    else:
        prompt += """
CURRENT POSITION:
- Status: NO OPEN POSITION
- Looking for entry opportunity

ENTRY CONSIDERATIONS:
- Is the risk/reward favorable?
- Are multiple indicators aligned?
- Is this a high-probability setup?
"""

    # Add recent trade history
    if recent_trades:
        prompt += "\nRECENT TRADING HISTORY:\n"
        for i, trade in enumerate(recent_trades[-3:], 1):  # Last 3 trades
            action = trade.get("action", "UNKNOWN")
            pnl = trade.get("pnl", 0)
            pnl_pct = trade.get("pnl_pct", 0)
            prompt += f"{i}. {action} - P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)\n"

        # Calculate win rate
        wins = sum(1 for t in recent_trades if t.get("pnl", 0) > 0)
        total = len(recent_trades)
        win_rate = (wins / total * 100) if total > 0 else 0
        prompt += f"\nWin Rate: {win_rate:.1f}% ({wins}/{total})\n"

    # Final instructions
    prompt += """
=== YOUR TASK ===
Analyze all the data above and make a trading decision.

Consider:
1. Is the trend clear and strong?
2. Are multiple indicators confirming the same direction?
3. Is the risk/reward ratio favorable?
4. Is volatility at a manageable level?
5. If we have a position, should we hold, take profit, or cut losses?

Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{
  "action": "BUY|SELL|HOLD|CLOSE",
  "confidence": 0.85,
  "reasoning": "Your analysis here",
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.05,
  "position_size_multiplier": 0.8
}
"""

    return prompt


def format_quick_decision_prompt(
    current_price: float,
    rsi: float,
    trend: str,
    macd_signal: str,
) -> str:
    """
    Format a quick decision prompt with minimal data.
    Useful for fast decisions or when full data is unavailable.

    Args:
        current_price: Current price
        rsi: RSI value
        trend: Trend direction
        macd_signal: MACD signal

    Returns:
        Formatted prompt string
    """
    prompt = f"""Quick market check:
- Price: ${current_price:,.2f}
- RSI: {rsi:.1f}
- Trend: {trend}
- MACD: {macd_signal}

Should we trade? Respond with JSON:
{{
  "action": "BUY|SELL|HOLD|CLOSE",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}}
"""
    return prompt


# Example prompts for different scenarios
EMERGENCY_EXIT_PROMPT = """URGENT: Market conditions have triggered emergency protocols.
Current position is at significant risk.

Recommend immediate action:
{
  "action": "CLOSE",
  "confidence": 0.95,
  "reasoning": "Emergency exit triggered"
}
"""


if __name__ == "__main__":
    # Test prompt formatting
    test_data = {
        "price_change_pct": 5.2,
        "volume_24h": 1000000000,
        "high_24h": 51000,
        "low_24h": 49000,
    }

    test_indicators = {
        "rsi": 65,
        "rsi_signal": "neutral",
        "macd": 50,
        "macd_signal": 45,
        "macd_signal_direction": "bullish",
        "trend": "uptrend",
        "sma_20": 49500,
        "sma_50": 48000,
        "atr": 500,
        "support": 49000,
        "resistance": 51000,
        "distance_to_support_pct": 2.0,
        "distance_to_resistance_pct": 2.0,
    }

    prompt = format_market_data_prompt(
        symbol="BTC/USDT",
        current_price=50000,
        market_data=test_data,
        indicators=test_indicators,
    )

    print("=== GENERATED PROMPT ===")
    print(prompt)
    print(f"\n=== PROMPT LENGTH: {len(prompt)} characters ===")
