"""
Redis Pub/Sub service for horizontal scaling.
"""

import json
import logging
import sys
import asyncio
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import redis.asyncio as aioredis
from config.redis_config import redis_client
from config.env_config import get_settings
from utils.constants import (
    REDIS_CHANNEL_ROOM_PREFIX,
    REDIS_CHANNEL_USER_PREFIX,
    REDIS_CHANNEL_RECEIPT_PREFIX,
    REDIS_CHANNEL_PRESENCE_PREFIX,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class PubSubService:
    """Redis Pub/Sub service for message broadcasting across instances."""

    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.subscribed_channels: set = set()
        self.message_handlers: Dict[str, Callable] = {}

    async def initialize(self) -> None:
        """
        Initialize Redis async client and Pub/Sub.
        """
        logger.info("STEP 1: Initializing Redis Pub/Sub service")

        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                decode_responses=True,
            )
            self.pubsub = self.redis_client.pubsub()

            logger.info("STEP 2: Redis Pub/Sub service initialized successfully")

        except Exception as exc:
            logger.error(f"STEP 2: Error initializing Redis Pub/Sub: {exc}", exc_info=True)
            raise

    async def close(self) -> None:
        """
        Close Redis connections.
        """
        logger.info("STEP 1: Closing Redis Pub/Sub connections")

        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("STEP 2: Redis Pub/Sub connections closed")

    async def publish_to_room(
        self, room_id: str, event_type: str, data: Dict[str, Any]
    ) -> None:
        """
        Publish message to a room channel.

        Args:
            room_id: Room UUID
            event_type: Event type (e.g., "message", "read_receipt")
            data: Event data
        """
        try:
            channel = f"{REDIS_CHANNEL_ROOM_PREFIX}{room_id}"
            message = {
                "event_type": event_type,
                "room_id": room_id,
                "data": data,
            }

            if self.redis_client:
                await self.redis_client.publish(channel, json.dumps(message))
                logger.info(f"STEP 1: Published {event_type} to room {room_id}")
            else:
                logger.warning("Redis client not initialized")

        except Exception as exc:
            logger.error(
                f"STEP 1: Error publishing to room {room_id}: {exc}", exc_info=True
            )

    async def publish_to_user(
        self, user_id: int, event_type: str, data: Dict[str, Any]
    ) -> None:
        """
        Publish message to a user channel.

        Args:
            user_id: User ID
            event_type: Event type (e.g., "presence", "notification")
            data: Event data
        """
        try:
            channel = f"{REDIS_CHANNEL_USER_PREFIX}{user_id}"
            message = {
                "event_type": event_type,
                "user_id": user_id,
                "data": data,
            }

            if self.redis_client:
                await self.redis_client.publish(channel, json.dumps(message))
                logger.info(f"STEP 1: Published {event_type} to user {user_id}")
            else:
                logger.warning("Redis client not initialized")

        except Exception as exc:
            logger.error(
                f"STEP 1: Error publishing to user {user_id}: {exc}", exc_info=True
            )

    async def publish_receipt(
        self, room_id: str, receipt_data: Dict[str, Any]
    ) -> None:
        """
        Publish read receipt to a room channel.

        Args:
            room_id: Room UUID
            receipt_data: Receipt data
        """
        try:
            channel = f"{REDIS_CHANNEL_RECEIPT_PREFIX}{room_id}"
            message = {
                "event_type": "read_receipt",
                "room_id": room_id,
                "data": receipt_data,
            }

            if self.redis_client:
                await self.redis_client.publish(channel, json.dumps(message))
                logger.info(f"STEP 1: Published read receipt to room {room_id}")
            else:
                logger.warning("Redis client not initialized")

        except Exception as exc:
            logger.error(
                f"STEP 1: Error publishing receipt to room {room_id}: {exc}",
                exc_info=True,
            )

    async def subscribe_to_room(
        self, room_id: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to a room channel.

        Args:
            room_id: Room UUID
            handler: Handler function for received messages
        """
        try:
            channel = f"{REDIS_CHANNEL_ROOM_PREFIX}{room_id}"

            if channel in self.subscribed_channels:
                logger.info(f"Already subscribed to room {room_id}")
                return

            if not self.pubsub:
                await self.initialize()

            await self.pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
            self.message_handlers[channel] = handler

            logger.info(f"STEP 1: Subscribed to room {room_id}")

            # Start listening task
            asyncio.create_task(self._listen_to_channel(channel))

        except Exception as exc:
            logger.error(
                f"STEP 1: Error subscribing to room {room_id}: {exc}", exc_info=True
            )

    async def unsubscribe_from_room(self, room_id: str) -> None:
        """
        Unsubscribe from a room channel.

        Args:
            room_id: Room UUID
        """
        try:
            channel = f"{REDIS_CHANNEL_ROOM_PREFIX}{room_id}"

            if channel not in self.subscribed_channels:
                return

            if self.pubsub:
                await self.pubsub.unsubscribe(channel)
                self.subscribed_channels.discard(channel)
                self.message_handlers.pop(channel, None)

                logger.info(f"STEP 1: Unsubscribed from room {room_id}")

        except Exception as exc:
            logger.error(
                f"STEP 1: Error unsubscribing from room {room_id}: {exc}",
                exc_info=True,
            )

    async def _listen_to_channel(self, channel: str) -> None:
        """
        Listen to messages on a channel and call handler.

        Args:
            channel: Channel name
        """
        try:
            handler = self.message_handlers.get(channel)

            if not handler:
                logger.warning(f"No handler registered for channel {channel}")
                return

            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await handler(data)
                    except json.JSONDecodeError as exc:
                        logger.error(
                            f"Error decoding message from channel {channel}: {exc}"
                        )
                    except Exception as exc:
                        logger.error(
                            f"Error handling message from channel {channel}: {exc}",
                            exc_info=True,
                        )

        except Exception as exc:
            logger.error(
                f"Error listening to channel {channel}: {exc}", exc_info=True
            )


# Global Pub/Sub service instance
pubsub_service = PubSubService()

