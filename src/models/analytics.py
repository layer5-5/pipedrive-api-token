"""Analytics data models for Pipedrive MCP Server."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import Field

from .common import PipedriveBaseModel


class DealAnalytics(PipedriveBaseModel):
    """Deal analytics and metrics."""

    # Basic counts
    total_deals: int = Field(description="Total number of deals")
    open_deals: int = Field(description="Number of open deals")
    won_deals: int = Field(description="Number of won deals")
    lost_deals: int = Field(description="Number of lost deals")

    # Value metrics
    total_value: Decimal = Field(description="Total value of all deals")
    open_value: Decimal = Field(description="Total value of open deals")
    won_value: Decimal = Field(description="Total value of won deals")
    lost_value: Decimal = Field(description="Total value of lost deals")

    # Conversion metrics
    win_rate: Decimal = Field(description="Win rate percentage")
    loss_rate: Decimal = Field(description="Loss rate percentage")

    # Average metrics
    average_deal_size: Decimal = Field(description="Average deal value")
    average_sales_cycle: Decimal = Field(description="Average sales cycle in days")

    # Pipeline health
    weighted_pipeline_value: Decimal = Field(
        description="Probability-weighted pipeline value"
    )
    pipeline_health_score: Decimal = Field(description="Overall pipeline health score")

    # Time metrics
    average_time_in_stage: Dict[str, Decimal] = Field(
        default_factory=dict, description="Average time spent in each stage"
    )
    average_conversion_time: Decimal = Field(
        description="Average time from creation to close"
    )

    # Performance indicators
    sales_velocity: Decimal = Field(
        description="Sales velocity (value × conversion ÷ cycle length)"
    )
    conversion_rate_by_stage: Dict[str, Decimal] = Field(
        default_factory=dict, description="Conversion rates by stage"
    )

    # Date range
    period_start: date = Field(description="Analytics period start date")
    period_end: date = Field(description="Analytics period end date")
    generated_at: datetime = Field(description="When analytics were generated")


class ContactAnalytics(PipedriveBaseModel):
    """Contact analytics and engagement metrics."""

    # Basic counts
    total_contacts: int = Field(description="Total number of contacts")
    active_contacts: int = Field(description="Number of active contacts")
    new_contacts: int = Field(description="Number of new contacts in period")

    # Engagement metrics
    average_interactions: Decimal = Field(
        description="Average interactions per contact"
    )
    total_interactions: int = Field(
        description="Total interactions across all contacts"
    )
    response_rate: Decimal = Field(description="Response rate to communications")

    # Deal involvement
    contacts_with_deals: int = Field(
        description="Number of contacts with associated deals"
    )
    average_deals_per_contact: Decimal = Field(description="Average deals per contact")

    # Value attribution
    total_generated_revenue: Decimal = Field(
        description="Total revenue attributed to contacts"
    )
    average_revenue_per_contact: Decimal = Field(
        description="Average revenue per contact"
    )

    # Engagement scoring
    high_engagement_contacts: int = Field(
        description="Number of highly engaged contacts"
    )
    engagement_score_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Distribution of engagement scores"
    )

    # Lifecycle metrics
    average_conversion_time: Decimal = Field(
        description="Average time from contact creation to first deal"
    )
    lead_to_customer_rate: Decimal = Field(
        description="Lead to customer conversion rate"
    )

    # Communication preferences
    preferred_contact_methods: Dict[str, int] = Field(
        default_factory=dict, description="Preferred contact method distribution"
    )

    # Date range
    period_start: date = Field(description="Analytics period start date")
    period_end: date = Field(description="Analytics period end date")
    generated_at: datetime = Field(description="When analytics were generated")


class CompanyAnalytics(PipedriveBaseModel):
    """Company analytics and account health metrics."""

    # Basic counts
    total_companies: int = Field(description="Total number of companies")
    active_companies: int = Field(description="Number of active companies")
    new_companies: int = Field(description="Number of new companies in period")

    # Revenue metrics
    total_revenue: Decimal = Field(description="Total revenue from all companies")
    average_revenue_per_company: Decimal = Field(
        description="Average revenue per company"
    )
    revenue_growth_rate: Decimal = Field(description="Revenue growth rate percentage")

    # Deal metrics
    companies_with_deals: int = Field(
        description="Number of companies with associated deals"
    )
    average_deals_per_company: Decimal = Field(description="Average deals per company")

    # Account health
    health_score_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Distribution of account health scores"
    )
    average_health_score: Decimal = Field(description="Average account health score")
    churn_risk_companies: int = Field(
        description="Number of companies with high churn risk"
    )

    # Market penetration
    wallet_share_estimate: Decimal = Field(
        description="Estimated wallet share percentage"
    )
    growth_potential_score: Decimal = Field(description="Growth potential score")

    # Firmographics
    industry_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Distribution by industry"
    )
    size_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Distribution by company size"
    )

    # Date range
    period_start: date = Field(description="Analytics period start date")
    period_end: date = Field(description="Analytics period end date")
    generated_at: datetime = Field(description="When analytics were generated")


class UserAnalytics(PipedriveBaseModel):
    """User performance analytics and metrics."""

    # Basic info
    user_id: int = Field(description="User ID")
    user_name: str = Field(description="User name")
    user_email: str = Field(description="User email")
    user_role: str = Field(description="User role")

    # Performance metrics
    total_deals_owned: int = Field(description="Total deals owned by user")
    open_deals: int = Field(description="Number of open deals")
    won_deals: int = Field(description="Number of won deals")
    lost_deals: int = Field(description="Number of lost deals")

    # Value metrics
    total_deal_value: Decimal = Field(description="Total value of user's deals")
    won_deal_value: Decimal = Field(description="Total value of won deals")
    average_deal_size: Decimal = Field(description="Average deal size")

    # Conversion metrics
    win_rate: Decimal = Field(description="User's win rate percentage")
    conversion_rate: Decimal = Field(description="Overall conversion rate")

    # Activity metrics
    total_activities: int = Field(description="Total activities performed")
    activities_per_deal: Decimal = Field(description="Average activities per deal")
    activity_completion_rate: Decimal = Field(description="Activity completion rate")

    # Efficiency metrics
    sales_velocity: Decimal = Field(description="User's sales velocity")
    productivity_score: Decimal = Field(description="Overall productivity score")
    time_management_score: Decimal = Field(
        description="Time management efficiency score"
    )

    # Goal attainment
    quota_attainment_rate: Decimal = Field(description="Quota attainment percentage")
    target_completion_rate: Decimal = Field(description="Target completion rate")

    # Ranking metrics
    performance_rank: int = Field(description="Performance rank in team")
    percentile_score: Decimal = Field(description="Performance percentile score")

    # Date range
    period_start: date = Field(description="Analytics period start date")
    period_end: date = Field(description="Analytics period end date")
    generated_at: datetime = Field(description="When analytics were generated")


class SalesVelocity(PipedriveBaseModel):
    """Sales velocity calculation results."""

    # Input metrics
    total_deal_value: Decimal = Field(description="Total deal value in period")
    conversion_rate: Decimal = Field(description="Deal conversion rate")
    average_sales_cycle: Decimal = Field(
        description="Average sales cycle length in days"
    )

    # Calculated velocity
    sales_velocity: Decimal = Field(
        description="Sales velocity (value × conversion ÷ cycle length)"
    )
    velocity_trend: str = Field(
        description="Velocity trend (improving/stable/declining)"
    )

    # Comparative metrics
    team_average_velocity: Decimal = Field(description="Team average velocity")
    performance_vs_team: Decimal = Field(description="Performance vs team average")

    # Period info
    period_start: date = Field(description="Analysis period start date")
    period_end: date = Field(description="Analysis period end date")
    calculated_at: datetime = Field(description="When velocity was calculated")


class ConversionRates(PipedriveBaseModel):
    """Conversion rate analysis results."""

    # Lead conversion
    lead_to_deal_rate: Decimal = Field(description="Lead to qualified deal rate")
    lead_to_opportunity_rate: Decimal = Field(description="Lead to opportunity rate")

    # Deal conversion
    deal_to_won_rate: Decimal = Field(description="Deal to won rate")
    stage_conversion_rates: Dict[str, Decimal] = Field(
        default_factory=dict, description="Conversion rates by stage"
    )

    # Overall metrics
    overall_conversion_rate: Decimal = Field(description="Overall conversion rate")
    conversion_funnel_analysis: Dict[str, Decimal] = Field(
        default_factory=dict, description="Funnel analysis by stage"
    )

    # Time-based conversion
    average_conversion_time: Decimal = Field(description="Average time to conversion")
    conversion_time_by_stage: Dict[str, Decimal] = Field(
        default_factory=dict, description="Average conversion time by stage"
    )

    # Period info
    period_start: date = Field(description="Analysis period start date")
    period_end: date = Field(description="Analysis period end date")
    calculated_at: datetime = Field(description="When conversion rates were calculated")


class PipelineHealth(PipedriveBaseModel):
    """Pipeline health analysis results."""

    # Basic metrics
    total_pipeline_value: Decimal = Field(description="Total value in pipeline")
    weighted_pipeline_value: Decimal = Field(
        description="Probability-weighted pipeline value"
    )

    # Health indicators
    pipeline_health_score: Decimal = Field(
        description="Overall pipeline health score (0-100)"
    )
    health_grade: str = Field(description="Health grade (A/B/C/D/F)")

    # Stage analysis
    stage_distribution: Dict[str, Decimal] = Field(
        default_factory=dict, description="Deal distribution by stage"
    )
    bottleneck_stages: List[str] = Field(
        default_factory=list, description="Stages with bottlenecks"
    )

    # Risk indicators
    stale_deals_count: int = Field(description="Number of stale deals")
    at_risk_deals_count: int = Field(description="Number of at-risk deals")
    average_deal_age: Decimal = Field(description="Average age of deals in pipeline")

    # Forecasting
    projected_revenue: Decimal = Field(
        description="Projected revenue from current pipeline"
    )
    forecast_accuracy: Decimal = Field(description="Historical forecast accuracy")

    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list, description="Pipeline improvement recommendations"
    )

    # Period info
    period_start: date = Field(description="Analysis period start date")
    period_end: date = Field(description="Analysis period end date")
    calculated_at: datetime = Field(description="When pipeline health was calculated")


class EngagementScore(PipedriveBaseModel):
    """Contact engagement score analysis."""

    # Score components
    interaction_frequency_score: Decimal = Field(
        description="Interaction frequency score"
    )
    response_time_score: Decimal = Field(description="Response time score")
    deal_involvement_score: Decimal = Field(description="Deal involvement score")
    communication_quality_score: Decimal = Field(
        description="Communication quality score"
    )

    # Overall score
    overall_engagement_score: Decimal = Field(description="Overall engagement score")
    engagement_level: str = Field(description="Engagement level (high/medium/low)")

    # Score breakdown
    score_factors: Dict[str, Decimal] = Field(
        default_factory=dict, description="Detailed score factors"
    )

    # Historical trends
    score_trend: str = Field(description="Score trend (improving/stable/declining)")
    score_history: List[Decimal] = Field(
        default_factory=list, description="Historical score values"
    )

    # Contact info
    contact_id: int = Field(description="Contact ID")
    contact_name: str = Field(description="Contact name")

    # Period info
    period_start: date = Field(description="Analysis period start date")
    period_end: date = Field(description="Analysis period end date")
    calculated_at: datetime = Field(description="When engagement score was calculated")


# Forward references for type hints
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .deal import Deal
    from .contact import Person
    from .company import Organization
    from .user import User
