# IBKR MCP Server

A Model Context Protocol (MCP) server that provides AI models with secure access to Interactive Brokers (IBKR) trading data and functionality through the TWS API.


## ⚠️⚠️⚠️ Disclaimer ⚠️⚠️⚠️

This software is for educational and development purposes. Use at your own risk. The authors are not responsible for any financial losses incurred through the use of this software. Always test with paper trading before using with real money.


## 🚀 Features

- **Account Management**: Get positions, portfolio details, and account summaries
- **Market Data**: Retrieve historical price data and real-time market information
- **Trading Operations**: Place orders, manage positions, and track executions
- **MCP Integration**: Seamless integration with AI models supporting MCP protocol
- **One-shot CLI**: Per-command connect-execute-disconnect for quick scripting
- **Automated TWS Launch** (macOS): One command to start TWS and auto-fill TOTP 2FA
- **Claude Code Skill**: Natural-language trading via the bundled `skills/ibkr-trading`
- **Safety Features**: Read-only mode, configurable trading restrictions, and comprehensive validation
- **High Availability**: Automatic reconnection, heartbeat monitoring, and graceful error handling

## 📋 Prerequisites

- Python 3.10+
- Interactive Brokers TWS or IB Gateway
- Active IBKR account (paper trading recommended for testing)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/happy-shine/ibkr_mcp.git
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

### Option A: MCP Server

```bash
python run.py
```

The server will:
1. Connect to TWS/IB Gateway
2. Start the MCP server on the configured port
3. Begin heartbeat monitoring
4. Log all activities

### Option B: One-shot CLI

Lightweight CLI that connects per command and exits — good for shell scripts or ad-hoc queries.

```bash
python cli.py positions
python cli.py summary
python cli.py quote AAPL
python cli.py history AAPL --duration "1 M" --bar "1 day"
python cli.py buy AAPL 10 --type MKT --confirm
python cli.py orders
```

Run `python cli.py --help` for the full command list.

> **Note on quote data**: If you do not have a live market-data subscription, `quote`
> falls back to the most recent daily bar via historical data (no real-time fields).

### Option C: Automated TWS Launch (macOS only)

`start_tws.py` launches TWS via [IBC](https://github.com/IbcAlpha/IBC), detects the
Second-Factor Authentication dialog, generates a TOTP code with
[pyotp](https://github.com/pyauth/pyotp), and types it in through AppleScript
(`osascript`) — fully automated login without touching the keyboard.

```bash
python start_tws.py          # launch and auto-fill 2FA
python start_tws.py --wait   # also block until API port 7496 is listening
```

**Requirements (macOS):**

| Component | Purpose | Link |
|-----------|---------|------|
| [IBC](https://github.com/IbcAlpha/IBC) | Automates TWS launch & login inputs | https://github.com/IbcAlpha/IBC |
| [pyotp](https://github.com/pyauth/pyotp) | RFC 6238 TOTP code generation | https://github.com/pyauth/pyotp |
| `osascript` / AppleScript | Ships with macOS; drives the 2FA dialog | built-in |

**Setup:**

1. Install IBC per its macOS instructions (typically at `~/ibc/`).
2. In `~/ibc/config.ini`, set:
   - `TradingMode=live` (or `paper`)
   - `SecondFactorDevice=Mobile Authenticator`
   - Your IBKR credentials
3. Save your IBKR TOTP secret (the Base32 string from the authenticator QR code) to
   `~/.ibkr-totp-secret` **or** export it as `TOTP_SECRET`.
4. Grant Terminal (or your Python launcher) **Accessibility** permission in
   *System Settings → Privacy & Security → Accessibility* — required for AppleScript
   to interact with the TWS window.

> **Platform note**: `start_tws.py` relies on AppleScript/`osascript` and is **macOS only**.
> Linux/Windows users should either use IBC directly or adapt the GUI-automation layer
> (e.g. `xdotool` on Linux, `pywinauto` on Windows).

### Available MCP Tools

#### Account Tools
- `get_positions()` - Get current account positions
- `get_account_summary()` - Get account balance and metrics
- `get_portfolio()` - Get detailed portfolio information

#### Market Data Tools
- `get_historical_data(symbol, duration, bar_size)` - Get historical price data
- `get_market_data(symbol)` - Get real-time market data
- `get_quote_from_history(symbol)` - Last daily bar as a quote (no subscription needed)
- `get_contract_details(symbol)` - Get contract specifications
- `get_option_chain` - Get Option data

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

## 🤖 Claude Code Skill

A companion skill lives at `skills/ibkr-trading/SKILL.md`. It lets
[Claude Code](https://claude.com/claude-code) dispatch the CLI commands above from
natural-language prompts (e.g. *"show my positions"*, *"quote AAPL"*).

To install, symlink it into your Claude Code skills directory:

```bash
ln -s "$(pwd)/skills/ibkr-trading" ~/.claude/skills/ibkr-trading
```

## 🔗 Related Links & Credits

- [Interactive Brokers TWS API](https://interactivebrokers.github.io/tws-api/) — official Python API (`ibapi`)
- [IBC — Interactive Brokers Controller](https://github.com/IbcAlpha/IBC) — TWS auto-launcher (used by `start_tws.py`)
- [pyotp](https://github.com/pyauth/pyotp) — TOTP/HOTP library (used by `start_tws.py`)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Claude Code](https://claude.com/claude-code) — AI pair-programming CLI that consumes the bundled skill
