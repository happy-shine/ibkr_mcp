"""
MCP Application - FastMCP server with IBKR tools integration.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP, Context

from config.validators import Config
from src.connection.manager import ConnectionManager
from src.tools import account_tools
from src.tools import historical_tools
from src.tools import trading_tools

logger = logging.getLogger(__name__)


class IBKRMCPServer:
    """IBKR MCP Server using FastMCP."""

    def __init__(self, config: Config):
        self.config = config
        self.connection_manager = ConnectionManager(config)

        # Initialize FastMCP server
        self.app = FastMCP(config.mcp.title)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""

        # Account tools
        @self.app.tool
        async def get_positions(account: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            Get current account positions.

            Args:
                account: Account ID (optional)

            Returns:
                List of position dictionaries
            """
            ib = self.connection_manager.get_ib()
            return await account_tools.get_positions(ib, account)

        @self.app.tool
        async def get_account_summary(
            account: Optional[str] = None,
            tags: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Get account summary information.

            Args:
                account: Account ID (optional)
                tags: Specific tags to retrieve (optional)

            Returns:
                Dictionary of account summary data
            """
            ib = self.connection_manager.get_ib()
            return await account_tools.get_account_summary(ib, account, tags)

        @self.app.tool
        async def get_portfolio(account: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            Get detailed portfolio information.

            Args:
                account: Account ID (optional)

            Returns:
                List of portfolio item dictionaries
            """
            ib = self.connection_manager.get_ib()
            return await account_tools.get_portfolio(ib, account)
        
        # Historical data tools
        @self.app.tool
        async def get_historical_data(
            symbol: str,
            end_date_time: str = '',
            duration: str = "1 D",
            bar_size: str = "1 hour",
            what_to_show: str = "TRADES",
            use_rth: bool = True,
            exchange: str = "SMART",
            currency: str = "USD"
        ) -> List[Dict[str, Any]]:
            """
            Get historical price data for a security.

            Args:
                symbol: Stock symbol
                end_date_time: The correct format is yyyymmdd hh:mm:ss xx/xxxx where yyyymmdd and xx/xxxx are optional. E.g.: 20031126 15:59:00 US/Eastern  Note that there is a space between the date and time, and between the time and time-zone.
                duration: Duration string (e.g., '1 D', '5 D', '1 M', '1 Y')
                bar_size: Bar size (e.g., '1 min', '5 mins', '1 hour', '1 day')
                what_to_show: Data type (TRADES, MIDPOINT, BID, ASK)
                use_rth: Use regular trading hours only
                exchange: Exchange
                currency: Currency

            Returns:
                List of OHLCV bar dictionaries
            """
            ib = self.connection_manager.get_ib()
            return await historical_tools.get_historical_data(
                ib, symbol, end_date_time, duration, bar_size, what_to_show, use_rth, exchange, currency
            )

        @self.app.tool
        async def get_market_data(
            symbol: str,
            exchange: str = "SMART",
            currency: str = "USD"
        ) -> Dict[str, Any]:
            """
            Get current market data for a security.

            Args:
                symbol: Stock symbol
                exchange: Exchange
                currency: Currency

            Returns:
                Dictionary with current market data
            """
            ib = self.connection_manager.get_ib()
            return await historical_tools.get_market_data(ib, symbol, exchange, currency)

        @self.app.tool
        async def get_contract_details(
            symbol: str,
            sec_type: str = "STK",
            exchange: str = "SMART",
            currency: str = "USD"
        ) -> List[Dict[str, Any]]:
            """
            Get contract details for a security.

            Args:
                symbol: Stock symbol
                sec_type: Security type
                exchange: Exchange
                currency: Currency

            Returns:
                List of contract detail dictionaries
            """
            ib = self.connection_manager.get_ib()
            return await historical_tools.get_contract_details(ib, symbol, sec_type, exchange, currency)
        
        # Trading tools
        @self.app.tool
        async def place_order(
            symbol: str,
            action: str,
            quantity: int,
            order_type: str = "MKT",
            limit_price: Optional[float] = None,
            stop_price: Optional[float] = None,
            tif: str = "DAY",
            exchange: str = "SMART",
            currency: str = "USD",
            sec_type: str = "STK",
            strike: Optional[float] = None,
            expiry: Optional[str] = None,
            right: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Place a trading order.

            Args:
                symbol: Stock symbol
                action: Order action (BUY or SELL)
                quantity: Number of shares/contracts
                order_type: Order type (MKT, LMT, STP, STP LMT)
                limit_price: Limit price for limit orders
                stop_price: Stop price for stop orders
                tif: Time in force
                exchange: Exchange
                currency: Currency
                sec_type: Security type (STK, OPT, FUT, etc.)
                strike: Strike price for options
                expiry: Expiry date for options (YYYYMMDD format)
                right: Option right (C for Call, P for Put)

            Returns:
                Dictionary with order information
            """
            ib = self.connection_manager.get_ib()
            try:
                res = await trading_tools.place_order(
                    ib, self.config, symbol, action, quantity, order_type,
                    limit_price, stop_price, tif, exchange, currency, sec_type,
                    strike, expiry, right
                )
                return res
            except Exception as e:
                return {"error": str(e)}

        @self.app.tool
        async def get_orders(status: str = "all") -> List[Dict[str, Any]]:
            """
            Get orders filtered by status.

            Args:
                status: Filter by status (all, open, filled, cancelled)

            Returns:
                List of order dictionaries
            """
            ib = self.connection_manager.get_ib()
            return await trading_tools.get_orders(ib, status)

        @self.app.tool
        async def cancel_order(order_id: int) -> Dict[str, Any]:
            """
            Cancel an open order.

            Args:
                order_id: Order ID to cancel

            Returns:
                Dictionary with cancellation result
            """
            ib = self.connection_manager.get_ib()
            return await trading_tools.cancel_order(ib, order_id)

        @self.app.tool
        async def get_trades() -> List[Dict[str, Any]]:
            """
            Get all trade executions.

            Args:

            Returns:
                List of trade execution dictionaries
            """
            ib = self.connection_manager.get_ib()
            return await trading_tools.get_trades(ib)
    
    async def start(self):
        """Start the MCP server and establish TWS connection."""
        try:
            # Connect to TWS
            logger.info("Connecting to TWS...")
            if not await self.connection_manager.connect():
                raise RuntimeError("Failed to connect to TWS")
            
            logger.info("IBKR MCP Server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start IBKR MCP Server: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server and disconnect from TWS."""
        try:
            await self.connection_manager.disconnect()
            logger.info("IBKR MCP Server stopped")
        except Exception as e:
            logger.error(f"Error stopping IBKR MCP Server: {e}")
    
    def run(self, host: str = None, port: int = None):
        """Run the MCP server."""
        host = host or self.config.mcp.host
        port = port or self.config.mcp.port

        logger.info(f"Starting IBKR MCP Server on {host}:{port}")
        # For FastMCP, we typically run with stdio transport for MCP
        self.app.run(transport="streamable-http")
