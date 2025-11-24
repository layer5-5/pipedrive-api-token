"""Company/Organization data models."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import Field

from .common import PipedriveBaseModel, Note, File


class Organization(PipedriveBaseModel):
    """Company/Organization core information."""

    id: int = Field(description="Organization ID")
    name: str = Field(description="Organization name")

    # Ownership
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    owner_name: Optional[str] = Field(None, description="Owner name")

    # Company details
    address: Optional[str] = Field(None, description="Company address")
    address_street_number: Optional[str] = Field(None, description="Street number")
    address_route: Optional[str] = Field(None, description="Street name")
    address_subpremise: Optional[str] = Field(None, description="Apartment/Suite")
    address_locality: Optional[str] = Field(None, description="City")
    address_admin_area_level_1: Optional[str] = Field(
        None, description="State/Province"
    )
    address_admin_area_level_2: Optional[str] = Field(None, description="County")
    address_country: Optional[str] = Field(None, description="Country")
    address_postal_code: Optional[str] = Field(None, description="Postal code")

    # Company info
    company_id: Optional[int] = Field(None, description="External company ID")
    people_count: Optional[int] = Field(None, description="Number of people")

    # Timestamps
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    last_activity_date: Optional[date] = Field(None, description="Last activity date")
    next_activity_date: Optional[date] = Field(None, description="Next activity date")

    # Deal counts
    open_deals_count: Optional[int] = Field(None, description="Number of open deals")
    closed_deals_count: Optional[int] = Field(
        None, description="Number of closed deals"
    )
    won_deals_count: Optional[int] = Field(None, description="Number of won deals")
    lost_deals_count: Optional[int] = Field(None, description="Number of lost deals")

    # Activity counts
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

    # Flags
    active_flag: bool = Field(True, description="Whether organization is active")
    visible_to: Optional[str] = Field(None, description="Visibility level")

    # Picture
    picture_id: Optional[int] = Field(None, description="Picture ID")

    # Custom fields
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Custom field values"
    )


class ComprehensiveOrganization(Organization):
    """Organization with all related data."""

    # Related entities
    deals: List["Deal"] = Field(default_factory=list, description="All deals")
    persons: List["Person"] = Field(default_factory=list, description="All contacts")
    activities: List["Activity"] = Field(
        default_factory=list, description="All activities"
    )
    notes: List[Note] = Field(default_factory=list, description="All notes")
    files: List[File] = Field(default_factory=list, description="Attached files")
    followers: List["User"] = Field(default_factory=list, description="Followers")

    # Computed metrics
    total_revenue: Optional[Decimal] = Field(
        None, description="Total revenue from won deals"
    )
    average_deal_value: Optional[Decimal] = Field(
        None, description="Average deal value"
    )
    last_contact_days_ago: Optional[int] = Field(
        None, description="Days since last contact"
    )


class OrganizationFilter(PipedriveBaseModel):
    """Filter parameters for organization queries."""

    owner_id: Optional[int] = Field(None, description="Filter by owner")
    first_char: Optional[str] = Field(None, description="Filter by first character")
    limit: int = Field(100, description="Number of results", ge=1, le=500)
    start: int = Field(0, description="Pagination start", ge=0)
    sort: Optional[str] = Field(None, description="Sort field")


class OrganizationCreateRequest(PipedriveBaseModel):
    """Request model for creating an organization."""

    name: str = Field(description="Organization name")
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    address: Optional[str] = Field(None, description="Address")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")


class OrganizationUpdateRequest(PipedriveBaseModel):
    """Request model for updating an organization."""

    name: Optional[str] = Field(None, description="Organization name")
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    address: Optional[str] = Field(None, description="Address")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")


# Forward references
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .deal import Deal
    from .contact import Person
    from .activity import Activity
    from .user import User
