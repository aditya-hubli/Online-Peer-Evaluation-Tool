"""Authentication routes - login, register, etc."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.db import get_db
from app.core.supabase import supabase
from app.core.config import settings
from app.core.password_validator import validate_password_strength
from app.core.jwt_handler import create_access_token
# OPETSE-30: Import session management
from app.core.session_timeout import create_session, destroy_session

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str  # Changed from int to str to support UUID
    email: str
    name: str
    role: str
    message: str


class LoginResponse(BaseModel):
    user: dict
    message: str
    access_token: str
    token_type: str = "bearer"
    # OPETSE-30: Session timeout information
    session_timeout_minutes: int


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user with password strength validation (OPETSE-28)."""
    try:
        # OPETSE-28: Validate password strength
        if settings.STRONG_PASSWORD_REQUIRED:
            is_valid, message = validate_password_strength(user_data.password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password requirements not met: {message}"
                )

        # Check if user already exists
        existing = supabase.table("users").select("*").eq("email", user_data.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Create user in database
        # TODO: Hash the password with bcrypt before storing
        new_user = {
            "email": user_data.email,
            "password_hash": user_data.password,  # TODO: Hash this!
            "name": user_data.name,
            "role": user_data.role
        }

        result = supabase.table("users").insert(new_user).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

        created_user = result.data[0]
        return {
            "id": created_user["id"],
            "email": created_user["email"],
            "name": created_user["name"],
            "role": created_user["role"],
            "message": "User registered successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """Login user and return user data."""
    try:
        # Find user by email
        result = supabase.table("users").select("*").eq("email", credentials.email).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        user = result.data[0]

        # Verify password
        # TODO: Use bcrypt to verify hashed password
        # For now, comparing plain text (INSECURE - fix this!)
        if user.get("password_hash") != credentials.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # OPETSE-29: Generate JWT token with user context
        access_token = create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"]
        )

        # OPETSE-30: Create server-side session for timeout tracking
        create_session(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            token=access_token
        )

        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"]
            },
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            # OPETSE-30: Return session timeout information to client
            "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(user_id: str = Query(..., description="User ID for session destruction")):
    """Logout user and destroy server-side session (OPETSE-30)."""
    try:
        # OPETSE-30: Destroy the user's session
        destroyed = destroy_session(user_id)
        
        if not destroyed:
            # Session didn't exist, but logout still succeeds
            return {
                "message": "Logout successful (session was already inactive)",
                "session_destroyed": False
            }
        
        return {
            "message": "Logout successful and session destroyed",
            "session_destroyed": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(user_id: str):
    """Get current authenticated user by ID."""
    # TODO: Replace user_id parameter with JWT token verification
    # This should extract user_id from the JWT token, not accept it as a parameter
    # Example:
    # def get_current_user(token: str = Depends(oauth2_scheme)):
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #     user_id = payload.get("sub")

    try:
        result = supabase.table("users").select("id, email, name, role, created_at").eq("id", user_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user = result.data[0]
        return {
            "user": user,
            "message": "User retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )
