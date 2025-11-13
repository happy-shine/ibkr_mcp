# IBKR MCP 服务器

一个 Model Context Protocol (MCP) 服务器，旨在通过 TWS API 为 AI 模型提供安全访问盈透证券 (IBKR) 的交易数据和功能。

## ⚠️⚠️⚠️ 免责声明 ⚠️⚠️⚠️

本软件仅供教育和开发目的使用。使用风险自负。作者不对因使用本软件而产生的任何财务损失负责。在用于真实资金交易之前，务必使用模拟交易进行测试。

## 🚀 功能特性

-   **账户管理**: 获取持仓、投资组合详情和账户概览
-   **市场数据**: 检索历史价格数据和实时市场信息
-   **交易操作**: 下达订单、管理持仓和跟踪执行情况
-   **MCP 集成**: 与支持 MCP 协议的 AI 模型无缝集成
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

### 启动服务器

```bash
# （使用运行脚本）
python run.py
```

服务器将：
1.  连接 TWS/IB Gateway
2.  在配置的端口上启动 MCP 服务器
3.  开始心跳监控
4.  记录所有活动

### 可用的 MCP 工具

#### 账户工具
-   `get_positions()` - 获取当前账户持仓
-   `get_account_summary()` - 获取账户余额和指标
-   `get_portfolio()` - 获取详细的投资组合信息

#### 市场数据工具
-   `get_historical_data(symbol, duration, bar_size)` - 获取历史价格数据
-   `get_market_data(symbol)` - 获取实时市场数据
-   `get_contract_details(symbol)` - 获取合约规格
- - `get_option_chain` - 获取期权数据

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

## 🔗 相关链接

-   [盈透证券 API 文档](https://interactivebrokers.github.io/tws-api/)
-   [Model Context Protocol 规范](https://modelcontextprotocol.io/)
-   [FastMCP 框架](https://github.com/jlowin/fastmcp)