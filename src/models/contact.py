"""Contact/Person data models."""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import Field, EmailStr

from .common import PipedriveBaseModel, Note, File


class PersonEmail(PipedriveBaseModel):
    """Person email address."""

    label: str = Field(description="Email label (work, home, etc)")
    value: str = Field(description="Email address")
    primary: bool = Field(False, description="Whether this is the primary email")


class PersonPhone(PipedriveBaseModel):
    """Person phone number."""

    label: str = Field(description="Phone label (work, mobile, etc)")
    value: str = Field(description="Phone number")
    primary: bool = Field(False, description="Whether this is the primary phone")


class Person(PipedriveBaseModel):
    """Contact/Person core information."""

    id: int = Field(description="Person ID")
    name: str = Field(description="Person name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")

    # Contact information
    email: Optional[List[PersonEmail]] = Field(None, description="Email addresses")
    phone: Optional[List[PersonPhone]] = Field(None, description="Phone numbers")

    # Organization relationship
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    org_name: Optional[str] = Field(None, description="Organization name")

    # Ownership
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    owner_name: Optional[str] = Field(None, description="Owner name")

    # Job information
    job_title: Optional[str] = Field(None, description="Job title")

    # Timestamps
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    last_activity_date: Optional[date] = Field(None, description="Last activity date")
    next_activity_date: Optional[date] = Field(None, description="Next activity date")

    # Counts
    open_deals_count: Optional[int] = Field(None, description="Number of open deals")
    closed_deals_count: Optional[int] = Field(
        None, description="Number of closed deals"
    )
    won_deals_count: Optional[int] = Field(None, description="Number of won deals")
    lost_deals_count: Optional[int] = Field(None, description="Number of lost deals")
    activities_count: Optional[int] = Field(None, description="Total activities count")
    done_activities_count: Optional[int] = Field(
        None, description="Completed activities"
    )
    undone_activities_count: Optional[int] = Field(
        None, description="Pending activities"
    )
    files_count: Optional[int] = Field(None, description="Number of attached files")
    notes_count: Optional[int] = Field(None, description="Number of notes")
    followers_count: Optional[int] = Field(None, description="Number of followers")
    email_messages_count: Optional[int] = Field(None, description="Number of emails")

    # Contact dates
    first_char: Optional[str] = Field(None, description="First character of name")
    last_incoming_mail_time: Optional[datetime] = Field(
        None, description="Last incoming email"
    )
    last_outgoing_mail_time: Optional[datetime] = Field(
        None, description="Last outgoing email"
    )

    # Flags
    active_flag: bool = Field(True, description="Whether person is active")
    visible_to: Optional[str] = Field(None, description="Visibility level")

    # Marketing
    marketing_status: Optional[str] = Field(None, description="Marketing status")

    # Custom fields
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Custom field values"
    )

    # Picture
    picture_id: Optional[int] = Field(None, description="Picture ID")


class ComprehensivePerson(Person):
    """Person with all related data."""

    # Related entities
    deals: List["Deal"] = Field(default_factory=list, description="All deals")
    activities: List["Activity"] = Field(
        default_factory=list, description="All activities"
    )
    notes: List[Note] = Field(default_factory=list, description="All notes")
    files: List[File] = Field(default_factory=list, description="Attached files")
    followers: List["User"] = Field(default_factory=list, description="Followers")

    # Organization details (if available)
    organization: Optional["Organization"] = Field(
        None, description="Full organization details"
    )

    # Computed metrics
    total_deal_value: Optional[float] = Field(
        None, description="Total value of all deals"
    )
    average_deal_value: Optional[float] = Field(None, description="Average deal value")
    last_contact_days_ago: Optional[int] = Field(
        None, description="Days since last contact"
    )
    engagement_score: Optional[float] = Field(
        None, description="Engagement score (0-100)"
    )


class PersonFilter(PipedriveBaseModel):
    """Filter parameters for person queries."""

    org_id: Optional[int] = Field(None, description="Filter by organization")
    owner_id: Optional[int] = Field(None, description="Filter by owner")
    first_char: Optional[str] = Field(None, description="Filter by first character")
    limit: int = Field(100, description="Number of results", ge=1, le=500)
    start: int = Field(0, description="Pagination start", ge=0)
    sort: Optional[str] = Field(None, description="Sort field")


class PersonCreateRequest(PipedriveBaseModel):
    """Request model for creating a person."""

    name: str = Field(description="Person name")
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    org_id: Optional[int] = Field(None, description="Organization ID")
    email: Optional[List[str]] = Field(None, description="Email addresses")
    phone: Optional[List[str]] = Field(None, description="Phone numbers")
    job_title: Optional[str] = Field(None, description="Job title")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    marketing_status: Optional[str] = Field(None, description="Marketing status")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")


class PersonUpdateRequest(PipedriveBaseModel):
    """Request model for updating a person."""

    name: Optional[str] = Field(None, description="Person name")
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    org_id: Optional[int] = Field(None, description="Organization ID")
    email: Optional[List[str]] = Field(None, description="Email addresses")
    phone: Optional[List[str]] = Field(None, description="Phone numbers")
    job_title: Optional[str] = Field(None, description="Job title")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    marketing_status: Optional[str] = Field(None, description="Marketing status")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")


# Forward references
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .deal import Deal
    from .activity import Activity
    from .company import Organization
    from .user import User
