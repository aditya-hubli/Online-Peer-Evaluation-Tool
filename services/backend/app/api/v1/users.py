"""User management routes with RBAC."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import List
from app.core.supabase import supabase
from app.core.rbac import require_permission, require_instructor
from app.core.roles import Permission
from app.core.csv_utils import process_students_csv

router = APIRouter(prefix="/users", tags=["users"])


# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    role: str = "student"  # default to student
    password: str = None


class UserUpdate(BaseModel):
    name: str = None
    email: EmailStr = None
    role: str = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str


@router.get("/")
async def list_users():
    """List all users using Supabase. No authentication required for MVP."""
    try:
        response = supabase.table("users").select("*").execute()
        return {
            "success": True,
            "data": response.data,
            "count": len(response.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID using Supabase."""
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return {
            "success": True,
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", dependencies=[Depends(require_instructor)])
async def create_user(user: UserCreate):
    """
    Create a new user using Supabase.
    Only instructors can create users.
    """
    try:
        # Check if email already exists
        existing = supabase.table("users").select("id").eq("email", user.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user data
        user_data = {
            "email": user.email,
            "name": user.name,
            "role": user.role
        }

        # Add password hash if provided (in production, hash this!)
        if user.password:
            user_data["password_hash"] = user.password  # TODO: Hash this with bcrypt

        # Insert into Supabase
        response = supabase.table("users").insert(user_data).execute()

        return {
            "success": True,
            "data": response.data[0] if response.data else None,
            "message": "User created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", dependencies=[Depends(require_permission(Permission.UPDATE_USER))])
async def update_user(user_id: str, user_update: UserUpdate):
    """
    Update a user using Supabase.
    Requires UPDATE_USER permission.
    """
    try:
        update_data = {}
        if user_update.name:
            update_data["name"] = user_update.name
        if user_update.email:
            update_data["email"] = user_update.email
        if user_update.role:
            update_data["role"] = user_update.role

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        response = supabase.table("users").update(update_data).eq("id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return {
            "success": True,
            "data": response.data[0],
            "message": "User updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}", dependencies=[Depends(require_instructor)])
async def delete_user(user_id: str):
    """
    Delete a user using Supabase.
    Only instructors can delete users.
    """
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()

        return {
            "success": True,
            "message": f"User {user_id} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-upload", dependencies=[Depends(require_instructor)])
async def bulk_upload_users(file: UploadFile = File(...)):
    """
    Bulk upload users from CSV file.
    Only instructors can bulk upload users.

    CSV Format:
    - Required headers: email, name
    - Optional headers: role (defaults to 'student')

    Example CSV:
    ```
    email,name,role
    student1@example.com,John Doe,student
    instructor@example.com,Jane Smith,instructor
    ```
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload a CSV file."
            )

        # Read file content
        file_content = await file.read()

        # Process CSV
        is_valid, students, errors = process_students_csv(file_content)

        if not is_valid:
            return {
                "success": False,
                "message": "CSV validation failed",
                "errors": errors,
                "created_count": 0
            }

        # Track results
        created_users = []
        failed_users = []
        skipped_users = []

        # Insert each student
        for student in students:
            try:
                # Check if email already exists
                existing = supabase.table("users").select("id").eq("email", student['email']).execute()

                if existing.data:
                    skipped_users.append({
                        "email": student['email'],
                        "reason": "Email already exists"
                    })
                    continue

                # Insert user
                response = supabase.table("users").insert(student).execute()

                if response.data:
                    created_users.append(response.data[0])
                else:
                    failed_users.append({
                        "email": student['email'],
                        "reason": "Database insert failed"
                    })

            except Exception as e:
                failed_users.append({
                    "email": student['email'],
                    "reason": str(e)
                })

        # Return comprehensive results
        return {
            "success": True,
            "message": f"Bulk upload completed. Created {len(created_users)} users.",
            "summary": {
                "total_in_csv": len(students),
                "created": len(created_users),
                "skipped": len(skipped_users),
                "failed": len(failed_users)
            },
            "created_users": created_users,
            "skipped_users": skipped_users,
            "failed_users": failed_users,
            "validation_errors": errors if errors else []
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")
