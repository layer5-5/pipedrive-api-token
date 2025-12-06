"""User data models."""

from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr

from .common import PipedriveBaseModel


class UserRole(PipedriveBaseModel):
    """User role."""

    id: int = Field(description="Role ID")
    name: str = Field(description="Role name")
    level: Optional[int] = Field(None, description="Permission level")


class User(PipedriveBaseModel):
    """User/Team member."""

    id: int = Field(description="User ID")
    name: str = Field(description="User name")
    email: str = Field(description="Email address")
    
    # Status
    active_flag: bool = Field(True, description="Whether user is active")
    is_admin: Optional[bool] = Field(None, description="Whether user is admin")
    is_you: Optional[bool] = Field(None, description="Whether this is the current user")
    
    # Role
    role_id: Optional[int] = Field(None, description="Role ID")
    
    # Profile
    phone: Optional[str] = Field(None, description="Phone number")
    icon_url: Optional[str] = Field(None, description="Profile picture URL")
    default_currency: Optional[str] = Field(None, description="Default currency")
    locale: Optional[str] = Field(None, description="Locale")
    timezone_name: Optional[str] = Field(None, description="Timezone")
    timezone_offset: Optional[str] = Field(None, description="Timezone offset")
    
    # Timestamps
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    modified: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Access
    has_created_company: Optional[bool] = Field(None, description="Whether user created company")
    access: Optional[list] = Field(None, description="Access permissions")
    
    # Language
    lang: Optional[int] = Field(None, description="Language ID")
    language: Optional[dict] = Field(None, description="Language info")
