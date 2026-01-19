"""
Receipt handler for read receipt events.
"""

import logging
from typing import Dict, Any
from models.schemas import ReadReceiptEvent, ErrorResponse, MessageResponse
from connection_manager import connection_manager
from services.persistence_service import PersistenceService
from services.pubsub_service import pubsub_service
from utils.constants import (
    EVENT_READ_RECEIPT,
    EVENT_READ_RECEIPT_RESPONSE,
    STATUS_SUCCESS,
    STATUS_ERROR,
    ROOM_PREFIX,
)

logger = logging.getLogger(__name__)
persistence_service = PersistenceService()


async def handle_read_receipt(sio, sid: str, data: Dict[str, Any]) -> None:
    """
    Handle read receipt event.

    Args:
        sio: Socket.IO server instance
        sid: Socket.IO session ID
        data: Read receipt event data
    """
    logger.info(f"STEP 1: Handling read receipt event from session {sid}")

    try:
        # Validate schema
        try:
            receipt_event = ReadReceiptEvent(**data)
        except Exception as exc:
            logger.error(f"STEP 2: Invalid read receipt schema: {exc}")
            await sio.emit(
                EVENT_READ_RECEIPT_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message=f"Invalid receipt format: {str(exc)}",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        # Get connection info
        connection_info = connection_manager.get_connection_info(sid)
        if not connection_info:
            logger.error(f"STEP 2: Connection not found for session {sid}")
            await sio.emit(
                EVENT_READ_RECEIPT_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Connection not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        user_id = connection_info.get("user_id")

        # Get reader user details if provided, otherwise use connection user
        reader_id = receipt_event.reader_id
        if not reader_id:
            reader_id = user_id

        # Get reader user
        reader_user = await persistence_service.get_user_by_id(reader_id)
        if not reader_user:
            logger.error("STEP 2: Reader user not found")
            await sio.emit(
                EVENT_READ_RECEIPT_RESPONSE,
                ErrorResponse(
                    status=STATUS_ERROR,
                    message="Reader user not found",
                    session_id=sid,
                ).dict(),
                to=sid,
            )
            return

        reader_id_int = reader_user.get("id")

        # Validate reader matches connection (unless admin/system)
        if reader_id_int != user_id:
            logger.warning(
                f"STEP 2: Reader ID {reader_id_int} does not match connection user {user_id}"
            )
            # Allow but log warning

        logger.info("STEP 3: Saving read receipt to database")

        # Get message ID from UUID (we need to query message_chats by UUID)
        import sys
        from pathlib import Path

        backend_path = Path(__file__).parent.parent.parent / "backend"
        sys.path.insert(0, str(backend_path))

        from core.db import SessionLocal
        from apps.v1.api.chat.models.model import message_chats

        db = SessionLocal()
        try:
            message = (
                db.query(message_chats)
                .filter(message_chats.uuid == receipt_event.message_id)
                .first()
            )

            if not message:
                logger.error(f"STEP 3: Message not found: {receipt_event.message_id}")
                await sio.emit(
                    EVENT_READ_RECEIPT_RESPONSE,
                    ErrorResponse(
                        status=STATUS_ERROR,
                        message="Message not found",
                        session_id=sid,
                    ).dict(),
                    to=sid,
                )
                return

            message_id_int = message.id

        finally:
            db.close()

        # Save read receipt
        saved_receipt = await persistence_service.save_read_receipt(
            message_id=message_id_int,
            reader_id=reader_id_int,
            room_id=receipt_event.room_id,
        )

        logger.info("STEP 4: Publishing read receipt to Redis Pub/Sub")

        # Publish to Redis Pub/Sub
        await pubsub_service.publish_receipt(
            room_id=receipt_event.room_id,
            receipt_data=saved_receipt,
        )

        logger.info("STEP 5: Broadcasting read receipt to local connections")

        # Broadcast to local connections in room (excluding sender)
        room_name = connection_manager.format_room_name(receipt_event.room_id)

        await sio.emit(
            EVENT_READ_RECEIPT_RESPONSE,
            MessageResponse(
                status=STATUS_SUCCESS,
                message="Read receipt recorded",
                session_id=sid,
                data=saved_receipt,
            ).dict(),
            room=room_name,
            skip_sid=sid,
        )

        logger.info(
            f"STEP 6: Read receipt handled successfully for message {receipt_event.message_id}"
        )

    except Exception as exc:
        logger.error(f"STEP 6: Error handling read receipt: {exc}", exc_info=True)
        await sio.emit(
            EVENT_READ_RECEIPT_RESPONSE,
            ErrorResponse(
                status=STATUS_ERROR,
                message=f"Error processing read receipt: {str(exc)}",
                session_id=sid,
            ).dict(),
            to=sid,
        )


async def handle_redis_receipt(sio, data: Dict[str, Any]) -> None:
    """
    Handle read receipt received from Redis Pub/Sub.

    Args:
        sio: Socket.IO server instance
        data: Receipt data from Redis
    """
    try:
        room_id = data.get("room_id")
        receipt_data = data.get("data", {})

        if not room_id:
            return

        room_name = connection_manager.format_room_name(room_id)

        # Broadcast to local connections in room
        await sio.emit(
            EVENT_READ_RECEIPT_RESPONSE,
            MessageResponse(
                status=STATUS_SUCCESS,
                message="Read receipt received",
                data=receipt_data,
            ).dict(),
            room=room_name,
        )

    except Exception as exc:
        logger.error(f"Error handling Redis receipt: {exc}", exc_info=True)

