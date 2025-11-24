"""Common data models and base classes."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class PipedriveBaseModel(BaseModel):
    """Base model for all Pipedrive data models."""

    model_config = ConfigDict(
        # Allow population by field name or alias
        populate_by_name=True,
        # Use enum values instead of enum instances
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Allow arbitrary types
        arbitrary_types_allowed=True,
        # Convert datetime to ISO format
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None,
        },
    )


class PaginationInfo(PipedriveBaseModel):
    """Pagination information."""

    start: int = Field(description="Start position")
    limit: int = Field(description="Number of items per page")
    more_items_in_collection: bool = Field(description="Whether there are more items")
    next_start: Optional[int] = Field(None, description="Start position for next page")


T = TypeVar("T")


class PaginatedResponse(PipedriveBaseModel, Generic[T]):
    """Paginated response wrapper."""

    data: List[T] = Field(description="List of items")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination info")
    success: bool = Field(True, description="Whether request was successful")


class Note(PipedriveBaseModel):
    """Note model."""

    id: int = Field(description="Note ID")
    content: str = Field(description="Note content")
    user_id: Optional[int] = Field(None, description="User who created the note")
    deal_id: Optional[int] = Field(None, description="Associated deal ID")
    person_id: Optional[int] = Field(None, description="Associated person ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")


class File(PipedriveBaseModel):
    """File attachment model."""

    id: int = Field(description="File ID")
    name: str = Field(description="File name")
    size: int = Field(description="File size in bytes")
    url: str = Field(description="File download URL")
    file_type: Optional[str] = Field(None, description="MIME type")
    deal_id: Optional[int] = Field(None, description="Associated deal ID")
    person_id: Optional[int] = Field(None, description="Associated person ID")
    org_id: Optional[int] = Field(None, description="Associated organization ID")
    add_time: datetime = Field(description="Upload timestamp")


class CustomFieldValue(PipedriveBaseModel):
    """Custom field value."""

    key: str = Field(description="Custom field key (40-char hash)")
    value: Any = Field(description="Field value")
    label: Optional[str] = Field(None, description="Field label")
