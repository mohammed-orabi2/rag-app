from fastapi import APIRouter
from app.api.schemas.schema import StandardResponse

router = APIRouter()


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """Health check endpoint."""
    return StandardResponse(
        success=True, message="Service is healthy", data={"status": "OK"}
    )
