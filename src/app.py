"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import List
import os
from pathlib import Path

# Initialize web host
app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities"
)

# ---------------------------
# Data Models
# ---------------------------
class Activity(BaseModel):
    description: str
    schedule: str
    max_participants: int
    participants: List[EmailStr]

class ActivityResponse(Activity):
    current_count: int

class SignupResponse(BaseModel):
    message: str

class Student(BaseModel):
    name: str
    grade: int
    email: EmailStr


# ---------------------------
# In-memory databases
# ---------------------------
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}

students = {}  # keyed by email


# ---------------------------
# Mount static frontend
# ---------------------------
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")


# ---------------------------
# Routes
# ---------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities", response_model=dict[str, ActivityResponse])
def get_activities():
    """Get all activities with details and participant count"""
    return {
        name: ActivityResponse(
            description=details["description"],
            schedule=details["schedule"],
            max_participants=details["max_participants"],
            participants=details["participants"],
            current_count=len(details["participants"])
        )
        for name, details in activities.items()
    }


@app.post("/activities/{activity_name}/signup", response_model=SignupResponse)
def signup_for_activity(activity_name: str, email: EmailStr):
    """Sign up a student for an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up")

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    activity["participants"].append(email)
    return SignupResponse(message=f"Signed up {email} for {activity_name}")


# ---------------------------
# Student Endpoints
# ---------------------------
@app.post("/students")
def add_student(student: Student):
    """Register a new student"""
    if student.email in students:
        raise HTTPException(status_code=400, detail="Student already exists")
    students[student.email] = student.dict()
    return {"message": f"Student {student.name} added"}

@app.get("/students/{email}")
def get_student(email: EmailStr):
    """Get student details and enrolled activities"""
    if email not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    enrolled = [name for name, act in activities.items() if email in act["participants"]]
    return {**students[email], "enrolled_activities": enrolled}

@app.get("/students")
def list_students():
    """List all registered students"""
    return students
