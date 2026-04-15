---
name: ibkr-trading
description: Use when user asks to trade stocks, check portfolio positions, view market data quotes or history, or manage IBKR gateway connection. Triggers on buying, selling, orders, positions, portfolio, stock prices, PnL, or IBKR mentions.
---

# IBKR Trading

## Overview

Trade stocks, check positions, and view market data via TWS API (ibapi).
All operations use the CLI at `~/PycharmProjects/ibkr_mcp/cli.py` (one-shot, connects per command).
Use the venv: `~/PycharmProjects/ibkr_mcp/.venv/bin/python`

## Prerequisites

TWS must be running and logged in. Start with:
```bash
~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/start_tws.py
```

## Quick Reference

| Task | Command |
|------|---------|
| Start TWS + auto 2FA | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/start_tws.py` |
| Start TWS + wait API | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/start_tws.py --wait` |
| List accounts | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py accounts` |
| View positions | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py positions` |
| Account summary | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py summary` |
| Portfolio | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py portfolio` |
| Get quote | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py quote AAPL` |
| Price history | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py history AAPL --duration "1 M" --bar "1 day"` |
| Contract details | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py details AAPL` |
| Option chain | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py options AAPL` |
| Buy (market) | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py buy AAPL 10 --type MKT --confirm` |
| Buy (limit) | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py buy AAPL 10 --type LMT --price 190.50 --confirm` |
| Sell | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py sell AAPL 5 --type MKT --confirm` |
| Cancel order | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py cancel ORDER_ID` |
| List orders | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py orders` |
| List trades | `~/PycharmProjects/ibkr_mcp/.venv/bin/python ~/PycharmProjects/ibkr_mcp/cli.py trades` |

## History Parameters

| Duration | Meaning | Bar Size | Meaning |
|----------|---------|----------|---------|
| 1 D | 1 day | 1 min | 1 minute |
| 5 D | 5 days | 5 mins | 5 minutes |
| 1 M | 1 month | 1 hour | 1 hour |
| 3 M | 3 months | 1 day | 1 day |
| 1 Y | 1 year | 1 week | 1 week |

## Buy/Sell Extra Options

- `--type MKT|LMT|STP|STP LMT` — order type
- `--price 190.50` — limit price (required for LMT)
- `--tif DAY|GTC|IOC|FOK` — time in force
- `--extended` — allow pre/after-market execution
- `--confirm` — required flag to place order

## Workflow

1. **Check TWS**: If CLI errors with "Cannot connect", run `start_tws.py` first
2. **Before trading**: ALWAYS confirm with user. NEVER place orders without explicit approval
3. **After trading**: Show order result and suggest checking `orders` or `positions`

## Safety

- All buy/sell commands require `--confirm` flag
- ALWAYS ask user for confirmation before executing any trade
- Show order details (symbol, qty, type, price) before confirming
- Never auto-confirm trades without user approval
