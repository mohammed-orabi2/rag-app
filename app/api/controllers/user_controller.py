from fastapi import APIRouter, HTTPException, Query, status
from app.api.schemas.schema import StandardResponse, UserLogin, UserRegister
from utils.logging_info import get_logger
from app.api.services.user_services import UserService

logger = get_logger()
router = APIRouter()

user_service = UserService()


@router.post("/login", response_model=StandardResponse)
async def login_user(email: str = Query(..., description="Your email")):
    try:
        # Use email from request body
        logger.info(f"Login attempt for email: {email}")
        result = await user_service.get_user_by_email(str(email))

        if result["success"]:
            return StandardResponse(
                success=True,
                message=result.get("message", "User logged in successfully"),
                data={"user": result["user"]["_id"]},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "User not found"),
            )

    except Exception as e:
        logger.error("Error in login endpoint: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/register", response_model=StandardResponse)
async def register_user(
    username: str = Query(..., description="Your username"),
    email: str = Query(..., description="Your email"),
):
    """Register a new user account or return existing user."""
    try:
        # First check if user exists by email
        existing_user = await user_service.get_user_by_email(str(email))

        if existing_user["success"]:
            # User exists, return their ID
            return StandardResponse(
                success=True,
                message="User already exists",
                data={"user_id": existing_user["user"]["_id"]},
            )

        # User doesn't exist, create new user
        user_dict = {
            "username": str(username),
            "email": str(email),
        }
        result = await user_service.create_user(user_dict)
        if result["success"]:
            return StandardResponse(
                success=True,
                message="New user created successfully",
                data={"user_id": result["user"]["_id"]},
            )

    except Exception as e:
        logger.error("Error in register endpoint: %s", e)
        # Instead of raising an error, return a response with success=False
        return StandardResponse(
            success=False,
            message="Error processing request",
            data=None,
        )
