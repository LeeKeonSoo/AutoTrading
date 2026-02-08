"""
Google Gemini API client for trading decisions.
Uses the NEW google-genai library (v1.0+).
"""

import json
from typing import Dict, Any, Optional
from loguru import logger
from google import genai
from google.genai import types
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config.settings import get_settings


class GeminiClient:
    """
    Wrapper around Google Gemini API for trading analysis.
    """

    def __init__(self):
        """Initialize Gemini client."""
        self.settings = get_settings()

        # Create client
        self.client = genai.Client(api_key=self.settings.gemini_api_key)

        # Model configuration
        self.model_id = self.settings.gemini_model
        self.generation_config = types.GenerateContentConfig(
            temperature=self.settings.gemini_temperature,
            max_output_tokens=self.settings.gemini_max_tokens,
            response_mime_type="application/json",
        )

        logger.info(
            f"GeminiClient initialized with model {self.model_id} "
            f"(temp={self.settings.gemini_temperature})"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
    )
    def generate_trading_decision(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate trading decision from Gemini.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User prompt with market data
            temperature: Override default temperature

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If response cannot be parsed as JSON
            Exception: For API errors
        """
        try:
            # Combine system and user prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Override temperature if specified
            config = self.generation_config
            if temperature is not None:
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=self.settings.gemini_max_tokens,
                    response_mime_type="application/json",
                )

            # Generate content
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config=config,
            )

            # Extract text from response
            response_text = response.text.strip()

            # Parse JSON
            try:
                decision = json.loads(response_text)
                logger.debug(f"Gemini decision: {decision.get('action', 'UNKNOWN')}")
                return decision
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response_text}")
                raise ValueError(f"Invalid JSON response from Gemini: {e}")

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            response = self.client.models.count_tokens(
                model=self.model_id,
                contents=text,
            )
            return response.total_tokens
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}")
            # Rough estimate: ~4 chars per token
            return len(text) // 4

    def test_connection(self) -> bool:
        """
        Test connection to Gemini API.

        Returns:
            True if connection works
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents="Respond with just the word 'OK' if you can read this.",
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            result = "ok" in response.text.lower()
            if result:
                logger.info("Gemini API connection OK")
            else:
                logger.warning(f"Unexpected test response: {response.text}")
            return result
        except Exception as e:
            logger.error(f"Gemini API connection failed: {e}")
            return False

    def list_available_models(self) -> list:
        """
        List all available Gemini models.

        Returns:
            List of model names
        """
        try:
            models = self.client.models.list()
            model_names = [model.name for model in models]
            logger.info(f"Found {len(model_names)} available models")
            return model_names
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


if __name__ == "__main__":
    # Test Gemini client
    import sys
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    try:
        client = GeminiClient()

        # Test connection
        print("\n=== Testing Connection ===")
        if client.test_connection():
            print("✅ Connection OK")
        else:
            print("❌ Connection failed")
            sys.exit(1)

        # Test trading decision generation
        print("\n=== Test Trading Decision ===")
        system_prompt = """You are a cryptocurrency trading assistant.
Analyze the market data and respond with JSON containing:
{
  "action": "BUY|SELL|HOLD|CLOSE",
  "confidence": 0.85,
  "reasoning": "Brief explanation"
}"""

        user_prompt = """Current market:
- BTC/USDT: $50,000
- RSI: 45 (neutral)
- Trend: Uptrend
- MACD: Bullish crossover

Should we trade?"""

        decision = client.generate_trading_decision(system_prompt, user_prompt)
        print(f"\nDecision: {json.dumps(decision, indent=2)}")

        # List available models
        print("\n=== Available Models ===")
        models = client.list_available_models()
        for model in models[:5]:  # Show first 5
            print(f"- {model}")
        if len(models) > 5:
            print(f"... and {len(models) - 5} more")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
