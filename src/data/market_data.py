"""
Market data collection and management.
Handles downloading, caching, and providing market data with technical indicators.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from src.data.binance_client import BinanceClient
from src.data.indicators import TechnicalIndicators
from src.config.settings import get_settings


class MarketData:
    """
    Manages market data collection, storage, and retrieval.
    """

    def __init__(
        self,
        client: Optional[BinanceClient] = None,
        cache_dir: str = "data/historical",
    ):
        """
        Initialize MarketData.

        Args:
            client: BinanceClient instance (creates new if None)
            cache_dir: Directory for caching data
        """
        self.settings = get_settings()
        self.client = client or BinanceClient()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.indicators = TechnicalIndicators()

        logger.info("MarketData initialized")

    def _get_cache_filename(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Path:
        """Generate cache filename."""
        symbol_clean = symbol.replace("/", "_")
        start_str = start_date.strftime("%Y%m%d") if start_date else "all"
        end_str = end_date.strftime("%Y%m%d") if end_date else "latest"
        filename = f"{symbol_clean}_{timeframe}_{start_str}_{end_str}.csv"
        return self.cache_dir / filename

    def _ohlcv_to_dataframe(self, ohlcv: List[List]) -> pd.DataFrame:
        """
        Convert OHLCV list to pandas DataFrame.

        Args:
            ohlcv: List of [timestamp, open, high, low, close, volume]

        Returns:
            DataFrame with OHLCV data
        """
        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # Convert to numeric
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Remove duplicates and sort
        df = df[~df.index.duplicated(keep="last")]
        df.sort_index(inplace=True)

        return df

    def fetch_latest_data(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 500,
        with_indicators: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch latest market data.

        Args:
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)
            limit: Number of candles to fetch
            with_indicators: Calculate technical indicators

        Returns:
            DataFrame with market data
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe

        logger.info(f"Fetching latest {limit} candles for {symbol} ({timeframe})")

        ohlcv = self.client.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        df = self._ohlcv_to_dataframe(ohlcv)

        if with_indicators:
            df = self.indicators.add_all_indicators(df)

        logger.info(f"Fetched {len(df)} candles with {len(df.columns)} columns")
        return df

    def fetch_historical_data(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        use_cache: bool = True,
        with_indicators: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch historical market data with optional caching.

        Args:
            start_date: Start date
            end_date: End date (default: now)
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)
            use_cache: Use cached data if available
            with_indicators: Calculate technical indicators

        Returns:
            DataFrame with historical data
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe
        end_date = end_date or datetime.now()

        # Check cache
        cache_file = self._get_cache_filename(symbol, timeframe, start_date, end_date)
        if use_cache and cache_file.exists():
            logger.info(f"Loading data from cache: {cache_file}")
            df = pd.read_csv(cache_file, index_col="timestamp", parse_dates=True)
            if with_indicators and "rsi" not in df.columns:
                df = self.indicators.add_all_indicators(df)
            return df

        # Fetch from API
        logger.info(
            f"Fetching historical data for {symbol} ({timeframe}) "
            f"from {start_date} to {end_date}"
        )

        ohlcv = self.client.fetch_ohlcv_range(
            start_date=start_date,
            end_date=end_date,
            symbol=symbol,
            timeframe=timeframe,
        )

        if not ohlcv:
            raise ValueError("No data fetched from API")

        df = self._ohlcv_to_dataframe(ohlcv)

        if with_indicators:
            df = self.indicators.add_all_indicators(df)

        # Save to cache
        if use_cache:
            logger.info(f"Saving data to cache: {cache_file}")
            df.to_csv(cache_file)

        return df

    def update_cache(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Update cached data with latest candles.

        Args:
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)

        Returns:
            Updated DataFrame
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe

        # Find most recent cache file
        cache_pattern = f"{symbol.replace('/', '_')}_{timeframe}_*.csv"
        cache_files = list(self.cache_dir.glob(cache_pattern))

        if not cache_files:
            logger.warning("No cache file found, fetching all data")
            # Default to last 6 months
            start_date = datetime.now() - timedelta(days=180)
            return self.fetch_historical_data(
                start_date=start_date,
                symbol=symbol,
                timeframe=timeframe,
            )

        # Load most recent cache
        latest_cache = max(cache_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Updating cache: {latest_cache}")
        df_cached = pd.read_csv(latest_cache, index_col="timestamp", parse_dates=True)

        # Fetch new data since last cached timestamp
        last_timestamp = df_cached.index[-1]
        since_date = last_timestamp + timedelta(seconds=1)

        try:
            ohlcv = self.client.fetch_ohlcv_range(
                start_date=since_date,
                end_date=datetime.now(),
                symbol=symbol,
                timeframe=timeframe,
            )

            if ohlcv:
                df_new = self._ohlcv_to_dataframe(ohlcv)
                df_combined = pd.concat([df_cached, df_new])
                df_combined = df_combined[~df_combined.index.duplicated(keep="last")]
                df_combined.sort_index(inplace=True)

                # Recalculate indicators on combined data
                # Remove old indicator columns
                indicator_cols = [
                    c for c in df_combined.columns
                    if c not in ["open", "high", "low", "close", "volume"]
                ]
                df_combined.drop(columns=indicator_cols, inplace=True, errors="ignore")
                df_combined = self.indicators.add_all_indicators(df_combined)

                # Save updated cache
                df_combined.to_csv(latest_cache)
                logger.info(f"Updated cache with {len(df_new)} new candles")
                return df_combined
            else:
                logger.info("No new data to update")
                return df_cached

        except Exception as e:
            logger.error(f"Failed to update cache: {e}")
            return df_cached

    def get_current_price(self, symbol: Optional[str] = None) -> float:
        """
        Get current market price.

        Args:
            symbol: Trading symbol (default: from settings)

        Returns:
            Current price
        """
        symbol = symbol or self.settings.trading_symbol
        ticker = self.client.fetch_ticker(symbol)
        return float(ticker["last"])

    def get_latest_candle(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get most recent complete candle.

        Args:
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)

        Returns:
            Dictionary with OHLCV data
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe

        ohlcv = self.client.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=1)
        if not ohlcv:
            raise ValueError("No candle data available")

        candle = ohlcv[0]
        return {
            "timestamp": datetime.fromtimestamp(candle[0] / 1000),
            "open": candle[1],
            "high": candle[2],
            "low": candle[3],
            "close": candle[4],
            "volume": candle[5],
        }

    def get_market_summary(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        lookback: int = 100,
    ) -> Dict[str, Any]:
        """
        Get market summary with key statistics.

        Args:
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)
            lookback: Number of periods to analyze

        Returns:
            Dictionary with market statistics
        """
        df = self.fetch_latest_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=lookback,
            with_indicators=True,
        )

        current_price = df["close"].iloc[-1]
        price_change_24h = (current_price - df["close"].iloc[0]) / df["close"].iloc[0] * 100
        volume_24h = df["volume"].sum()
        volatility = df["close"].pct_change().std() * np.sqrt(lookback)

        summary = {
            "symbol": symbol or self.settings.trading_symbol,
            "current_price": current_price,
            "price_change_pct": price_change_24h,
            "volume_24h": volume_24h,
            "volatility": volatility,
            "high_24h": df["high"].max(),
            "low_24h": df["low"].min(),
            "rsi": df["rsi"].iloc[-1] if "rsi" in df.columns else None,
            "macd": df["macd"].iloc[-1] if "macd" in df.columns else None,
            "macd_signal": df["macd_signal"].iloc[-1] if "macd_signal" in df.columns else None,
            "sma_20": df["sma_20"].iloc[-1] if "sma_20" in df.columns else None,
            "sma_50": df["sma_50"].iloc[-1] if "sma_50" in df.columns else None,
            "atr": df["atr"].iloc[-1] if "atr" in df.columns else None,
        }

        return summary


if __name__ == "__main__":
    # Test MarketData
    from loguru import logger
    import sys

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    market_data = MarketData()

    # Test latest data
    print("\n=== Latest Data ===")
    df = market_data.fetch_latest_data(limit=10)
    print(df.tail())
    print(f"\nColumns: {list(df.columns)}")

    # Test market summary
    print("\n=== Market Summary ===")
    summary = market_data.get_market_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    # Test current price
    print("\n=== Current Price ===")
    price = market_data.get_current_price()
    print(f"Current price: ${price:,.2f}")
