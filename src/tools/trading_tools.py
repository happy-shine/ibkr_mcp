"""
Trading MCP tools for order placement and management.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from ibapi.contract import Contract
from ibapi.order import Order
from src.connection.ibapi_client import IBAPIClient
from config.validators import Config

logger = logging.getLogger(__name__)


async def place_order(
    ib: IBAPIClient,
    config: Config,
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
        ib: IBAPIClient connection instance
        config: Configuration object
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
    try:
        # Check if trading is allowed
        if config.ibkr.read_only:
            raise ValueError("Trading is disabled in read-only mode")
        
        # Validate order type is allowed
        if order_type not in config.ibkr.order_types:
            raise ValueError(f"Order type {order_type} is not allowed. Allowed types: {config.ibkr.order_types}")
        
        # Validate TIF is allowed
        if tif not in config.ibkr.tif_types:
            raise ValueError(f"TIF {tif} is not allowed. Allowed TIFs: {config.ibkr.tif_types}")
        
        # Check short selling restrictions
        if action == "SELL" and not config.ibkr.allow_short_selling:
            # Check if we have a position to sell
            ib.reqPositions()
            await asyncio.sleep(1)  # Wait for position data

            positions_dict = ib.get_positions_dict()
            position_qty = 0

            for key, pos_data in positions_dict.items():
                contract = pos_data['contract']
                # Match by symbol and security type
                if (contract.symbol == symbol and contract.secType == sec_type):
                    # For options, also match strike, expiry, and right if provided
                    if sec_type == "OPT":
                        if (strike and hasattr(contract, 'strike') and
                            abs(contract.strike - strike) > 0.01):
                            continue
                        if (expiry and hasattr(contract, 'lastTradeDateOrContractMonth') and
                            contract.lastTradeDateOrContractMonth != expiry):
                            continue
                        if (right and hasattr(contract, 'right') and
                            contract.right != right):
                            continue
                    position_qty += pos_data['position']

            if position_qty < quantity:
                raise ValueError(f"Short selling is not allowed and insufficient position to sell. You want to sell: {quantity}, but position: {position_qty}")
        
        # Create contract based on security type
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency

        if sec_type == "OPT":
            if not all([strike, expiry, right]):
                raise ValueError("Options require strike, expiry, and right parameters")
            contract.strike = strike
            contract.lastTradeDateOrContractMonth = expiry
            contract.right = right
        
        # Create order
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = order_type
        order.tif = tif
        order.eTradeOnly = False
        order.firmQuoteOnly = False

        # Set prices based on order type
        if order_type in ["LMT", "STP LMT"]:
            if limit_price is None:
                raise ValueError(f"Limit price is required for {order_type} orders")
            order.lmtPrice = limit_price
        
        if order_type in ["STP", "STP LMT"]:
            if stop_price is None:
                raise ValueError(f"Stop price is required for {order_type} orders")
            order.auxPrice = stop_price
        
        # Get next valid order ID (thread-safe)
        order_id = ib.get_next_order_id()

        # Place the order
        ib.placeOrder(order_id, contract, order)

        # Wait a moment for order to be acknowledged
        await asyncio.sleep(1)

        # Get order status from the client
        orders_dict = ib.get_orders_dict()
        order_info = orders_dict.get(order_id, {})

        result = {
            "order_id": order_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "order_type": order_type,
            "tif": tif,
            "status": order_info.get('status', 'Submitted'),
            "filled": order_info.get('filled', 0),
            "remaining": order_info.get('remaining', quantity),
            "avg_fill_price": order_info.get('avgFillPrice', 0),
            "last_fill_price": order_info.get('lastFillPrice', 0),
            "timestamp": None  # IBAPI doesn't provide timestamp in the same way
        }

        # Add prices if applicable
        if limit_price is not None:
            result["limit_price"] = limit_price
        if stop_price is not None:
            result["stop_price"] = stop_price

        logger.info(f"Placed {action} order for {quantity} shares of {symbol} (Order ID: {order_id})")
        return result
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise


async def get_orders(ib: IBAPIClient, status: str = "all") -> List[Dict[str, Any]]:
    """
    Get orders filtered by status.

    Args:
        ib: IBAPIClient connection instance
        status: Filter by status (all, open, filled, cancelled)

    Returns:
        List of order dictionaries
    """
    try:
        # Clear previous order data to get fresh results
        ib.orders.clear()
        logger.info("Cleared previous order data")

        # Request completed orders (filled and cancelled) - requires TWS 976+
        logger.info("Requesting completed orders...")
        ib.reqCompletedOrders(False)  # False = all completed orders, not just API orders
        await asyncio.sleep(2)  # Wait for completed order data

        # Also request open orders
        logger.info("Requesting all open orders...")
        ib.reqAllOpenOrders()
        await asyncio.sleep(2)  # Wait for open order data

        # Get orders from the client
        orders_dict = ib.get_orders_dict()
        logger.info(f"Retrieved {len(orders_dict)} total orders from client")

        result = []
        for order_id, order_info in orders_dict.items():
            logger.info(f"Processing order {order_id}: {list(order_info.keys())}")
            order_status = order_info.get('status', '').lower()
            logger.info(f"Order {order_id} status: {order_status}")

            # Filter by status
            if status != "all":
                if status == "open" and order_status not in ["submitted", "presubmitted", "pendingsubmit"]:
                    logger.info(f"Skipping order {order_id} - not open (status: {order_status})")
                    continue
                elif status == "filled" and order_status != "filled":
                    logger.info(f"Skipping order {order_id} - not filled (status: {order_status})")
                    continue
                elif status == "cancelled" and order_status != "cancelled":
                    logger.info(f"Skipping order {order_id} - not cancelled (status: {order_status})")
                    continue

            # Get contract and order details
            contract = order_info.get('contract')
            order = order_info.get('order')

            if not contract or not order:
                logger.warning(f"Skipping order {order_id} - missing contract or order data. Contract: {contract is not None}, Order: {order is not None}")
                continue

            order_data = {
                "order_id": order_id,
                "symbol": contract.symbol,
                "action": order.action,
                "quantity": order.totalQuantity,
                "order_type": order.orderType,
                "tif": order.tif,
                "status": order_info.get('status', 'Unknown'),
                "filled": order_info.get('filled', 0),
                "remaining": order_info.get('remaining', order.totalQuantity),
                "avg_fill_price": order_info.get('avgFillPrice', 0),
                "last_fill_price": order_info.get('lastFillPrice', 0),
                "timestamp": None  # IBAPI doesn't provide timestamp in the same way
            }

            # Add commission (simplified for IBAPI)
            order_data["commission"] = 0.0

            # Add prices if available
            if order.lmtPrice:
                order_data["limit_price"] = order.lmtPrice
            if order.auxPrice:
                order_data["stop_price"] = order.auxPrice

            result.append(order_data)

        logger.info(f"Retrieved {len(result)} orders with status filter: {status}")
        return result

    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise


async def cancel_order(ib: IBAPIClient, order_id: int) -> Dict[str, Any]:
    """
    Cancel an open order.

    Args:
        ib: IBAPIClient connection instance
        order_id: Order ID to cancel

    Returns:
        Dictionary with cancellation result
    """
    try:
        # Get orders from the client
        orders_dict = ib.get_orders_dict()
        order_info = orders_dict.get(order_id)

        if not order_info:
            raise ValueError(f"Order with ID {order_id} not found")

        # Check if order can be cancelled
        status = order_info.get('status', '').lower()
        if status in ["filled", "cancelled"]:
            raise ValueError(f"Cannot cancel order with status: {status}")

        # Cancel the order
        ib.cancelOrder(order_id)

        # Wait a moment for cancellation to be processed
        await asyncio.sleep(1)

        # Get updated order info
        orders_dict = ib.get_orders_dict()
        updated_order_info = orders_dict.get(order_id, order_info)

        contract = order_info.get('contract')
        order = order_info.get('order')

        result = {
            "order_id": order_id,
            "symbol": contract.symbol if contract else "Unknown",
            "action": order.action if order else "Unknown",
            "quantity": order.totalQuantity if order else 0,
            "status": updated_order_info.get('status', 'Cancelled'),
            "message": f"Cancellation request sent for order {order_id}"
        }

        logger.info(f"Cancelled order {order_id}")
        return result

    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise


async def get_trades(ib: IBAPIClient) -> List[Dict[str, Any]]:
    """
    Get all trade executions.

    Args:
        ib: IBAPIClient connection instance

    Returns:
        List of trade execution dictionaries
    """
    try:
        # Request executions
        from ibapi.execution import ExecutionFilter
        exec_filter = ExecutionFilter()
        req_id = ib.get_next_request_id()
        ib.reqExecutions(req_id, exec_filter)

        # Wait for execution data
        await asyncio.sleep(2)

        # Get trades from the client
        trades_dict = ib.get_trades_dict()

        result = []
        for exec_id, trade_data in trades_dict.items():
            execution = trade_data.get('execution')
            contract = trade_data.get('contract')
            commission = trade_data.get('commission')

            if not execution or not contract:
                continue

            execution_data = {
                "order_id": execution.orderId,
                "symbol": contract.symbol,
                "action": execution.side,
                "quantity": execution.shares,
                "price": execution.price,
                "commission": commission.commission if commission else 0,
                "execution_id": execution.execId,
                "time": execution.time,
                "exchange": execution.exchange,
                "side": execution.side,
                "cumQty": execution.cumQty,
                "avgPrice": execution.avgPrice
            }
            result.append(execution_data)

        logger.info(f"Retrieved {len(result)} trade executions")
        return result

    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        raise
