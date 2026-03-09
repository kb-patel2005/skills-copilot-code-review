"""
Endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, EmailStr

from ..database import activities_collection, teachers_collection

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

# ---------------------------
# Data Models
# ---------------------------
class ActivityResponse(BaseModel):
    description: str
    schedule_details: Dict[str, Any]
    max_participants: int
    participants: List[EmailStr]
    current_count: int

class SignupResponse(BaseModel):
    message: str


# ---------------------------
# Routes
# ---------------------------
@router.get("", response_model=Dict[str, ActivityResponse])
@router.get("/", response_model=Dict[str, ActivityResponse])
def get_activities(
    day: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all activities with their details, with optional filtering by day and time.

    - day: Filter activities occurring on this day (e.g., 'Monday')
    - start_time: Filter activities starting at or after this time (24-hour format, e.g., '14:30')
    - end_time: Filter activities ending at or before this time (24-hour format, e.g., '17:00')
    """
    query = {}

    if day:
        query["schedule_details.days"] = {"$in": [day]}
    if start_time:
        query["schedule_details.start_time"] = {"$gte": start_time}
    if end_time:
        query["schedule_details.end_time"] = {"$lte": end_time}

    activities: Dict[str, Any] = {}
    for activity in activities_collection.find(query):
        name = activity.pop("_id")
        activity["current_count"] = len(activity.get("participants", []))
        activities[name] = activity

    return activities


@router.get("/days", response_model=List[str])
def get_available_days() -> List[str]:
    """Get a list of all days that have activities scheduled"""
    pipeline = [
        {"$unwind": "$schedule_details.days"},
        {"$group": {"_id": "$schedule_details.days"}},
        {"$sort": {"_id": 1}}
    ]

    days = [day_doc["_id"] for day_doc in activities_collection.aggregate(pipeline)]
    return days


@router.post("/{activity_name}/signup", response_model=SignupResponse)
def signup_for_activity(
    activity_name: str,
    email: EmailStr,
    teacher_username: Optional[str] = Query(None)
):
    """Sign up a student for an activity - requires teacher authentication"""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email in activity.get("participants", []):
        raise HTTPException(status_code=400, detail="Already signed up")

    if len(activity.get("participants", [])) >= activity.get("max_participants", 0):
        raise HTTPException(status_code=400, detail="Activity is full")

    result = activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return SignupResponse(message=f"Signed up {email} for {activity_name}")


@router.post("/{activity_name}/unregister", response_model=SignupResponse)
def unregister_from_activity(
    activity_name: str,
    email: EmailStr,
    teacher_username: Optional[str] = Query(None)
):
    """Remove a student from an activity - requires teacher authentication"""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email not in activity.get("participants", []):
        raise HTTPException(status_code=400, detail="Not registered for this activity")

    result = activities_collection.update_one(
        {"_id": activity_name},
        {"$pull": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return SignupResponse(message=f"Unregistered {email} from {activity_name}")
