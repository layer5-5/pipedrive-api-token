"""Deal data models."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import Field

from .common import PipedriveBaseModel, Note, File


class DealStatus(str, Enum):
    """Deal status enum."""

    OPEN = "open"
    WON = "won"
    LOST = "lost"
    DELETED = "deleted"


class DealProduct(PipedriveBaseModel):
    """Product attached to a deal."""

    id: int = Field(description="Deal product ID")
    deal_id: int = Field(description="Deal ID")
    product_id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    item_price: Decimal = Field(description="Unit price")
    quantity: int = Field(description="Quantity")
    discount: Optional[Decimal] = Field(
        None, description="Discount amount or percentage"
    )
    discount_type: Optional[str] = Field(
        None, description="Discount type (percentage/amount)"
    )
    tax: Optional[Decimal] = Field(None, description="Tax percentage")
    sum: Decimal = Field(description="Total sum")
    currency: str = Field(description="Currency code")
    enabled_flag: bool = Field(True, description="Whether product is enabled")
    add_time: Optional[datetime] = Field(None, description="When product was added")
    comments: Optional[str] = Field(None, description="Additional comments")


class StageChange(PipedriveBaseModel):
    """Deal stage change record."""

    id: int = Field(description="Change ID")
    deal_id: int = Field(description="Deal ID")
    stage_id: int = Field(description="Stage ID")
    pipeline_id: int = Field(description="Pipeline ID")
    user_id: Optional[int] = Field(None, description="User who made the change")
    timestamp: datetime = Field(description="When the change occurred")
    duration_in_stage: Optional[int] = Field(
        None, description="Days spent in previous stage"
    )


class Deal(PipedriveBaseModel):
    """Core deal information."""

    id: int = Field(description="Deal ID")
    title: str = Field(description="Deal title")
    value: Optional[Decimal] = Field(None, description="Deal value")
    currency: str = Field(description="Currency code (e.g., USD, EUR)")
    status: DealStatus = Field(description="Deal status")
    stage_id: int = Field(description="Current stage ID")
    pipeline_id: int = Field(description="Pipeline ID")

    # Ownership
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    creator_user_id: Optional[int] = Field(None, description="Creator user ID")

    # Relationships
    person_id: Optional[int] = Field(None, description="Associated person ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    person_name: Optional[str] = Field(None, description="Person name")
    org_name: Optional[str] = Field(None, description="Organization name")

    # Dates
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    stage_change_time: Optional[datetime] = Field(
        None, description="Last stage change timestamp"
    )
    expected_close_date: Optional[date] = Field(None, description="Expected close date")
    close_time: Optional[datetime] = Field(None, description="Actual close timestamp")
    won_time: Optional[datetime] = Field(None, description="When deal was won")
    lost_time: Optional[datetime] = Field(None, description="When deal was lost")
    first_won_time: Optional[datetime] = Field(
        None, description="First time deal was won"
    )

    # Status details
    lost_reason: Optional[str] = Field(None, description="Reason for losing deal")
    probability: Optional[int] = Field(None, description="Win probability percentage")

    # Metrics
    products_count: Optional[int] = Field(None, description="Number of products")
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
    participants_count: Optional[int] = Field(
        None, description="Number of participants"
    )

    # Activity dates
    next_activity_date: Optional[date] = Field(None, description="Next activity date")
    next_activity_time: Optional[str] = Field(None, description="Next activity time")
    next_activity_id: Optional[int] = Field(None, description="Next activity ID")
    last_activity_date: Optional[date] = Field(None, description="Last activity date")
    last_activity_id: Optional[int] = Field(None, description="Last activity ID")
    last_incoming_mail_time: Optional[datetime] = Field(
        None, description="Last incoming email"
    )
    last_outgoing_mail_time: Optional[datetime] = Field(
        None, description="Last outgoing email"
    )

    # Visibility
    visible_to: Optional[str] = Field(None, description="Visibility level")

    # Flags
    active: bool = Field(True, description="Whether deal is active")
    deleted: bool = Field(False, description="Whether deal is deleted")

    # Custom fields (stored as dict)
    custom_fields: Optional[Dict[str, Any]] = Field(
        None, description="Custom field values"
    )


class ComprehensiveDeal(Deal):
    """Deal with all related data."""

    # Related entities
    activities: List["Activity"] = Field(
        default_factory=list, description="All activities"
    )
    notes: List[Note] = Field(default_factory=list, description="All notes")
    products: List[DealProduct] = Field(
        default_factory=list, description="All products"
    )
    participants: List["Person"] = Field(
        default_factory=list, description="All participants"
    )
    stage_history: List[StageChange] = Field(
        default_factory=list, description="Stage change history"
    )
    files: List[File] = Field(default_factory=list, description="Attached files")
    followers: List["User"] = Field(default_factory=list, description="Followers")

    # Computed metrics
    time_in_current_stage_days: Optional[int] = Field(
        None, description="Days in current stage"
    )
    total_stage_changes: int = Field(0, description="Total number of stage changes")
    average_time_per_stage: Optional[float] = Field(
        None, description="Average days per stage"
    )
    total_product_value: Optional[Decimal] = Field(
        None, description="Sum of all product values"
    )

    # Owner details (if available)
    owner_name: Optional[str] = Field(None, description="Owner user name")
    owner_email: Optional[str] = Field(None, description="Owner user email")


class DealFilter(PipedriveBaseModel):
    """Filter parameters for deal queries."""

    status: Optional[DealStatus] = Field(None, description="Filter by status")
    pipeline_id: Optional[int] = Field(None, description="Filter by pipeline")
    stage_id: Optional[int] = Field(None, description="Filter by stage")
    owner_id: Optional[int] = Field(None, description="Filter by owner")
    person_id: Optional[int] = Field(None, description="Filter by person")
    org_id: Optional[int] = Field(None, description="Filter by organization")
    date_from: Optional[date] = Field(None, description="Filter by date from")
    date_to: Optional[date] = Field(None, description="Filter by date to")
    limit: int = Field(100, description="Number of results", ge=1, le=500)
    start: int = Field(0, description="Pagination start", ge=0)
    sort: Optional[str] = Field(None, description="Sort field")


class DealCreateRequest(PipedriveBaseModel):
    """Request model for creating a deal."""

    title: str = Field(description="Deal title")
    value: Optional[Decimal] = Field(None, description="Deal value")
    currency: Optional[str] = Field("USD", description="Currency code")
    person_id: Optional[int] = Field(None, description="Associated person ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    stage_id: Optional[int] = Field(None, description="Stage ID")
    status: Optional[DealStatus] = Field(None, description="Deal status")
    expected_close_date: Optional[date] = Field(None, description="Expected close date")
    probability: Optional[int] = Field(None, description="Win probability")
    lost_reason: Optional[str] = Field(None, description="Lost reason")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")


class DealUpdateRequest(PipedriveBaseModel):
    """Request model for updating a deal."""

    title: Optional[str] = Field(None, description="Deal title")
    value: Optional[Decimal] = Field(None, description="Deal value")
    currency: Optional[str] = Field(None, description="Currency code")
    person_id: Optional[int] = Field(None, description="Associated person ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    stage_id: Optional[int] = Field(None, description="Stage ID")
    status: Optional[DealStatus] = Field(None, description="Deal status")
    expected_close_date: Optional[date] = Field(None, description="Expected close date")
    probability: Optional[int] = Field(None, description="Win probability")
    lost_reason: Optional[str] = Field(None, description="Lost reason")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")


# Forward references for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .activity import Activity
    from .contact import Person
    from .user import User
