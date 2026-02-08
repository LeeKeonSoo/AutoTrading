"""
Technical indicators calculation using TA library.
Provides common trading indicators for market analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional
from loguru import logger
import ta

from src.config.constants import INDICATOR_PARAMS


class TechnicalIndicators:
    """
    Calculate technical indicators for trading analysis.
    """

    def __init__(self):
        """Initialize TechnicalIndicators."""
        self.params = INDICATOR_PARAMS
        logger.debug("TechnicalIndicators initialized")

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicators
        """
        logger.debug(f"Adding all indicators to {len(df)} candles")

        # Make a copy to avoid modifying original
        df = df.copy()

        # Trend indicators
        df = self.add_sma(df)
        df = self.add_ema(df)
        df = self.add_macd(df)

        # Momentum indicators
        df = self.add_rsi(df)
        df = self.add_stochastic(df)

        # Volatility indicators
        df = self.add_bollinger_bands(df)
        df = self.add_atr(df)

        # Volume indicators
        df = self.add_volume_indicators(df)

        logger.debug(f"Added indicators, now have {len(df.columns)} columns")
        return df

    def add_sma(
        self,
        df: pd.DataFrame,
        short: Optional[int] = None,
        medium: Optional[int] = None,
        long: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add Simple Moving Averages.

        Args:
            df: DataFrame with OHLCV data
            short: Short period (default: from config)
            medium: Medium period (default: from config)
            long: Long period (default: from config)

        Returns:
            DataFrame with SMA columns
        """
        short = short or self.params["SMA"]["short"]
        medium = medium or self.params["SMA"]["medium"]
        long = long or self.params["SMA"]["long"]

        df[f"sma_{short}"] = ta.trend.sma_indicator(df["close"], window=short)
        df[f"sma_{medium}"] = ta.trend.sma_indicator(df["close"], window=medium)
        df[f"sma_{long}"] = ta.trend.sma_indicator(df["close"], window=long)

        return df

    def add_ema(
        self,
        df: pd.DataFrame,
        short: Optional[int] = None,
        medium: Optional[int] = None,
        long: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add Exponential Moving Averages.

        Args:
            df: DataFrame with OHLCV data
            short: Short period (default: from config)
            medium: Medium period (default: from config)
            long: Long period (default: from config)

        Returns:
            DataFrame with EMA columns
        """
        short = short or self.params["EMA"]["short"]
        medium = medium or self.params["EMA"]["medium"]
        long = long or self.params["EMA"]["long"]

        df[f"ema_{short}"] = ta.trend.ema_indicator(df["close"], window=short)
        df[f"ema_{medium}"] = ta.trend.ema_indicator(df["close"], window=medium)
        df[f"ema_{long}"] = ta.trend.ema_indicator(df["close"], window=long)

        return df

    def add_rsi(
        self,
        df: pd.DataFrame,
        period: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add Relative Strength Index.

        Args:
            df: DataFrame with OHLCV data
            period: RSI period (default: from config)

        Returns:
            DataFrame with RSI column
        """
        period = period or self.params["RSI"]["period"]
        df["rsi"] = ta.momentum.rsi(df["close"], window=period)
        return df

    def add_macd(
        self,
        df: pd.DataFrame,
        fast: Optional[int] = None,
        slow: Optional[int] = None,
        signal: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add MACD (Moving Average Convergence Divergence).

        Args:
            df: DataFrame with OHLCV data
            fast: Fast period (default: from config)
            slow: Slow period (default: from config)
            signal: Signal period (default: from config)

        Returns:
            DataFrame with MACD columns
        """
        fast = fast or self.params["MACD"]["fast_period"]
        slow = slow or self.params["MACD"]["slow_period"]
        signal = signal or self.params["MACD"]["signal_period"]

        macd_indicator = ta.trend.MACD(
            df["close"],
            window_fast=fast,
            window_slow=slow,
            window_sign=signal,
        )

        df["macd"] = macd_indicator.macd()
        df["macd_signal"] = macd_indicator.macd_signal()
        df["macd_diff"] = macd_indicator.macd_diff()

        return df

    def add_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: Optional[int] = None,
        std_dev: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add Bollinger Bands.

        Args:
            df: DataFrame with OHLCV data
            period: Period (default: from config)
            std_dev: Standard deviation multiplier (default: from config)

        Returns:
            DataFrame with Bollinger Bands columns
        """
        period = period or self.params["BOLLINGER_BANDS"]["period"]
        std_dev = std_dev or self.params["BOLLINGER_BANDS"]["std_dev"]

        bb_indicator = ta.volatility.BollingerBands(
            df["close"],
            window=period,
            window_dev=std_dev,
        )

        df["bb_upper"] = bb_indicator.bollinger_hband()
        df["bb_middle"] = bb_indicator.bollinger_mavg()
        df["bb_lower"] = bb_indicator.bollinger_lband()
        df["bb_width"] = bb_indicator.bollinger_wband()
        df["bb_pct"] = bb_indicator.bollinger_pband()

        return df

    def add_atr(
        self,
        df: pd.DataFrame,
        period: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add Average True Range (volatility indicator).

        Args:
            df: DataFrame with OHLCV data
            period: ATR period (default: from config)

        Returns:
            DataFrame with ATR column
        """
        period = period or self.params["ATR"]["period"]
        df["atr"] = ta.volatility.average_true_range(
            df["high"],
            df["low"],
            df["close"],
            window=period,
        )
        return df

    def add_stochastic(
        self,
        df: pd.DataFrame,
        k_period: Optional[int] = None,
        d_period: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Add Stochastic Oscillator.

        Args:
            df: DataFrame with OHLCV data
            k_period: K period (default: from config)
            d_period: D period (default: from config)

        Returns:
            DataFrame with Stochastic columns
        """
        k_period = k_period or self.params["STOCHASTIC"]["k_period"]
        d_period = d_period or self.params["STOCHASTIC"]["d_period"]

        stoch_indicator = ta.momentum.StochasticOscillator(
            df["high"],
            df["low"],
            df["close"],
            window=k_period,
            smooth_window=d_period,
        )

        df["stoch_k"] = stoch_indicator.stoch()
        df["stoch_d"] = stoch_indicator.stoch_signal()

        return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add volume-based indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with volume indicators
        """
        # On-Balance Volume
        df["obv"] = ta.volume.on_balance_volume(df["close"], df["volume"])

        # Volume-Weighted Average Price (VWAP)
        df["vwap"] = ta.volume.volume_weighted_average_price(
            df["high"],
            df["low"],
            df["close"],
            df["volume"],
        )

        # Money Flow Index
        df["mfi"] = ta.volume.money_flow_index(
            df["high"],
            df["low"],
            df["close"],
            df["volume"],
            window=14,
        )

        return df

    def identify_trend(self, df: pd.DataFrame) -> str:
        """
        Identify current market trend.

        Args:
            df: DataFrame with indicators

        Returns:
            Trend string: "uptrend", "downtrend", or "sideways"
        """
        if df.empty or len(df) < 50:
            return "unknown"

        # Use price vs moving averages
        current_price = df["close"].iloc[-1]
        sma_20 = df["sma_20"].iloc[-1] if "sma_20" in df.columns else current_price
        sma_50 = df["sma_50"].iloc[-1] if "sma_50" in df.columns else current_price

        # Strong uptrend: price above both MAs and MAs in correct order
        if current_price > sma_20 > sma_50:
            return "uptrend"

        # Strong downtrend: price below both MAs and MAs in correct order
        if current_price < sma_20 < sma_50:
            return "downtrend"

        # Otherwise sideways
        return "sideways"

    def identify_support_resistance(
        self,
        df: pd.DataFrame,
        window: int = 20,
    ) -> dict:
        """
        Identify support and resistance levels.

        Args:
            df: DataFrame with OHLCV data
            window: Lookback window

        Returns:
            Dictionary with support and resistance levels
        """
        if df.empty or len(df) < window:
            return {"support": None, "resistance": None}

        recent = df.tail(window)

        # Simple support/resistance using highs and lows
        resistance = recent["high"].max()
        support = recent["low"].min()

        return {
            "support": support,
            "resistance": resistance,
            "current": df["close"].iloc[-1],
            "distance_to_support_pct": (df["close"].iloc[-1] - support) / df["close"].iloc[-1] * 100,
            "distance_to_resistance_pct": (resistance - df["close"].iloc[-1]) / df["close"].iloc[-1] * 100,
        }

    def get_indicator_summary(self, df: pd.DataFrame) -> dict:
        """
        Get summary of all indicators at the latest candle.

        Args:
            df: DataFrame with indicators

        Returns:
            Dictionary with indicator values
        """
        if df.empty:
            return {}

        latest = df.iloc[-1]
        summary = {}

        # Add all indicator values
        for col in df.columns:
            if col not in ["open", "high", "low", "close", "volume"]:
                summary[col] = latest[col]

        # Add trend analysis
        summary["trend"] = self.identify_trend(df)

        # Add support/resistance
        sr = self.identify_support_resistance(df)
        summary.update(sr)

        # Add signal interpretations
        if "rsi" in summary:
            if summary["rsi"] > self.params["RSI"]["overbought"]:
                summary["rsi_signal"] = "overbought"
            elif summary["rsi"] < self.params["RSI"]["oversold"]:
                summary["rsi_signal"] = "oversold"
            else:
                summary["rsi_signal"] = "neutral"

        if "macd" in summary and "macd_signal" in summary:
            if summary["macd"] > summary["macd_signal"]:
                summary["macd_signal_direction"] = "bullish"
            else:
                summary["macd_signal_direction"] = "bearish"

        if "stoch_k" in summary:
            if summary["stoch_k"] > self.params["STOCHASTIC"]["overbought"]:
                summary["stoch_signal"] = "overbought"
            elif summary["stoch_k"] < self.params["STOCHASTIC"]["oversold"]:
                summary["stoch_signal"] = "oversold"
            else:
                summary["stoch_signal"] = "neutral"

        return summary


if __name__ == "__main__":
    # Test indicators
    from datetime import datetime, timedelta
    from src.data.binance_client import BinanceClient

    client = BinanceClient(testnet=True)
    indicators = TechnicalIndicators()

    # Fetch some data
    ohlcv = client.fetch_ohlcv(limit=100)
    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    # Add indicators
    df = indicators.add_all_indicators(df)

    print("\n=== DataFrame with Indicators ===")
    print(df.tail())
    print(f"\nColumns: {list(df.columns)}")

    print("\n=== Indicator Summary ===")
    summary = indicators.get_indicator_summary(df)
    for key, value in summary.items():
        if isinstance(value, (int, float)) and not pd.isna(value):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
