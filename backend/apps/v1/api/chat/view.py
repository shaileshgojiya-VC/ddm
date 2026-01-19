"""
Chat REST API Views.

Note: Socket.IO/WebSocket functionality has been migrated to socket-service/.
This file contains only REST API endpoints for chat operations.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.chat.schema import CreateGroupRequest
from apps.v1.api.chat.services.create_group_service import CreateGroupService
from apps.v1.api.chat.services.get_group_service import GetGroupService
from apps.v1.api.chat.services.update_group_service import UpdateGroupService
from apps.v1.api.chat.services.get_chat_history_service import GetChatHistoryService
from apps.v1.api.chat.services.get_user_chats_service import GetUserChatsService
from config.db_config import get_async_db
from core.utils import constant_variable
from core.utils.auth_dependencies import get_current_user, security

logger = logging.getLogger(__name__)

router = APIRouter(prefix=constant_variable.API_V1_PREFIX, tags=["Chat API"])


"""
Chat REST API endpoints.
"""

@router.post("/chat/groups")
async def create_group(
    body: CreateGroupRequest = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new message group.
    
    Args:
        body: CreateGroupRequest containing group_name and members list
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with created group data
    """
    try:
        logger.info("Starting create group endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to create group
        create_group_service = CreateGroupService()
        return await create_group_service.create_group(
            db=db,
            body=body,
            current_user=current_user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in create_group endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/groups/{group_uuid}")
async def get_group(
    group_uuid: str,
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a specific group by UUID.
    
    Args:
        group_uuid: UUID of the group to retrieve
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with group data
    """
    try:
        logger.info(f"Starting get group endpoint for UUID: {group_uuid}")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to get group
        get_group_service = GetGroupService()
        return await get_group_service.get_group(
            db=db,
            group_uuid=group_uuid,
            current_user=current_user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_group endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/groups")
async def list_groups(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: str = Query(None, description="Search by group name"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List groups that the current user is a member of.
    
    Args:
        page: Page number for pagination
        limit: Number of items per page
        search: Search term for group name
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with paginated list of groups
    """
    try:
        logger.info("Starting list groups endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to list groups
        get_group_service = GetGroupService()
        return await get_group_service.list_groups(
            db=db,
            current_user=current_user,
            page=page,
            limit=limit,
            search=search,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in list_groups endpoint: {exc}", exc_info=True)
        raise


@router.put("/chat/groups/{group_uuid}")
async def update_group(
    group_uuid: str,
    body: dict = Body(...),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update a message group (name and/or members).
    
    Args:
        group_uuid: UUID of the group to update
        body: UpdateGroupRequest containing group_name and/or members
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with updated group data
    """
    try:
        logger.info(f"Starting update group endpoint for UUID: {group_uuid}")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Parse body into UpdateGroupRequest
        from apps.v1.api.chat.schema import UpdateGroupRequest
        update_body = UpdateGroupRequest(**body)
        
        # Call service to update group
        update_group_service = UpdateGroupService()
        return await update_group_service.update_group(
            db=db,
            group_uuid=group_uuid,
            body=update_body,
            current_user=current_user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in update_group endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/user/chats")
async def get_user_chats(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all chats (1:1 and group) for the authenticated user.
    
    Args:
        page: Page number for pagination
        limit: Number of items per page
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with paginated chat list
    """
    try:
        logger.info("Starting get user chats endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to get user chats
        get_user_chats_service = GetUserChatsService()
        return await get_user_chats_service.get_user_chats(
            db=db,
            current_user=current_user,
            page=page,
            limit=limit,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_user_chats endpoint: {exc}", exc_info=True)
        raise


@router.get("/chat/history")
async def get_chat_history(
    room_id: str = Query(None, description="Room UUID (for one-on-one or group chats)"),
    group_id: str = Query(None, description="Group UUID (alternative to room_id for group chats)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Number of items per page"),
    authorize: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get chat history for a room or group.
    
    Args:
        room_id: Room UUID (for one-on-one or group chats)
        group_id: Group UUID (alternative to room_id for group chats)
        page: Page number for pagination
        limit: Number of items per page
        authorize: HTTPAuthorizationCredentials for token authorization
        db: Database session
        
    Returns:
        StandardResponse with paginated chat history
    """
    try:
        logger.info("Starting get chat history endpoint")
        
        # Get current authenticated user
        current_user = await get_current_user(authorize, db)
        logger.info(f"Current user authenticated: {current_user.email}, ID: {current_user.id}")
        
        # Call service to get chat history
        get_chat_history_service = GetChatHistoryService()
        return await get_chat_history_service.get_chat_history(
            db=db,
            current_user=current_user,
            room_id=room_id,
            group_id=group_id,
            page=page,
            limit=limit,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in get_chat_history endpoint: {exc}", exc_info=True)
        raise

