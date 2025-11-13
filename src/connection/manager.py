"""
TWS Connection Manager - Manages single IB connection instance with reconnection logic.
"""
import asyncio
import logging
from typing import Optional
from .ibapi_client import IBAPIClient
from config.validators import Config, IBKRSettings


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages TWS connection with automatic reconnection and health monitoring."""

    def __init__(self, config: Config):
        self.config = config
        self.ibkr_config = config.ibkr
        self.connection_config = config.connection
        self.ib: Optional[IBAPIClient] = None
        self.connected = False
        self._connection_lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Establish connection to TWS with retry logic."""
        async with self._connection_lock:
            if self.connected and self.ib and self.ib.is_connected():
                logger.info("Already connected to TWS")
                return True

            self.ib = IBAPIClient()

            for attempt in range(self.connection_config.reconnect_attempts):
                try:
                    logger.info(
                        f"Connecting to TWS at {self.ibkr_config.host}:{self.ibkr_config.port} "
                        f"(attempt {attempt + 1}/{self.connection_config.reconnect_attempts})"
                    )

                    # Connect synchronously in a thread
                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(
                        None,
                        self.ib.connect_sync,
                        self.ibkr_config.host,
                        self.ibkr_config.port,
                        self.ibkr_config.client_id,
                        20
                    )

                    if not success:
                        raise RuntimeError("Connection failed")

                    # Wait for connection to be fully established
                    if not await self.ib.wait_for_connection(timeout=10):
                        raise RuntimeError("Connection timeout")

                    # Wait for next valid order ID
                    if not await self.ib.wait_for_next_valid_id(timeout=10):
                        raise RuntimeError("Failed to receive next valid order ID")

                    self.connected = True
                    logger.info(f"Successfully connected to TWS (Client ID: {self.ibkr_config.client_id})")
                    return True

                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                    if self.ib:
                        self.ib.disconnect_sync()

                    if attempt < self.connection_config.reconnect_attempts - 1:
                        logger.info(f"Retrying in {self.connection_config.reconnect_delay} seconds...")
                        await asyncio.sleep(self.connection_config.reconnect_delay)

            logger.error("Failed to connect to TWS after all attempts")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from TWS."""
        async with self._connection_lock:
            if self.ib and self.ib.is_connected():
                self.ib.disconnect_sync()
                logger.info("Disconnected from TWS")
            self.connected = False
            self.ib = None

    def get_ib(self) -> IBAPIClient:
        """Get the IB connection instance."""
        if not self.connected or not self.ib or not self.ib.is_connected():
            raise RuntimeError("TWS connection not established. Call connect() first.")
        return self.ib

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return (
            self.connected and
            self.ib is not None and
            self.ib.is_connected()
        )

    async def ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if necessary."""
        if not self.is_connected():
            logger.warning("Connection lost, attempting to reconnect...")
            return await self.connect()
        return True

    async def health_check(self) -> bool:
        """Perform health check by requesting current time."""
        try:
            if not self.is_connected():
                return False

            # Request current time as health check
            self.ib.reqCurrentTime()
            # For IBAPI, we just check if the connection is still active
            await asyncio.sleep(0.5)  # Give time for any error responses

            if self.ib.is_connected():
                logger.debug("Health check successful")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
