"""Data models for Pipedrive MCP Server."""

from .common import (
    PipedriveBaseModel,
    PaginationInfo,
    PaginatedResponse,
)
from .deal import (
    Deal,
    DealStatus,
    ComprehensiveDeal,
    DealProduct,
    StageChange,
)
from .contact import (
    Person,
    PersonEmail,
    PersonPhone,
    ComprehensivePerson,
)
from .company import (
    Organization,
    ComprehensiveOrganization,
)
from .activity import (
    Activity,
    ActivityType,
    ActivityParticipant,
)
from .pipeline import (
    Pipeline,
    Stage,
)
from .user import (
    User,
    UserRole,
)
from .product import (
    Product,
    ProductPrice,
)

__all__ = [
    # Common
    "PipedriveBaseModel",
    "PaginationInfo",
    "PaginatedResponse",
    # Deal
    "Deal",
    "DealStatus",
    "ComprehensiveDeal",
    "DealProduct",
    "StageChange",
    # Contact
    "Person",
    "PersonEmail",
    "PersonPhone",
    "ComprehensivePerson",
    # Company
    "Organization",
    "ComprehensiveOrganization",
    # Activity
    "Activity",
    "ActivityType",
    "ActivityParticipant",
    # Pipeline
    "Pipeline",
    "Stage",
    # User
    "User",
    "UserRole",
    # Product
    "Product",
    "ProductPrice",
]
