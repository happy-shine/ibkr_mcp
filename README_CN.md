# IBKR MCP 服务器

一个 Model Context Protocol (MCP) 服务器，旨在通过 TWS API 为 AI 模型提供安全访问盈透证券 (IBKR) 的交易数据和功能。

## ⚠️⚠️⚠️ 免责声明 ⚠️⚠️⚠️

本软件仅供教育和开发目的使用。使用风险自负。作者不对因使用本软件而产生的任何财务损失负责。在用于真实资金交易之前，务必使用模拟交易进行测试。

## 🚀 功能特性

-   **账户管理**: 获取持仓、投资组合详情和账户概览
-   **市场数据**: 检索历史价格数据和实时市场信息
-   **交易操作**: 下达订单、管理持仓和跟踪执行情况
-   **MCP 集成**: 与支持 MCP 协议的 AI 模型无缝集成
-   **一次性 CLI**: 按命令连接-执行-断开，适合脚本或临时查询
-   **TWS 自动启动 (macOS)**: 一条命令启动 TWS 并自动填入 TOTP 2FA 验证码
-   **Claude Code Skill**: 通过自带的 `skills/ibkr-trading` 用自然语言交易
-   **安全特性**: 只读模式、可配置的交易限制和全面的验证
-   **高可用性**: 自动重连、心跳监控和优雅的错误处理

## 📋 先决条件

-   Python 3.10+
-   盈透证券 (Interactive Brokers) TWS 或 IB Gateway
-   活跃的 IBKR 账户（建议使用模拟交易进行测试）

## 🛠️ 安装

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/happy-shine/ibkr_mcp.git
    cd ibkr_mcp
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置 TWS/IB Gateway**:
    -   在 TWS/Gateway 设置中启用 API 连接
    -   设置 Socket 端口（模拟交易默认为 7497，实盘为 7496）
    -   如果需要，配置受信任的 IP 地址

4.  **配置服务器**:
    ```bash
    cp config/config.yaml.example config/config.yaml
    # 根据您的设置编辑 config/config.yaml
    ```

## 🚀 使用方法

### 方式 A: MCP 服务器

```bash
python run.py
```

服务器将：
1.  连接 TWS/IB Gateway
2.  在配置的端口上启动 MCP 服务器
3.  开始心跳监控
4.  记录所有活动

### 方式 B: 一次性 CLI

轻量 CLI，按命令连接后立即断开——适合 shell 脚本或临时查询。

```bash
python cli.py positions
python cli.py summary
python cli.py quote AAPL
python cli.py history AAPL --duration "1 M" --bar "1 day"
python cli.py buy AAPL 10 --type MKT --confirm
python cli.py orders
```

运行 `python cli.py --help` 查看完整命令列表。

> **关于 quote 数据**：若未订阅实时行情，`quote` 会自动回退到历史日线，
> 返回最近一个交易日的 OHLCV（无实时字段）。

### 方式 C: TWS 自动启动（仅限 macOS）

`start_tws.py` 会调用 [IBC](https://github.com/IbcAlpha/IBC) 启动 TWS，
检测到 Second Factor Authentication 对话框后，使用
[pyotp](https://github.com/pyauth/pyotp) 生成 TOTP 码，并通过 AppleScript
(`osascript`) 输入——全程无需手动操作键盘即可完成登录。

```bash
python start_tws.py          # 启动并自动填入 2FA
python start_tws.py --wait   # 同时阻塞，直到 API 端口 7496 就绪
```

**依赖项 (macOS)：**

| 组件 | 用途 | 地址 |
|------|------|------|
| [IBC](https://github.com/IbcAlpha/IBC) | 自动启动 TWS 并注入登录凭据 | https://github.com/IbcAlpha/IBC |
| [pyotp](https://github.com/pyauth/pyotp) | RFC 6238 TOTP 码生成 | https://github.com/pyauth/pyotp |
| `osascript` / AppleScript | macOS 自带；驱动 2FA 对话框 | 系统内置 |

**配置步骤：**

1. 按 IBC 的 macOS 文档安装（通常位于 `~/ibc/`）。
2. 编辑 `~/ibc/config.ini`，设置：
   -   `TradingMode=live`（或 `paper`）
   -   `SecondFactorDevice=Mobile Authenticator`
   -   你的 IBKR 登录凭据
3. 把 IBKR TOTP 密钥（身份验证器二维码中的 Base32 字符串）保存到
   `~/.ibkr-totp-secret`，**或**导出为环境变量 `TOTP_SECRET`。
4. 在 *系统设置 → 隐私与安全性 → 辅助功能* 中，为 Terminal（或你的 Python 启动器）
   授予 **辅助功能** 权限——AppleScript 操作 TWS 窗口必需。

> **平台说明**：`start_tws.py` 依赖 AppleScript/`osascript`，**仅支持 macOS**。
> Linux/Windows 用户可直接使用 IBC，或自行将 GUI 自动化层改为
> `xdotool`（Linux）/ `pywinauto`（Windows）。

### 可用的 MCP 工具

#### 账户工具
-   `get_positions()` - 获取当前账户持仓
-   `get_account_summary()` - 获取账户余额和指标
-   `get_portfolio()` - 获取详细的投资组合信息

#### 市场数据工具
-   `get_historical_data(symbol, duration, bar_size)` - 获取历史价格数据
-   `get_market_data(symbol)` - 获取实时市场数据
-   `get_quote_from_history(symbol)` - 用历史日线替代的报价（无需订阅）
-   `get_contract_details(symbol)` - 获取合约规格
-   `get_option_chain` - 获取期权数据

#### 交易工具
-   `place_order(symbol, action, quantity, order_type, ...)` - 下达买入/卖出订单
-   `get_orders(status)` - 获取订单历史和状态
-   `cancel_order(order_id)` - 取消待处理订单
-   `get_trades()` - 获取执行历史

### AI 交互示例

```
AI: "我目前的持仓是什么？"
→ 调用 get_positions() 工具

AI: "以市价买入 100 股 AAPL"
→ 调用 place_order(symbol="AAPL", action="BUY", quantity=100, order_type="MKT")

AI: "显示 AAPL 过去一周的价格历史"
→ 调用 get_historical_data(symbol="AAPL", duration="1 W", bar_size="1 day")
```

## 🤖 Claude Code Skill

配套的 skill 位于 `skills/ibkr-trading/SKILL.md`，让
[Claude Code](https://claude.com/claude-code) 能通过自然语言直接触发上面的 CLI
命令（例如 *"看我的持仓"*、*"查 AAPL 行情"*）。

软链接到 Claude Code 的 skills 目录即可启用：

```bash
ln -s "$(pwd)/skills/ibkr-trading" ~/.claude/skills/ibkr-trading
```

## 🔗 相关链接与致谢

-   [盈透证券 TWS API](https://interactivebrokers.github.io/tws-api/) — 官方 Python API (`ibapi`)
-   [IBC — Interactive Brokers Controller](https://github.com/IbcAlpha/IBC) — TWS 自动启动器（`start_tws.py` 使用）
-   [pyotp](https://github.com/pyauth/pyotp) — TOTP/HOTP 库（`start_tws.py` 使用）
-   [Model Context Protocol 规范](https://modelcontextprotocol.io/)
-   [FastMCP 框架](https://github.com/jlowin/fastmcp)
-   [Claude Code](https://claude.com/claude-code) — 调用自带 skill 的 AI 结对编程 CLI
