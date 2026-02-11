"""
Binance API client wrapper using CCXT.
Handles connection, authentication, and API calls with rate limiting and error handling.
"""

import ccxt
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config.settings import get_settings
from src.config.constants import OrderSide, OrderType


class BinanceClient:
    """
    Wrapper around CCXT Binance exchange with error handling and rate limiting.
    """

    def __init__(self, demo_mode: Optional[bool] = None):
        """
        Initialize Binance client.

        Args:
            demo_mode: Use demo mode for paper trading (None = use setting from config)
        """
        self.settings = get_settings()
        self.demo_mode = demo_mode if demo_mode is not None else self.settings.is_demo_mode

        # Initialize CCXT exchange
        self.exchange = self._init_exchange()

        logger.info(
            f"BinanceClient initialized (demo_mode={self.demo_mode}, "
            f"symbol={self.settings.trading_symbol})"
        )

    def _init_exchange(self) -> ccxt.binance:
        """
        Initialize CCXT Binance exchange.

        Returns:
            CCXT Binance exchange instance
        """
        if self.demo_mode:
            api_key = self.settings.binance_demo_api_key
            api_secret = self.settings.binance_demo_api_secret
            if not api_key or not api_secret:
                raise ValueError("Demo mode requires BINANCE_DEMO_API_KEY and BINANCE_DEMO_API_SECRET")
        else:
            api_key = self.settings.binance_api_key
            api_secret = self.settings.binance_api_secret
            if not api_key or not api_secret:
                raise ValueError("Live mode requires BINANCE_API_KEY and BINANCE_API_SECRET")

        config = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "rateLimit": 60000 / self.settings.api_rate_limit,  # Convert to ms
            "timeout": self.settings.api_timeout * 1000,  # Convert to ms
            "options": {
                # CCXT는 "future" (s 없음)를 사용, settings의 "futures"와 다름
                "defaultType": "future" if self.settings.market_type == "futures" else self.settings.market_type,
                "adjustForTimeDifference": True,
            },
        }

        # Demo mode: Use Binance demo trading API (https://demo-api.binance.com)
        # Requires demo API keys from https://testnet.binance.vision/
        if self.demo_mode:
            logger.warning(
                f"⚠️  Demo mode enabled - Using Binance Demo API "
                f"(demo-api.binance.com, {self.settings.market_type})"
            )
            if self.settings.market_type == "futures":
                # Futures Demo: demo-fapi.binance.com (Spot Demo와 도메인 다름)
                # CCXT는 urls.api 내부의 키를 사용하므로 반드시 api 딕셔너리 안에 설정
                config["urls"] = {
                    "api": {
                        "fapiPublic": "https://demo-fapi.binance.com/fapi/v1",
                        "fapiPrivate": "https://demo-fapi.binance.com/fapi/v1",
                        "fapiPublicV2": "https://demo-fapi.binance.com/fapi/v2",
                        "fapiPrivateV2": "https://demo-fapi.binance.com/fapi/v2",
                    }
                }
            else:
                # Spot Demo: demo-api.binance.com
                config["urls"] = {
                    "api": {
                        "public": "https://demo-api.binance.com/api/v3",
                        "private": "https://demo-api.binance.com/api/v3",
                    },
                }
            config["options"]["fetchCurrencies"] = False

        exchange = ccxt.binance(config)

        # Load markets
        try:
            exchange.load_markets()
            logger.info(f"Loaded {len(exchange.markets)} markets from Binance")
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise

        return exchange

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable)),
    )
    def fetch_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch current ticker data.

        Args:
            symbol: Trading symbol (default: from settings)

        Returns:
            Ticker data dictionary
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.debug(f"Fetched ticker for {symbol}: {ticker['last']}")
            return ticker
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable)),
    )
    def fetch_ohlcv(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[List]:
        """
        Fetch OHLCV (candlestick) data.

        Args:
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)
            since: Start time (default: 500 periods ago)
            limit: Number of candles to fetch (max: 1000)

        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe

        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)

        try:
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since_ms,
                limit=limit,
            )
            logger.debug(
                f"Fetched {len(ohlcv)} {timeframe} candles for {symbol} "
                f"(from {datetime.fromtimestamp(ohlcv[0][0]/1000)})"
            )
            return ohlcv
        except Exception as e:
            logger.error(
                f"Failed to fetch OHLCV for {symbol} ({timeframe}): {e}"
            )
            raise

    def fetch_ohlcv_range(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> List[List]:
        """
        Fetch OHLCV data for a specific date range.
        Handles pagination for large date ranges.

        Args:
            start_date: Start date
            end_date: End date
            symbol: Trading symbol (default: from settings)
            timeframe: Timeframe (default: from settings)

        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        symbol = symbol or self.settings.trading_symbol
        timeframe = timeframe or self.settings.trading_timeframe

        all_candles = []
        current_date = start_date

        # Calculate approximate number of candles per request
        timeframe_seconds = self._timeframe_to_seconds(timeframe)
        candles_per_request = 1000

        logger.info(
            f"Fetching {timeframe} candles for {symbol} "
            f"from {start_date} to {end_date}"
        )

        while current_date < end_date:
            try:
                candles = self.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=current_date,
                    limit=candles_per_request,
                )

                if not candles:
                    break

                all_candles.extend(candles)

                # Move to next batch
                last_timestamp = candles[-1][0]
                current_date = datetime.fromtimestamp(last_timestamp / 1000)
                current_date += timedelta(seconds=timeframe_seconds)

                # Avoid fetching beyond end_date
                if current_date >= end_date:
                    break

            except Exception as e:
                logger.error(f"Error fetching candles at {current_date}: {e}")
                break

        # Filter out candles beyond end_date
        end_timestamp = int(end_date.timestamp() * 1000)
        all_candles = [c for c in all_candles if c[0] <= end_timestamp]

        logger.info(f"Fetched total of {len(all_candles)} candles")
        return all_candles

    @staticmethod
    def _timeframe_to_seconds(timeframe: str) -> int:
        """Convert timeframe string to seconds."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])

        units = {
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
            "M": 2592000,  # Approximate
        }

        return value * units.get(unit, 60)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable)),
    )
    def fetch_balance(self, account_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch account balance.

        Args:
            account_type: Account type override (e.g., "spot", "future")

        Returns:
            Balance dictionary
        """
        try:
            params = {"type": account_type} if account_type else None
            balance = self.exchange.fetch_balance(params) if params else self.exchange.fetch_balance()
            logger.debug("Fetched account balance")
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable)),
    )
    def fetch_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch order details.

        Args:
            order_id: Order ID
            symbol: Trading symbol (default: from settings)

        Returns:
            Order details
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            logger.debug(f"Fetched order {order_id} for {symbol}")
            return order
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ccxt.NetworkError, ccxt.ExchangeNotAvailable)),
    )
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch open orders.

        Args:
            symbol: Trading symbol (default: from settings)

        Returns:
            List of open orders
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            logger.debug(f"Fetched {len(orders)} open orders for {symbol}")
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            raise

    def create_market_order(
        self,
        side: OrderSide,
        amount: float,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a market order.

        Args:
            side: Order side (BUY or SELL)
            amount: Order amount (in base currency)
            symbol: Trading symbol (default: from settings)

        Returns:
            Order details
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type="market",
                side=side.value,
                amount=amount,
            )
            mode = "[DEMO]" if self.demo_mode else "[LIVE]"
            logger.info(
                f"{mode} Created market {side.value} order: {amount} {symbol} (ID: {order['id']})"
            )
            return order
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise

    def create_limit_order(
        self,
        side: OrderSide,
        amount: float,
        price: float,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a limit order.

        Args:
            side: Order side (BUY or SELL)
            amount: Order amount (in base currency)
            price: Limit price
            symbol: Trading symbol (default: from settings)

        Returns:
            Order details
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type="limit",
                side=side.value,
                amount=amount,
                price=price,
            )
            logger.info(
                f"Created limit {side.value} order: {amount} {symbol} @ {price} (ID: {order['id']})"
            )
            return order
        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise

    def create_stop_loss_order(
        self,
        side: OrderSide,
        amount: float,
        stop_price: float,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a stop-loss order.

        Args:
            side: Order side (BUY or SELL)
            amount: Order amount
            stop_price: Stop price
            symbol: Trading symbol (default: from settings)

        Returns:
            Order details
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            order = self.exchange.create_order(
                symbol=symbol,
                type="stop_loss_limit",
                side=side.value,
                amount=amount,
                price=stop_price,
                params={"stopPrice": stop_price},
            )
            logger.info(
                f"Created stop-loss {side.value} order: {amount} {symbol} @ {stop_price}"
            )
            return order
        except Exception as e:
            logger.error(f"Failed to create stop-loss order: {e}")
            raise

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading symbol (default: from settings)

        Returns:
            Cancellation result
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order {order_id} for {symbol}")
            return result
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def cancel_all_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Cancel all open orders.

        Args:
            symbol: Trading symbol (default: from settings)

        Returns:
            List of cancellation results
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            open_orders = self.fetch_open_orders(symbol)
            results = []
            for order in open_orders:
                result = self.cancel_order(order["id"], symbol)
                results.append(result)
            logger.info(f"Cancelled {len(results)} orders for {symbol}")
            return results
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise

    def get_trading_fee(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees for symbol.

        Args:
            symbol: Trading symbol (default: from settings)

        Returns:
            Dictionary with 'maker' and 'taker' fees
        """
        symbol = symbol or self.settings.trading_symbol
        try:
            fees = self.exchange.fetch_trading_fee(symbol)
            logger.debug(f"Trading fees for {symbol}: {fees}")
            return fees
        except Exception as e:
            logger.warning(f"Failed to fetch trading fees, using defaults: {e}")
            # Return default Binance fees
            return {"maker": 0.001, "taker": 0.001}

    def check_connection(self) -> bool:
        """
        Check if connection to Binance is working.

        Returns:
            True if connection is working
        """
        try:
            self.exchange.fetch_time()
            logger.info("Binance connection OK")
            return True
        except Exception as e:
            logger.error(f"Binance connection failed: {e}")
            return False


if __name__ == "__main__":
    # Test Binance client
    from loguru import logger
    import sys

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    client = BinanceClient(demo_mode=True)

    # Test connection
    if client.check_connection():
        print("✅ Connection OK")

        # Test ticker
        ticker = client.fetch_ticker()
        print(f"✅ Current price: ${ticker['last']}")

        # Test OHLCV
        ohlcv = client.fetch_ohlcv(limit=10)
        print(f"✅ Fetched {len(ohlcv)} candles")

        # Test balance (requires valid API keys)
        try:
            balance = client.fetch_balance()
            print(f"✅ Balance fetched: {len(balance['total'])} assets")
        except Exception as e:
            print(f"⚠️  Balance fetch failed (API keys may be invalid): {e}")
    else:
        print("❌ Connection failed")
