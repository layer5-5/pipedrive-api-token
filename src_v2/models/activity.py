"""Activity data models."""

from datetime import datetime, date, time
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import Field

from .common import PipedriveBaseModel, File


class ActivityType(str, Enum):
    """Activity type enum."""

    CALL = "call"
    MEETING = "meeting"
    TASK = "task"
    DEADLINE = "deadline"
    EMAIL = "email"
    LUNCH = "lunch"


class ActivityParticipant(PipedriveBaseModel):
    """Activity participant."""

    person_id: int = Field(description="Person ID")
    primary_flag: bool = Field(False, description="Whether this is primary participant")


class Activity(PipedriveBaseModel):
    """Activity core information."""

    id: int = Field(description="Activity ID")
    subject: str = Field(description="Activity subject")
    type: str = Field(description="Activity type")
    
    # Relationships
    deal_id: Optional[int] = Field(None, description="Associated deal ID")
    person_id: Optional[int] = Field(None, description="Associated person ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    user_id: Optional[int] = Field(None, description="Assigned user ID")
    
    # Timing
    due_date: Optional[date] = Field(None, description="Due date")
    due_time: Optional[str] = Field(None, description="Due time")
    duration: Optional[str] = Field(None, description="Duration (HH:MM:SS)")
    
    # Status
    done: bool = Field(False, description="Whether activity is completed")
    marked_as_done_time: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Details
    note: Optional[str] = Field(None, description="Activity notes")
    location: Optional[str] = Field(None, description="Location")
    public_description: Optional[str] = Field(None, description="Public description")
    
    # Participants
    participants: Optional[List[ActivityParticipant]] = Field(None, description="Participants")
    
    # Attendees (for meetings)
    attendees: Optional[List[Dict[str, Any]]] = Field(None, description="Meeting attendees")
    
    # Timestamps
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Files
    files: List[File] = Field(default_factory=list, description="Attached files")
    
    # Flags
    active_flag: bool = Field(True, description="Whether activity is active")
    busy_flag: bool = Field(False, description="Whether user is busy")
    
    # Reference
    reference_type: Optional[str] = Field(None, description="Reference type")
    reference_id: Optional[int] = Field(None, description="Reference ID")
    
    # Organization info
    org_name: Optional[str] = Field(None, description="Organization name")
    person_name: Optional[str] = Field(None, description="Person name")
    deal_title: Optional[str] = Field(None, description="Deal title")


class ActivityFilter(PipedriveBaseModel):
    """Filter parameters for activity queries."""

    deal_id: Optional[int] = Field(None, description="Filter by deal")
    person_id: Optional[int] = Field(None, description="Filter by person")
    org_id: Optional[int] = Field(None, description="Filter by organization")
    user_id: Optional[int] = Field(None, description="Filter by user")
    type: Optional[str] = Field(None, description="Filter by type")
    done: Optional[bool] = Field(None, description="Filter by completion status")
    start_date: Optional[date] = Field(None, description="Filter by start date")
    end_date: Optional[date] = Field(None, description="Filter by end date")
    limit: int = Field(100, description="Number of results", ge=1, le=500)
    start: int = Field(0, description="Pagination start", ge=0)


class ActivityCreateRequest(PipedriveBaseModel):
    """Request model for creating an activity."""

    subject: str = Field(description="Activity subject")
    type: str = Field(description="Activity type")
    due_date: Optional[date] = Field(None, description="Due date")
    due_time: Optional[str] = Field(None, description="Due time")
    duration: Optional[str] = Field(None, description="Duration")
    deal_id: Optional[int] = Field(None, description="Deal ID")
    person_id: Optional[int] = Field(None, description="Person ID")
    org_id: Optional[int] = Field(None, description="Organization ID")
    note: Optional[str] = Field(None, description="Notes")
    location: Optional[str] = Field(None, description="Location")
    public_description: Optional[str] = Field(None, description="Public description")
    participants: Optional[List[int]] = Field(None, description="Participant person IDs")
    busy_flag: Optional[bool] = Field(None, description="Busy flag")
    attendees: Optional[List[Dict[str, Any]]] = Field(None, description="Attendees")


class ActivityUpdateRequest(PipedriveBaseModel):
    """Request model for updating an activity."""

    subject: Optional[str] = Field(None, description="Activity subject")
    type: Optional[str] = Field(None, description="Activity type")
    due_date: Optional[date] = Field(None, description="Due date")
    due_time: Optional[str] = Field(None, description="Due time")
    duration: Optional[str] = Field(None, description="Duration")
    deal_id: Optional[int] = Field(None, description="Deal ID")
    person_id: Optional[int] = Field(None, description="Person ID")
    org_id: Optional[int] = Field(None, description="Organization ID")
    note: Optional[str] = Field(None, description="Notes")
    location: Optional[str] = Field(None, description="Location")
    public_description: Optional[str] = Field(None, description="Public description")
    done: Optional[bool] = Field(None, description="Completion status")
    participants: Optional[List[int]] = Field(None, description="Participant person IDs")
    busy_flag: Optional[bool] = Field(None, description="Busy flag")
    attendees: Optional[List[Dict[str, Any]]] = Field(None, description="Attendees")
