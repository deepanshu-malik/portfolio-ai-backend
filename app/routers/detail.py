"""Detail endpoint for fetching detailed content like code snippets."""

import logging

from fastapi import APIRouter, HTTPException

from app.models import DetailRequest, DetailResponse
from app.services.code_handler import CodeHandler

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
code_handler = CodeHandler()


@router.post("/detail", response_model=DetailResponse)
async def get_detail(detail_request: DetailRequest) -> DetailResponse:
    """
    Fetch detailed content based on action and target.

    Supports:
    - code: Retrieve code snippets with syntax highlighting
    - deepdive: Detailed information about a topic
    - compare: Comparison between two items
    """
    try:
        action = detail_request.action
        target = detail_request.target
        session_id = detail_request.session_id

        logger.info(f"Detail request: {action}/{target} from session {session_id}")

        if action == "code":
            return code_handler.get_code_snippet(target)
        elif action == "deepdive":
            return code_handler.get_deepdive(target)
        elif action == "compare":
            return code_handler.get_comparison(target)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {action}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detail error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch detail: {str(e)}",
        )
