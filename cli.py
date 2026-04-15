#!/usr/bin/env python3
"""
IBKR CLI - One-shot commands via TWS API (ibapi).
Connects, executes, disconnects.

Usage:
    python cli.py positions
    python cli.py summary
    python cli.py history AAPL --duration "1 M" --bar "1 day"
    python cli.py quote AAPL
    python cli.py orders
    python cli.py buy AAPL 10 --type MKT --confirm
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.validators import Config
from src.connection.ibapi_client import IBAPIClient
from src.tools import account_tools, historical_tools, trading_tools


def load_config():
    config_path = project_root / "config" / "config.yaml"
    if config_path.exists():
        return Config.from_yaml(str(config_path))
    return Config.from_env()


def connect(config) -> IBAPIClient:
    ib = IBAPIClient()
    ok = ib.connect_sync(config.ibkr.host, config.ibkr.port, config.ibkr.client_id, timeout=10)
    if not ok:
        print(f"Cannot connect to TWS at {config.ibkr.host}:{config.ibkr.port}", file=sys.stderr)
        sys.exit(1)
    # Wait for next valid order ID
    import time
    for _ in range(50):
        if ib.next_valid_order_id is not None:
            break
        time.sleep(0.1)
    return ib


def out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


async def run_command(ib, config, args):
    cmd = args.command

    if cmd == "accounts":
        out(ib.get_managed_accounts())

    elif cmd == "positions":
        result = await account_tools.get_positions(ib, args.account if hasattr(args, 'account') else None)
        out(result)

    elif cmd == "summary":
        result = await account_tools.get_account_summary(ib, args.account if hasattr(args, 'account') else None)
        out(result)

    elif cmd == "portfolio":
        result = await account_tools.get_portfolio(ib, args.account if hasattr(args, 'account') else None)
        out(result)

    elif cmd == "history":
        result = await historical_tools.get_historical_data(
            ib, args.symbol,
            end_date_time=args.end or "",
            duration=args.duration,
            bar_size=args.bar,
            what_to_show=args.show,
            use_rth=not args.extended,
            exchange=args.exchange,
            currency=args.currency,
        )
        out(result)

    elif cmd == "quote":
        result = await historical_tools.get_quote_from_history(
            ib, args.symbol,
            exchange=args.exchange if hasattr(args, 'exchange') else "SMART",
            currency=args.currency if hasattr(args, 'currency') else "USD",
        )
        out(result)

    elif cmd == "details":
        result = await historical_tools.get_contract_details(
            ib, args.symbol,
            sec_type=args.sec_type if hasattr(args, 'sec_type') else "STK",
            exchange=args.exchange if hasattr(args, 'exchange') else "SMART",
            currency=args.currency if hasattr(args, 'currency') else "USD",
        )
        out(result)

    elif cmd == "options":
        result = await historical_tools.get_option_chain(
            ib, args.symbol,
            exchange=args.exchange if hasattr(args, 'exchange') else "",
        )
        out(result)

    elif cmd == "orders":
        result = await trading_tools.get_orders(ib, args.status if hasattr(args, 'status') else "all")
        out(result)

    elif cmd == "trades":
        result = await trading_tools.get_trades(ib)
        out(result)

    elif cmd == "buy":
        result = await trading_tools.place_order(
            ib, config, args.symbol, "BUY", args.qty,
            order_type=args.type,
            limit_price=args.price,
            tif=args.tif,
            outside_rth=args.extended if hasattr(args, 'extended') else False,
        )
        out(result)

    elif cmd == "sell":
        result = await trading_tools.place_order(
            ib, config, args.symbol, "SELL", args.qty,
            order_type=args.type,
            limit_price=args.price,
            tif=args.tif,
            outside_rth=args.extended if hasattr(args, 'extended') else False,
        )
        out(result)

    elif cmd == "cancel":
        result = await trading_tools.cancel_order(ib, args.order_id)
        out(result)


def main():
    parser = argparse.ArgumentParser(prog="ibkr", description="IBKR Trading CLI")
    sub = parser.add_subparsers(dest="command")

    # Accounts
    sub.add_parser("accounts")

    # Positions
    p = sub.add_parser("positions")
    p.add_argument("--account", default=None)

    # Summary
    s = sub.add_parser("summary")
    s.add_argument("--account", default=None)

    # Portfolio
    pf = sub.add_parser("portfolio")
    pf.add_argument("--account", default=None)

    # History
    h = sub.add_parser("history")
    h.add_argument("symbol")
    h.add_argument("--duration", default="1 M")
    h.add_argument("--bar", default="1 day")
    h.add_argument("--show", default="TRADES")
    h.add_argument("--end", default="")
    h.add_argument("--exchange", default="SMART")
    h.add_argument("--currency", default="USD")
    h.add_argument("--extended", action="store_true")

    # Quote
    q = sub.add_parser("quote")
    q.add_argument("symbol")
    q.add_argument("--exchange", default="SMART")
    q.add_argument("--currency", default="USD")

    # Contract details
    d = sub.add_parser("details")
    d.add_argument("symbol")
    d.add_argument("--sec-type", default="STK")
    d.add_argument("--exchange", default="SMART")
    d.add_argument("--currency", default="USD")

    # Option chain
    o = sub.add_parser("options")
    o.add_argument("symbol")
    o.add_argument("--exchange", default="")

    # Orders
    od = sub.add_parser("orders")
    od.add_argument("--status", default="all", choices=["all", "open", "filled", "cancelled"])

    # Trades
    sub.add_parser("trades")

    # Buy
    b = sub.add_parser("buy")
    b.add_argument("symbol")
    b.add_argument("qty", type=int)
    b.add_argument("--type", default="MKT", choices=["MKT", "LMT", "STP", "STP LMT"])
    b.add_argument("--price", type=float, default=None)
    b.add_argument("--tif", default="DAY")
    b.add_argument("--extended", action="store_true")
    b.add_argument("--confirm", action="store_true", required=True)

    # Sell
    sl = sub.add_parser("sell")
    sl.add_argument("symbol")
    sl.add_argument("qty", type=int)
    sl.add_argument("--type", default="MKT", choices=["MKT", "LMT", "STP", "STP LMT"])
    sl.add_argument("--price", type=float, default=None)
    sl.add_argument("--tif", default="DAY")
    sl.add_argument("--extended", action="store_true")
    sl.add_argument("--confirm", action="store_true", required=True)

    # Cancel
    c = sub.add_parser("cancel")
    c.add_argument("order_id", type=int)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    config = load_config()
    ib = connect(config)

    try:
        asyncio.run(run_command(ib, config, args))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        ib.disconnect_sync()


if __name__ == "__main__":
    main()
