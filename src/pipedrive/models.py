"""
Enhanced data models for Pipedrive MCP with business intelligence fields.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class DealStatus(str, Enum):
    """Deal status enumeration"""

    OPEN = "open"
    WON = "won"
    LOST = "lost"
    DELETED = "deleted"
    ALL_NOT_DELETED = "all_not_deleted"


class ActivityType(str, Enum):
    """Activity type enumeration"""

    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    TASK = "task"
    NOTE = "note"
    DEADLINE = "deadline"
    LUNCH = "lunch"


class CompanySize(str, Enum):
    """Company size categorization"""

    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


@dataclass
class DealProduct:
    """Product associated with a deal"""

    id: int
    name: str
    code: Optional[str] = None
    unit_price: float = 0.0
    quantity: int = 1
    discount: float = 0.0
    total: float = 0.0
    currency: str = "USD"
    product_id: Optional[int] = None
    deal_id: Optional[int] = None

    def __post_init__(self):
        """Calculate total if not provided"""
        if self.total == 0.0 and self.unit_price > 0:
            self.total = (self.unit_price * self.quantity) - self.discount


@dataclass
class StageChange:
    """Deal stage movement history"""

    id: int
    deal_id: int
    from_stage_id: Optional[int]
    to_stage_id: int
    from_stage_name: Optional[str] = None
    to_stage_name: Optional[str] = None
    changed_by_user_id: Optional[int] = None
    changed_by_user_name: Optional[str] = None
    change_date: datetime = field(default_factory=datetime.now)
    time_in_previous_stage: Optional[int] = None  # hours
    notes: Optional[str] = None


@dataclass
class EnhancedDeal:
    """Enhanced deal model with business intelligence fields"""

    id: int
    title: str
    value: float = 0.0
    currency: str = "USD"
    status: DealStatus = DealStatus.OPEN
    stage_id: Optional[int] = None
    stage_name: Optional[str] = None
    pipeline_id: Optional[int] = None
    pipeline_name: Optional[str] = None

    # Enhanced business fields
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    lost_reason: Optional[str] = None
    probability: Optional[int] = None  # 0-100
    lead_source: Optional[str] = None
    next_activity_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None

    # Relationship fields
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    org_id: Optional[int] = None
    org_name: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None

    # Analytics fields
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    time_in_current_stage: Optional[int] = None  # hours
    total_time_in_stages: Optional[int] = None  # hours
    stage_changes: List[StageChange] = field(default_factory=list)
    products: List[DealProduct] = field(default_factory=list)

    # Additional fields
    notes_count: int = 0
    activities_count: int = 0
    products_count: int = 0
    weighted_value: float = 0.0  # value * probability

    def __post_init__(self):
        """Calculate derived fields"""
        if self.probability is not None:
            self.weighted_value = self.value * (self.probability / 100)

        self.products_count = len(self.products)

    def calculate_time_in_stages(self) -> Dict[str, int]:
        """Calculate time spent in each stage"""
        stage_times = {}

        if not self.stage_changes:
            return stage_times

        # Sort stage changes by date
        sorted_changes = sorted(self.stage_changes, key=lambda x: x.change_date)

        # Calculate time in each stage
        for i, change in enumerate(sorted_changes):
            stage_name = change.to_stage_name or f"Stage_{change.to_stage_id}"

            if i < len(sorted_changes) - 1:
                # Time until next change
                next_change = sorted_changes[i + 1]
                time_hours = (
                    next_change.change_date - change.change_date
                ).total_seconds() / 3600
            else:
                # Time until now or deal close
                end_date = self.actual_close_date or datetime.now()
                time_hours = (end_date - change.change_date).total_seconds() / 3600

            stage_times[stage_name] = int(time_hours)

        return stage_times

    def get_current_stage_duration(self) -> Optional[int]:
        """Get time in current stage in hours"""
        if not self.stage_changes:
            return None

        # Find the most recent stage change
        latest_change = max(self.stage_changes, key=lambda x: x.change_date)

        # Calculate time since latest change
        end_date = self.actual_close_date or datetime.now()
        time_hours = (end_date - latest_change.change_date).total_seconds() / 3600

        return int(time_hours)


@dataclass
class EnhancedPerson:
    """Enhanced person/contact model with business intelligence"""

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    # Enhanced business fields
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    org_id: Optional[int] = None
    lead_score: Optional[int] = None  # 0-100
    lead_source: Optional[str] = None
    last_contacted_date: Optional[datetime] = None
    next_activity_date: Optional[datetime] = None

    # Analytics fields
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)

    # Deal relationship counts
    total_deals: int = 0
    active_deals: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    total_deal_value: float = 0.0

    # Activity metrics
    activities_count: int = 0
    notes_count: int = 0
    emails_count: int = 0
    calls_count: int = 0

    # Owner
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None


@dataclass
class EnhancedOrganization:
    """Enhanced organization model with business intelligence"""

    id: int
    name: str

    # Enhanced business fields
    industry: Optional[str] = None
    size: Optional[CompanySize] = None
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None

    # Analytics fields
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)

    # Deal relationship counts
    total_deals: int = 0
    active_deals: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    total_deal_value: float = 0.0
    average_deal_size: float = 0.0

    # Contact metrics
    contacts_count: int = 0
    active_contacts: int = 0

    # Owner
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None

    def calculate_average_deal_size(self):
        """Calculate average deal size"""
        if self.total_deals > 0:
            self.average_deal_size = self.total_deal_value / self.total_deals


@dataclass
class EnhancedActivity:
    """Enhanced activity model with rich details"""

    id: int
    subject: str
    type: ActivityType
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None

    # Enhanced fields
    duration: Optional[int] = None  # minutes
    outcome: Optional[str] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    conference_call_url: Optional[str] = None

    # Relationship fields
    deal_id: Optional[int] = None
    deal_title: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    org_id: Optional[int] = None
    org_name: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None

    # Status and completion
    done: bool = False
    completed_date: Optional[datetime] = None
    completion_note: Optional[str] = None

    # Participants and attachments
    participants: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_tasks: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    notes_count: int = 0


@dataclass
class EnhancedUser:
    """Enhanced user model with performance tracking"""

    id: int
    name: str
    email: str

    # Enhanced fields
    role: Optional[str] = None
    department: Optional[str] = None
    quota: Optional[float] = None  # sales quota
    quota_period: Optional[str] = None  # monthly, quarterly, yearly
    join_date: Optional[datetime] = None
    is_active: bool = True
    last_login: Optional[datetime] = None

    # Performance metrics
    total_deals: int = 0
    active_deals: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    won_deal_value: float = 0.0
    lost_deal_value: float = 0.0
    conversion_rate: float = 0.0
    average_deal_size: float = 0.0
    quota_attainment: float = 0.0

    # Activity metrics
    activities_completed: int = 0
    calls_made: int = 0
    emails_sent: int = 0
    meetings_held: int = 0

    def calculate_conversion_rate(self):
        """Calculate win rate"""
        if self.total_deals > 0:
            self.conversion_rate = (self.won_deals / self.total_deals) * 100

    def calculate_average_deal_size(self):
        """Calculate average deal size"""
        if self.won_deals > 0:
            self.average_deal_size = self.won_deal_value / self.won_deals

    def calculate_quota_attainment(self):
        """Calculate quota attainment percentage"""
        if self.quota and self.quota > 0:
            self.quota_attainment = (self.won_deal_value / self.quota) * 100


@dataclass
class Product:
    """Product catalog model"""

    id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    unit_price: float = 0.0
    cost: Optional[float] = None
    currency: str = "USD"
    active: bool = True

    # Categories and tags
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Inventory
    in_stock: Optional[int] = None
    reorder_point: Optional[int] = None

    # Analytics
    total_sold: int = 0
    total_revenue: float = 0.0

    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)


# Validation functions
def validate_deal_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean deal data"""
    errors = []

    # Required fields
    if not data.get("title"):
        errors.append("Deal title is required")

    # Value validation
    if data.get("value") is not None:
        try:
            data["value"] = float(data["value"])
            if data["value"] < 0:
                errors.append("Deal value cannot be negative")
        except (ValueError, TypeError):
            errors.append("Deal value must be a valid number")

    # Probability validation
    if data.get("probability") is not None:
        try:
            prob = int(data["probability"])
            if prob < 0 or prob > 100:
                errors.append("Probability must be between 0 and 100")
            data["probability"] = prob
        except (ValueError, TypeError):
            errors.append("Probability must be an integer between 0 and 100")

    # Date validation
    for date_field in ["expected_close_date", "actual_close_date"]:
        if data.get(date_field):
            if isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.fromisoformat(
                        data[date_field].replace("Z", "+00:00")
                    )
                except ValueError:
                    errors.append(f"{date_field} must be a valid date")

    if errors:
        raise ValueError(f"Validation errors: {'; '.join(errors)}")

    return data


def validate_person_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean person data"""
    errors = []

    # Required fields
    if not data.get("name"):
        errors.append("Person name is required")

    # Email validation
    if data.get("email"):
        email = data["email"].strip().lower()
        if "@" not in email or "." not in email.split("@")[1]:
            errors.append("Invalid email format")
        data["email"] = email

    # Lead score validation
    if data.get("lead_score") is not None:
        try:
            score = int(data["lead_score"])
            if score < 0 or score > 100:
                errors.append("Lead score must be between 0 and 100")
            data["lead_score"] = score
        except (ValueError, TypeError):
            errors.append("Lead score must be an integer between 0 and 100")

    if errors:
        raise ValueError(f"Validation errors: {'; '.join(errors)}")

    return data


def validate_organization_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean organization data"""
    errors = []

    # Required fields
    if not data.get("name"):
        errors.append("Organization name is required")

    # Revenue validation
    if data.get("annual_revenue") is not None:
        try:
            data["annual_revenue"] = float(data["annual_revenue"])
            if data["annual_revenue"] < 0:
                errors.append("Annual revenue cannot be negative")
        except (ValueError, TypeError):
            errors.append("Annual revenue must be a valid number")

    # Employee count validation
    if data.get("employee_count") is not None:
        try:
            count = int(data["employee_count"])
            if count < 0:
                errors.append("Employee count cannot be negative")
            data["employee_count"] = count
        except (ValueError, TypeError):
            errors.append("Employee count must be a valid integer")

    # Website validation
    if data.get("website"):
        website = data["website"].strip()
        if not website.startswith(("http://", "https://")):
            website = "https://" + website
        data["website"] = website

    if errors:
        raise ValueError(f"Validation errors: {'; '.join(errors)}")

    return data
