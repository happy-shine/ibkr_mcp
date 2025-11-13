"""
Configuration validators using Pydantic for type safety and validation.
"""
import os
import yaml
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class IBKRSettings(BaseModel):
    """Interactive Brokers TWS connection settings."""
    client_id: int = Field(default=1, description="TWS client ID")
    host: str = Field(default="127.0.0.1", description="TWS host address")
    port: int = Field(default=7497, description="TWS port (7497 for paper, 7496 for live)")
    read_only: bool = Field(default=False, description="Enable read-only mode (no trading)")
    allow_short_selling: bool = Field(default=True, description="Allow short selling")
    order_types: List[str] = Field(
        default=["LMT", "MKT"], 
        description="Allowed order types"
    )
    tif_types: List[str] = Field(
        default=["DAY", "GTC"], 
        description="Allowed time-in-force types"
    )

    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v

    @field_validator('order_types')
    @classmethod
    def validate_order_types(cls, v):
        valid_types = ["LMT", "MKT", "STP", "STP LMT", "TRAIL", "TRAIL LIMIT"]
        for order_type in v:
            if order_type not in valid_types:
                raise ValueError(f'Invalid order type: {order_type}')
        return v

    @field_validator('tif_types')
    @classmethod
    def validate_tif_types(cls, v):
        valid_tifs = ["DAY", "GTC", "IOC", "FOK", "GTD"]
        for tif in v:
            if tif not in valid_tifs:
                raise ValueError(f'Invalid TIF type: {tif}')
        return v


class MCPSettings(BaseModel):
    """MCP server settings."""
    host: str = Field(default="127.0.0.1", description="MCP server host")
    port: int = Field(default=8000, description="MCP server port")
    title: str = Field(default="IBKR MCP Server", description="Server title")
    description: str = Field(
        default="AI interface for Interactive Brokers data and trading",
        description="Server description"
    )

    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v


class ConnectionSettings(BaseModel):
    """Connection management settings."""
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    reconnect_attempts: int = Field(default=3, description="Number of reconnection attempts")
    reconnect_delay: int = Field(default=5, description="Delay between reconnection attempts")

    @field_validator('heartbeat_interval')
    @classmethod
    def validate_heartbeat_interval(cls, v):
        if v < 10:
            raise ValueError('Heartbeat interval must be at least 10 seconds')
        return v


class LoggingSettings(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )

    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid logging level: {v}')
        return v.upper()


class Config(BaseModel):
    """Main configuration model."""
    ibkr: IBKRSettings
    mcp: MCPSettings
    connection: ConnectionSettings = ConnectionSettings()
    logging: LoggingSettings = LoggingSettings()

    @classmethod
    def from_yaml(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        return cls(
            ibkr=IBKRSettings(
                client_id=int(os.getenv('IBKR_CLIENT_ID', 1)),
                host=os.getenv('IBKR_HOST', '127.0.0.1'),
                port=int(os.getenv('IBKR_PORT', 7497)),
                read_only=os.getenv('IBKR_READ_ONLY', 'false').lower() == 'true',
                allow_short_selling=os.getenv('IBKR_ALLOW_SHORT', 'true').lower() == 'true'
            ),
            mcp=MCPSettings(
                host=os.getenv('MCP_HOST', '127.0.0.1'),
                port=int(os.getenv('MCP_PORT', 8000))
            )
        )
