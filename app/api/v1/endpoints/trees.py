"""Tree analysis API endpoints."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.trees import TreeAnalysesListResponse, TreeAnalysisResponse, TreeUsageResponse
from app.services.tree_service import TreeService, TreeServiceError

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 20 * 1024 * 1024


@router.post(
    "/analyze",
    response_model=TreeAnalysisResponse,
    summary="Analyze farm image",
    description="Upload a farm image to analyze tree count, canopy health, and get agronomic recommendations.",
)
async def analyze_image(
    image: UploadFile = File(..., description="Farm image (JPEG/PNG/WEBP, max 20MB)"),
    farmer_id: Annotated[Optional[str], Form()] = None,
    county: Annotated[Optional[str], Form()] = None,
    land_acres: Annotated[Optional[float], Form()] = None,
    location: Annotated[Optional[str], Form()] = None,
    notes: Annotated[Optional[str], Form()] = None,
    current_user: User = Depends(get_current_user),
) -> TreeAnalysisResponse:
    """
    Upload a farm image for tree analysis.

    Analyzes the image using computer vision to count trees, assess canopy health,
    and provides Gemini AI-powered agronomic recommendations.

    Supports JPEG, PNG, and WEBP images up to 20MB. Results are not cached.
    """
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    try:
        image_bytes = await image.read()
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: 20MB",
            )

        service = TreeService()
        result = await service.analyze_image(
            image_bytes,
            image.filename or "image.jpg",
            image.content_type,
            farmer_id,
            county,
            land_acres,
            location,
            notes,
        )
        return TreeAnalysisResponse(**result)
    except TreeServiceError as e:
        logger.error(f"Tree service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analyze endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/analyses",
    response_model=TreeAnalysesListResponse,
    summary="List past analyses",
    description="Get paginated list of past tree analyses.",
)
async def list_analyses(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[Optional[str], Query(description="Pagination cursor")] = None,
    current_user: User = Depends(get_current_user),
) -> TreeAnalysesListResponse:
    """
    List past tree analyses for the authenticated user.

    Results are cached for 5 minutes. Returns paginated results ordered by newest first.
    """
    try:
        service = TreeService()
        data = await service.list_analyses(limit, cursor)
        return TreeAnalysesListResponse(**data)
    except TreeServiceError as e:
        logger.error(f"Tree service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in list_analyses endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/usage",
    response_model=TreeUsageResponse,
    summary="Get tree analysis usage",
    description="Get monthly usage and quota for tree analyses.",
)
async def get_usage(
    current_user: User = Depends(get_current_user),
) -> TreeUsageResponse:
    """
    Get tree analysis usage and quota for current plan.

    Results are cached for 5 minutes. Shows how many analyses have been used
    and how many remain in the current billing period.
    """
    try:
        service = TreeService()
        data = await service.get_usage()
        return TreeUsageResponse(**data)
    except TreeServiceError as e:
        logger.error(f"Tree service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in usage endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
