"""
Historical data MCP tools for retrieving market data and price history.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ibapi.contract import Contract
from src.connection.ibapi_client import IBAPIClient

logger = logging.getLogger(__name__)


async def get_historical_data(
    ib: IBAPIClient,
    symbol: str,
    end_date_time: str = "",
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
        ib: IBAPIClient connection instance
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
    try:
        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency

        # Get request ID and clear previous data
        req_id = ib.get_next_request_id()
        if req_id in ib.historical_data:
            del ib.historical_data[req_id]

        # Request historical data
        ib.reqHistoricalData(
            reqId=req_id,
            contract=contract,
            endDateTime=end_date_time,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=1 if use_rth else 0,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )

        # Wait for historical data to be received
        await asyncio.sleep(3)

        # Get historical data from the client
        bars = ib.historical_data.get(req_id, [])
        
        # Convert to list of dictionaries
        result = []
        for bar in bars:
            bar_data = {
                "date": bar.get('date', ''),
                "open": float(bar.get('open', 0)),
                "high": float(bar.get('high', 0)),
                "low": float(bar.get('low', 0)),
                "close": float(bar.get('close', 0)),
                "volume": int(bar.get('volume', 0)),
                "average": float(bar.get('wap', 0)),  # WAP is weighted average price
                "barCount": int(bar.get('count', 0))
            }
            result.append(bar_data)

        logger.info(f"Retrieved {len(result)} historical bars for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {e}")
        raise


async def get_market_data(
    ib: IBAPIClient,
    symbol: str,
    exchange: str = "SMART",
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    Get current market data for a security.

    Args:
        ib: IBAPIClient connection instance
        symbol: Stock symbol
        exchange: Exchange
        currency: Currency

    Returns:
        Dictionary with current market data
    """
    try:
        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency

        # Get request ID and clear previous data
        req_id = ib.get_next_request_id()
        if req_id in ib.market_data:
            del ib.market_data[req_id]

        # Request market data
        ib.reqMktData(req_id, contract, '', False, False, [])

        # Wait for data to be populated
        await asyncio.sleep(3)  # Give some time for data to arrive

        # Get market data from the client
        market_data = ib.market_data.get(req_id, {})

        # Helper function to safely convert values
        def safe_float(value):
            try:
                if value is None or str(value).lower() == 'nan':
                    return None
                return float(value) if float(value) > 0 else None
            except (ValueError, TypeError):
                return None

        def safe_int(value):
            try:
                if value is None or str(value).lower() == 'nan':
                    return None
                return int(value) if int(value) > 0 else None
            except (ValueError, TypeError):
                return None

        # Map tick types to field names (simplified mapping)
        result = {
            "symbol": symbol,
            "exchange": exchange,
            "currency": currency,
            "bid": safe_float(market_data.get('price_1')),  # Bid price
            "ask": safe_float(market_data.get('price_2')),  # Ask price
            "last": safe_float(market_data.get('price_4')),  # Last price
            "bidSize": safe_int(market_data.get('size_0')),  # Bid size
            "askSize": safe_int(market_data.get('size_3')),  # Ask size
            "lastSize": safe_int(market_data.get('size_5')),  # Last size
            "volume": safe_int(market_data.get('size_8')),  # Volume
            "high": safe_float(market_data.get('price_6')),  # High
            "low": safe_float(market_data.get('price_7')),  # Low
            "close": safe_float(market_data.get('price_9')),  # Close
            "timestamp": datetime.now().isoformat()
        }

        # Cancel market data subscription
        ib.cancelMktData(req_id)

        logger.info(f"Retrieved market data for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise


async def get_contract_details(
    ib: IBAPIClient,
    symbol: str,
    sec_type: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD"
) -> List[Dict[str, Any]]:
    """
    Get contract details for a security.

    Args:
        ib: IBAPIClient connection instance
        symbol: Stock symbol
        sec_type: Security type
        exchange: Exchange
        currency: Currency

    Returns:
        List of contract detail dictionaries
    """
    try:
        # Create contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency

        # Get request ID and clear previous data
        req_id = ib.get_next_request_id()
        if req_id in ib.contract_details:
            del ib.contract_details[req_id]

        # Request contract details
        ib.reqContractDetails(req_id, contract)

        # Wait for contract details to be received
        await asyncio.sleep(2)

        # Get contract details from the client
        contract_details = ib.contract_details.get(req_id, [])
        
        result = []
        for detail in contract_details:
            contract = detail.contract
            contract_info = {
                "conId": contract.conId,
                "symbol": contract.symbol,
                "secType": contract.secType,
                "exchange": contract.exchange,
                "primaryExchange": contract.primaryExchange,
                "currency": contract.currency,
                "localSymbol": contract.localSymbol,
                "tradingClass": contract.tradingClass,
                "marketName": detail.marketName,
                "minTick": float(detail.minTick),
                "priceMagnifier": int(detail.priceMagnifier),
                "orderTypes": detail.orderTypes.split(',') if detail.orderTypes else [],
                "validExchanges": detail.validExchanges.split(',') if detail.validExchanges else [],
                "timeZoneId": detail.timeZoneId,
                "tradingHours": detail.tradingHours,
                "liquidHours": detail.liquidHours
            }
            result.append(contract_info)
        
        logger.info(f"Retrieved {len(result)} contract details for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting contract details for {symbol}: {e}")
        raise
