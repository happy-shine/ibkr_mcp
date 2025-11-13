"""
Heartbeat task for maintaining TWS connection health.
"""
import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import ConnectionManager

logger = logging.getLogger(__name__)


class HeartbeatTask:
    """Manages heartbeat task for TWS connection."""
    
    def __init__(self, connection_manager: 'ConnectionManager'):
        self.connection_manager = connection_manager
        self.running = False
        self.task: asyncio.Task = None
    
    async def start(self):
        """Start the heartbeat task."""
        if self.running:
            logger.warning("Heartbeat task is already running")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Heartbeat task started")
    
    async def stop(self):
        """Stop the heartbeat task."""
        if not self.running:
            return
            
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat task stopped")
    
    async def _heartbeat_loop(self):
        """Main heartbeat loop."""
        interval = self.connection_manager.connection_config.heartbeat_interval
        
        while self.running:
            try:
                # Perform health check
                if not await self.connection_manager.health_check():
                    logger.warning("Health check failed, attempting reconnection...")
                    await self.connection_manager.ensure_connected()
                else:
                    logger.debug("Heartbeat successful")
                
                # Wait for next heartbeat
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat task error: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(interval)


async def heartbeat_task(connection_manager: 'ConnectionManager'):
    """Standalone heartbeat task function for backward compatibility."""
    heartbeat = HeartbeatTask(connection_manager)
    await heartbeat.start()
    
    try:
        # Keep the task running indefinitely
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await heartbeat.stop()
        raise
