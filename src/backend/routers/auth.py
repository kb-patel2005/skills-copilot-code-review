"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# ---------------------------
# Data Models
# ---------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class TeacherResponse(BaseModel):
    username: str
    display_name: str
    role: str


# ---------------------------
# Routes
# ---------------------------
@router.post("/login", response_model=TeacherResponse)
def login(request: LoginRequest) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": request.username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(request.password, teacher.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Return teacher information (excluding password)
    return {
        "username": teacher.get("username", request.username),
        "display_name": teacher.get("display_name", ""),
        "role": teacher.get("role", "teacher")
    }


@router.get("/check-session", response_model=TeacherResponse)
def check_session(username: str) -> Dict[str, Any]:
    """Check if a session is valid by username"""
    teacher = teachers_collection.find_one({"_id": username})

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "username": teacher.get("username", username),
        "display_name": teacher.get("display_name", ""),
        "role": teacher.get("role", "teacher")
    }
