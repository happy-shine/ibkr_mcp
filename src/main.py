"""
Main entry point for IBKR MCP Server.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.validators import Config
from src.mcp_app import IBKRMCPServer
from src.connection.heartbeat import HeartbeatTask


# Global server instance for signal handling
server_instance = None
heartbeat_task = None

# Load configuration
config_path = project_root / "config" / "config.yaml"
if not config_path.exists():
    print(f"Configuration file not found: {config_path}")
    sys.exit(1)
config = Config.from_yaml(str(config_path))

# Setup logging
logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ibkr_mcp.log')
        ]
    )
logger = logging.getLogger(__name__)
logger.info("Starting IBKR MCP Server...")
logger.info(f"Configuration loaded from: {config_path}")


async def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    
    global server_instance, heartbeat_task
    
    try:
        # Stop heartbeat task
        if heartbeat_task:
            await heartbeat_task.stop()
        
        # Stop server
        if server_instance:
            await server_instance.stop()
        
        logger.info("Shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)



# Setup signal handlers for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    try:
        if heartbeat_task:
            asyncio.run(heartbeat_task.stop())
        if server_instance:
            asyncio.run(server_instance.stop())
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)

def main():
    """Main application entry point."""
    global server_instance, heartbeat_task

    try:
        # Create server instance
        server_instance = IBKRMCPServer(config)

        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, signal_handler)

        # Start the server (this will connect to TWS)
        asyncio.run(server_instance.start())

        # Start heartbeat task
        heartbeat_task = HeartbeatTask(server_instance.connection_manager)
        asyncio.run(heartbeat_task.start())

        logger.info("IBKR MCP Server is running...")
        logger.info("MCP server will run with STDIO transport")
        logger.info("Press Ctrl+C to stop the server")

        # Run the FastMCP server (this will block and handle stdio)
        server_instance.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
