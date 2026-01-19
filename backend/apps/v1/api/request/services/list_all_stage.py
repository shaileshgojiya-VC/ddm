"""
Get All Stages Service

Service for retrieving all stages with relationships.
"""

import logging
from typing import Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.v1.api.request.models.methods.method import StageMethod
from apps.v1.api.request.serializer import StageListItemSerializer
from core.utils import constant_variable, message_variable
from core.utils.standard_response import StandardResponse

logger = logging.getLogger(__name__)


class GetAllStageService:
    """
    Service for getting all stages.
    """

    def __init__(self):
        self.stage_method = StageMethod()
        self.stage_serializer = StageListItemSerializer()

    async def get_all_stages(self, db: AsyncSession, phase: Optional[str] = None):
        """
        Get all stages with relationships.

        Args:
            db: Database session
            phase: Optional phase filter (lead, registration, deal)

        Returns:
            StandardResponse with stage list
        """
        try:
            logger.info("STEP 1: Starting get_all_stages service")

            # Get all stages using method with phase filter
            stages = await self.stage_method.get_all_stages(db, phase=phase)

            logger.info(f"STEP 2: Retrieved {len(stages)} stages")

            # Serialize stages directly
            serialized_items = self.stage_serializer.dump(stages, many=True)

            logger.info("STEP 3: Serialized stage items")

            # Build response
            response_data = {
                "items": serialized_items,
                "total": len(stages),
                "total_stages": len(stages),
            }

            logger.info("STEP 4: Get all stages successful")

            return StandardResponse(
                status=constant_variable.STATUS_SUCCESS,
                status_code=status.HTTP_200_OK,
                data=response_data,
                message=message_variable.STAGES_RETRIEVED_SUCCESS
                if hasattr(message_variable, "STAGES_RETRIEVED_SUCCESS")
                else "Stages retrieved successfully",
            ).make

        except Exception as e:
            logger.error(f"Error in get_all_stages: {e}", exc_info=True)
            return StandardResponse(
                status=constant_variable.STATUS_FAIL,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data=constant_variable.STATUS_NULL,
                message=message_variable.SOMETHING_WENT_WRONG,
            ).make
