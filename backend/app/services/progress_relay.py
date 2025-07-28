"""
Progress relay service that bridges Redis pub/sub events to WebSocket connections
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ProgressRelayService:
    """Service that subscribes to Redis pub/sub and relays events to WebSocket clients"""
    
    def __init__(self, redis_pool: redis.ConnectionPool):
        self.redis_pool = redis_pool
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._subscriptions: Dict[str, asyncio.Task] = {}
        self.progress_callback: Optional[Callable[[str, dict], asyncio.Coroutine]] = None
    
    async def start(self):
        """Start the progress relay service"""
        if self._running:
            logger.warning("Progress relay service already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._relay_loop())
        logger.info("Progress relay service started")
    
    async def stop(self):
        """Stop the progress relay service"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all subscription tasks
        for task in self._subscriptions.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._subscriptions:
            await asyncio.gather(*self._subscriptions.values(), return_exceptions=True)
        
        # Cancel main task
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self._subscriptions.clear()
        logger.info("Progress relay service stopped")
    
    async def _relay_loop(self):
        """Main relay loop that monitors for new job events"""
        logger.info("Progress relay loop started")
        
        try:
            async with redis.Redis(connection_pool=self.redis_pool) as r:
                # Subscribe to pattern for all job events
                pubsub = r.pubsub()
                await pubsub.psubscribe("jobs:*:events")
                
                logger.info("Subscribed to Redis pattern 'jobs:*:events'")
                
                while self._running:
                    try:
                        # Get message with timeout
                        message = await asyncio.wait_for(
                            pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                            timeout=5.0
                        )
                        
                        if message and message['type'] == 'pmessage':
                            await self._handle_message(message)
                            
                    except asyncio.TimeoutError:
                        # No messages, continue
                        continue
                    except Exception as e:
                        logger.error(f"Error in relay loop: {e}")
                        await asyncio.sleep(1)  # Brief pause before retry
                
                await pubsub.punsubscribe("jobs:*:events")
                
        except asyncio.CancelledError:
            logger.info("Progress relay loop cancelled")
        except Exception as e:
            logger.error(f"Fatal error in relay loop: {e}")
        finally:
            logger.info("Progress relay loop ended")
    
    async def _handle_message(self, message: dict):
        """Handle a Redis pub/sub message"""
        try:
            # Extract job ID from channel name
            # Channel format: jobs:{job_id}:events
            channel = message['channel']  # Already decoded due to decode_responses=True
            parts = channel.split(':')
            if len(parts) >= 3 and parts[0] == 'jobs':
                job_id = parts[1]
                
                # Parse the progress data
                try:
                    progress_data = json.loads(message['data'])  # Already decoded due to decode_responses=True
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in message: {message['data']}")
                    return
                
                # Add metadata
                progress_data['job_id'] = job_id
                
                # Log the event
                logger.debug(f"Relaying progress for job {job_id}: {progress_data}")
                
                # Send to callback if registered
                if self.progress_callback:
                    try:
                        await self.progress_callback(job_id, progress_data)
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def subscribe_to_job(self, job_id: str):
        """Subscribe to events for a specific job (legacy method, kept for compatibility)"""
        # With the pattern subscription, we automatically get all job events
        logger.debug(f"Job {job_id} events will be relayed automatically")
    
    async def unsubscribe_from_job(self, job_id: str):
        """Unsubscribe from events for a specific job (legacy method, kept for compatibility)"""
        # With the pattern subscription, we don't need per-job management
        logger.debug(f"Job {job_id} unsubscribe request (no-op with pattern subscription)") 