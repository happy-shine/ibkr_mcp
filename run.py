#!/usr/bin/env python3
"""
Simple startup script for IBKR MCP Server.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run main
from src.main import main
import asyncio

if __name__ == "__main__":
    print("🚀 Starting IBKR MCP Server...")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
