"""
IBAPI Client wrapper - Provides a unified interface for IBAPI EClient/EWrapper.
"""
import asyncio
import logging
import threading
import time
from typing import Optional, Dict, Any, List
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.execution import Execution
from ibapi.commission_report import CommissionReport

logger = logging.getLogger(__name__)


class IBAPIClient(EWrapper, EClient):
    """
    IBAPI Client that combines EClient and EWrapper functionality.
    Provides async-friendly interface for Interactive Brokers API.
    """
    
    def __init__(self):
        EClient.__init__(self, self)
        EWrapper.__init__(self)
        
        # Connection state
        self.connected = False
        self.next_valid_order_id = None
        self.managed_accounts = []
        
        # Data storage
        self.positions = {}
        self.account_values = {}
        self.orders = {}
        self.trades = {}
        self.historical_data = {}
        self.market_data = {}
        self.contract_details = {}
        self.option_params = {}  # For option chain parameters
        
        # Event handling
        self.events = {}
        self.request_id_counter = 1000
        
        # Threading
        self.api_thread = None
        self.lock = threading.Lock()
        
    def get_next_request_id(self) -> int:
        """Get next available request ID."""
        with self.lock:
            self.request_id_counter += 1
            return self.request_id_counter

    def get_next_order_id(self) -> int:
        """Get next available order ID and increment it."""
        with self.lock:
            if self.next_valid_order_id is None:
                raise RuntimeError("No valid order ID available")
            order_id = self.next_valid_order_id
            self.next_valid_order_id += 1
            return order_id
    
    def connect_sync(self, host: str, port: int, client_id: int, timeout: int = 10) -> bool:
        """
        Connect to TWS/Gateway synchronously.
        """
        try:
            self.connect(host, port, client_id)
            
            # Start API thread
            self.api_thread = threading.Thread(target=self.run, daemon=True)
            self.api_thread.start()
            
            # Wait for connection
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info(f"Connected to TWS at {host}:{port} with client ID {client_id}")
                return True
            else:
                logger.error("Connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect_sync(self):
        """Disconnect from TWS/Gateway."""
        if self.isConnected():
            self.disconnect()
        self.connected = False
        
    # EWrapper callback implementations
    def connectAck(self):
        """Called when connection is acknowledged."""
        logger.debug("Connection acknowledged")
    
    def nextValidId(self, orderId: int):
        """Receives next valid order ID."""
        self.next_valid_order_id = orderId
        self.connected = True
        logger.debug(f"Next valid order ID: {orderId}")

        # Reset request ID counter on new connection to avoid conflicts
        with self.lock:
            self.request_id_counter = 1000
    
    def managedAccounts(self, accountsList: str):
        """Receives managed accounts list."""
        self.managed_accounts = accountsList.split(',') if accountsList else []
        logger.debug(f"Managed accounts: {self.managed_accounts}")
    
    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
        """Handle errors."""
        if errorCode in [2104, 2106, 2158]:  # Informational messages
            logger.debug(f"Info {errorCode}: {errorString}")
        elif errorCode < 1000:  # System errors
            logger.error(f"System error {errorCode}: {errorString}")
        else:  # Warning messages
            logger.warning(f"Warning {errorCode}: {errorString}")
    
    def connectionClosed(self):
        """Called when connection is closed."""
        self.connected = False
        logger.info("Connection closed")
    
    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        """Receive position data."""
        key = f"{account}_{contract.conId}"
        self.positions[key] = {
            'account': account,
            'contract': contract,
            'position': position,
            'avgCost': avgCost
        }
    
    def positionEnd(self):
        """Called when all positions have been received."""
        logger.debug("Position data complete")
    
    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        """Receive account value updates."""
        account_key = f"{accountName}_{key}_{currency}"
        self.account_values[account_key] = {
            'key': key,
            'value': val,
            'currency': currency,
            'account': accountName
        }
    
    def accountDownloadEnd(self, accountName: str):
        """Called when account download is complete."""
        logger.debug(f"Account download complete for {accountName}")
    
    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float,
                   avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float,
                   clientId: int, whyHeld: str, mktCapPrice: float):
        """Receive order status updates."""
        if orderId not in self.orders:
            self.orders[orderId] = {}
        self.orders[orderId].update({
            'orderId': orderId,
            'status': status,
            'filled': filled,
            'remaining': remaining,
            'avgFillPrice': avgFillPrice,
            'permId': permId,
            'parentId': parentId,
            'lastFillPrice': lastFillPrice,
            'clientId': clientId,
            'whyHeld': whyHeld,
            'mktCapPrice': mktCapPrice
        })
    
    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState):
        """Receive open order data."""
        if orderId not in self.orders:
            self.orders[orderId] = {}
        self.orders[orderId].update({
            'contract': contract,
            'order': order,
            'orderState': orderState
        })
    
    def openOrderEnd(self):
        """Called when all open orders have been received."""
        logger.debug("Open orders data complete")

    def completedOrder(self, contract: Contract, order: Order, orderState):
        """Receive completed order data."""
        order_id = order.orderId
        if order_id not in self.orders:
            self.orders[order_id] = {}
        self.orders[order_id].update({
            'contract': contract,
            'order': order,
            'orderState': orderState
        })
        logger.debug(f"Received completed order: {order_id} - {contract.symbol}")

    def completedOrdersEnd(self):
        """Called when all completed orders have been received."""
        logger.debug("Completed orders data complete")

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        """Receive execution details."""
        exec_id = execution.execId
        self.trades[exec_id] = {
            'reqId': reqId,
            'contract': contract,
            'execution': execution
        }

    def execDetailsEnd(self, reqId: int):
        """Called when all execution details have been received."""
        logger.debug(f"Execution details complete for request {reqId}")

    def commissionReport(self, commissionReport: CommissionReport):
        """Receive commission report."""
        exec_id = commissionReport.execId
        if exec_id in self.trades:
            self.trades[exec_id]['commission'] = commissionReport

    def historicalData(self, reqId: int, bar):
        """Receive historical data bars."""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []

        bar_data = {
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'wap': getattr(bar, 'wap', 0),  # Some bar types don't have wap
            'count': getattr(bar, 'count', 0)  # Some bar types don't have count
        }
        self.historical_data[reqId].append(bar_data)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Called when historical data is complete."""
        logger.debug(f"Historical data complete for request {reqId}")

    def tickPrice(self, reqId: int, tickType: int, price: float, attrib):
        """Receive tick price data."""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        self.market_data[reqId][f'price_{tickType}'] = price

    def tickSize(self, reqId: int, tickType: int, size: int):
        """Receive tick size data."""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        self.market_data[reqId][f'size_{tickType}'] = size

    def tickString(self, reqId: int, tickType: int, value: str):
        """Receive tick string data."""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        self.market_data[reqId][f'string_{tickType}'] = value

    def contractDetails(self, reqId: int, contractDetails):
        """Receive contract details."""
        if reqId not in self.contract_details:
            self.contract_details[reqId] = []
        self.contract_details[reqId].append(contractDetails)

    def contractDetailsEnd(self, reqId: int):
        """Called when contract details are complete."""
        logger.debug(f"Contract details complete for request {reqId}")

    def securityDefinitionOptionParameter(self, reqId: int, exchange: str,
                                        underlyingConId: int, tradingClass: str,
                                        multiplier: str, expirations, strikes):
        """Receive option chain parameters."""
        if reqId not in self.option_params:
            self.option_params[reqId] = []

        option_param = {
            'exchange': exchange,
            'underlyingConId': underlyingConId,
            'tradingClass': tradingClass,
            'multiplier': multiplier,
            'expirations': list(expirations) if expirations else [],
            'strikes': list(strikes) if strikes else []
        }
        self.option_params[reqId].append(option_param)
        logger.debug(f"Received option parameters for request {reqId}, exchange {exchange}")

    def securityDefinitionOptionParameterEnd(self, reqId: int):
        """Called when option parameters are complete."""
        logger.debug(f"Option parameters complete for request {reqId}")

    def currentTime(self, time: int):
        """Receive current server time."""
        logger.debug(f"Server time: {time}")

    # Utility methods for async compatibility
    async def wait_for_connection(self, timeout: int = 10) -> bool:
        """Wait for connection to be established."""
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        return self.connected

    async def wait_for_next_valid_id(self, timeout: int = 10) -> Optional[int]:
        """Wait for next valid order ID."""
        start_time = time.time()
        while self.next_valid_order_id is None and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        return self.next_valid_order_id

    def is_connected(self) -> bool:
        """Check if connected to TWS."""
        return self.connected and self.isConnected()

    def get_managed_accounts(self) -> List[str]:
        """Get list of managed accounts."""
        return self.managed_accounts.copy()

    def get_positions_dict(self) -> Dict[str, Any]:
        """Get current positions as dictionary."""
        return self.positions.copy()

    def get_account_values_dict(self) -> Dict[str, Any]:
        """Get current account values as dictionary."""
        return self.account_values.copy()

    def get_orders_dict(self) -> Dict[int, Any]:
        """Get current orders as dictionary."""
        return self.orders.copy()

    def get_trades_dict(self) -> Dict[str, Any]:
        """Get current trades as dictionary."""
        return self.trades.copy()

    def get_option_params_dict(self) -> Dict[int, Any]:
        """Get current option parameters as dictionary."""
        return self.option_params.copy()

    def clear_data(self):
        """Clear all cached data."""
        self.positions.clear()
        self.account_values.clear()
        self.orders.clear()
        self.trades.clear()
        self.historical_data.clear()
        self.market_data.clear()
        self.contract_details.clear()
        self.option_params.clear()
