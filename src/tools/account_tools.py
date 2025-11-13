"""
Account-related MCP tools for retrieving positions and account information.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from src.connection.ibapi_client import IBAPIClient

logger = logging.getLogger(__name__)


async def get_positions(ib: IBAPIClient, account: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get current account positions.

    Args:
        ib: IBAPIClient connection instance
        account: Account ID (optional)

    Returns:
        List of position dictionaries
    """
    try:
        # Clear previous position data
        ib.positions.clear()

        # Request positions
        ib.reqPositions()

        # Wait for position data to be received
        await asyncio.sleep(2)

        # Get positions from the client
        positions_dict = ib.get_positions_dict()

        result = []
        for key, pos_data in positions_dict.items():
            # Filter by account if specified
            if account and pos_data['account'] != account:
                continue

            contract = pos_data['contract']
            position_data = {
                "symbol": contract.symbol,
                "secType": contract.secType,
                "exchange": contract.exchange,
                "currency": contract.currency,
                "position": float(pos_data['position']),
                "avgCost": float(pos_data['avgCost']) if pos_data['avgCost'] else 0.0,
                "account": pos_data['account']
            }

            # Add contract details for stocks
            if contract.secType == "STK":
                position_data.update({
                    "primaryExchange": getattr(contract, 'primaryExchange', ''),
                    "localSymbol": getattr(contract, 'localSymbol', contract.symbol)
                })

            result.append(position_data)

        logger.info(f"Retrieved {len(result)} positions for account {account or 'default'}")
        return result

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise


async def get_account_summary(ib: IBAPIClient, account: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get account summary information.
    
    Args:
        ib: IBAPIClient connection instance
        account: Account ID (optional)
        tags: Specific tags to retrieve (optional)
    
    Returns:
        Dictionary of account summary data
    """
    try:
        # Default tags if none specified
        if not tags:
            tags = [
                'NetLiquidation', 'TotalCashValue', 'SettledCash', 'AccruedCash',
                'BuyingPower', 'EquityWithLoanValue', 'PreviousEquityWithLoanValue',
                'GrossPositionValue', 'RegTEquity', 'RegTMargin', 'SMA', 'InitMarginReq',
                'MaintMarginReq', 'AvailableFunds', 'ExcessLiquidity', 'Cushion',
                'FullInitMarginReq', 'FullMaintMarginReq', 'FullAvailableFunds',
                'FullExcessLiquidity', 'LookAheadNextChange', 'LookAheadInitMarginReq',
                'LookAheadMaintMarginReq', 'LookAheadAvailableFunds', 'LookAheadExcessLiquidity',
                'HighestSeverity', 'DayTradesRemaining', 'Leverage'
            ]
        
        # Clear previous account data
        ib.account_values.clear()

        # Request account updates
        if not account:
            # Get first managed account if none specified
            managed_accounts = ib.get_managed_accounts()
            if managed_accounts:
                account = managed_accounts[0]
            else:
                raise ValueError("No account specified and no managed accounts available")

        ib.reqAccountUpdates(True, account)

        # Wait for account data to be received
        await asyncio.sleep(3)

        # Stop account updates
        ib.reqAccountUpdates(False, account)

        # Get account values from the client
        account_values_dict = ib.get_account_values_dict()

        # Convert to result format
        result = {}
        for key, item in account_values_dict.items():
            if item['account'] != account:
                continue

            tag = item['key']
            value = item['value']
            currency = item['currency']

            # Try to convert numeric values
            try:
                if value and value != '':
                    numeric_value = float(value)
                    result[tag] = {
                        'value': numeric_value,
                        'currency': currency,
                        'formatted': f"{numeric_value:,.2f} {currency}" if currency else f"{numeric_value:,.2f}"
                    }
                else:
                    result[tag] = {
                        'value': value,
                        'currency': currency,
                        'formatted': value
                    }
            except (ValueError, TypeError):
                result[tag] = {
                    'value': value,
                    'currency': currency,
                    'formatted': value
                }

        logger.info(f"Retrieved account summary with {len(result)} items for account {account}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting account summary: {e}")
        raise


async def get_portfolio(ib: IBAPIClient, account: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get detailed portfolio information.
    
    Args:
        ib: IBAPIClient connection instance
        account: Account ID (optional)
    
    Returns:
        List of portfolio item dictionaries
    """
    try:
        # For IBAPI, portfolio information comes from positions
        # This is a simplified implementation that uses position data
        return await get_positions(ib, account)
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise
