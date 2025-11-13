# IBKR MCP Server

A Model Context Protocol (MCP) server that provides AI models with secure access to Interactive Brokers (IBKR) trading data and functionality through the TWS API.


## ⚠️⚠️⚠️ Disclaimer ⚠️⚠️⚠️

This software is for educational and development purposes. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this software. Always test with paper trading before using with real money.


## 🚀 Features

- **Account Management**: Get positions, portfolio details, and account summaries
- **Market Data**: Retrieve historical price data and real-time market information
- **Trading Operations**: Place orders, manage positions, and track executions
- **MCP Integration**: Seamless integration with AI models supporting MCP protocol
- **Safety Features**: Read-only mode, configurable trading restrictions, and comprehensive validation
- **High Availability**: Automatic reconnection, heartbeat monitoring, and graceful error handling

## 📋 Prerequisites

- Python 3.10+
- Interactive Brokers TWS or IB Gateway
- Active IBKR account (paper trading recommended for testing)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ibkr_mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure TWS/IB Gateway**:
   - Enable API connections in TWS/Gateway settings
   - Set socket port (default: 7497 for paper trading, 7496 for live)
   - Configure trusted IP addresses if needed

4. **Configure the server**:
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config/config.yaml with your settings
   ```


## 🚀 Usage

### Starting the Server

```bash
# Using the run script
python run.py
```

The server will:
1. Connect to TWS/IB Gateway
2. Start the MCP server on the configured port
3. Begin heartbeat monitoring
4. Log all activities

### Available MCP Tools

#### Account Tools
- `get_positions()` - Get current account positions
- `get_account_summary()` - Get account balance and metrics
- `get_portfolio()` - Get detailed portfolio information

#### Market Data Tools
- `get_historical_data(symbol, duration, bar_size)` - Get historical price data
- `get_market_data(symbol)` - Get real-time market data
- `get_contract_details(symbol)` - Get contract specifications

#### Trading Tools
- `place_order(symbol, action, quantity, order_type, ...)` - Place buy/sell orders
- `get_orders(status)` - Get order history and status
- `cancel_order(order_id)` - Cancel pending orders
- `get_trades()` - Get execution history

### Example AI Interactions

```
AI: "What are my current positions?"
→ Calls get_positions() tool

AI: "Buy 100 shares of AAPL at market price"
→ Calls place_order(symbol="AAPL", action="BUY", quantity=100, order_type="MKT")

AI: "Show me AAPL's price history for the last week"
→ Calls get_historical_data(symbol="AAPL", duration="1 W", bar_size="1 day")
```

## 🔗 Related Links

- [Interactive Brokers API Documentation](https://interactivebrokers.github.io/tws-api/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
