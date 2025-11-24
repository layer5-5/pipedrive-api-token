"""
Analytics and business intelligence for Pipedrive MCP.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .models import StageChange, EnhancedDeal

logger = logging.getLogger(__name__)


@dataclass
class DealAnalytics:
    """Deal analytics and metrics"""

    total_deals: int = 0
    open_deals: int = 0
    won_deals: int = 0
    lost_deals: int = 0
    total_value: float = 0.0
    weighted_value: float = 0.0
    average_deal_size: float = 0.0
    conversion_rate: float = 0.0
    average_sales_cycle: float = 0.0  # days
    average_time_in_stages: Dict[str, float] = None

    def __post_init__(self):
        if self.average_time_in_stages is None:
            self.average_time_in_stages = {}


@dataclass
class StageAnalytics:
    """Pipeline stage analytics"""

    stage_id: int
    stage_name: str
    deals_count: int = 0
    total_value: float = 0.0
    average_time_in_stage: float = 0.0  # days
    conversion_rate_to_next: float = 0.0
    drop_off_rate: float = 0.0


class DealAnalyticsCalculator:
    """Calculator for deal and pipeline analytics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_deal_analytics(self, deals: List[Dict]) -> DealAnalytics:
        """
        Calculate comprehensive deal analytics.

        Args:
            deals: List of deal dictionaries

        Returns:
            DealAnalytics object with calculated metrics
        """
        analytics = DealAnalytics()

        if not deals:
            return analytics

        analytics.total_deals = len(deals)

        total_value = 0.0
        weighted_value = 0.0
        sales_cycle_days = []
        stage_times = {}

        for deal in deals:
            status = deal.get("status", "open")
            value = float(deal.get("value", 0))
            probability = int(deal.get("probability", 0))

            total_value += value
            weighted_value += value * (probability / 100)

            # Status counts
            if status == "open":
                analytics.open_deals += 1
            elif status == "won":
                analytics.won_deals += 1
            elif status == "lost":
                analytics.lost_deals += 1

            # Sales cycle calculation
            if deal.get("add_time") and deal.get("close_time"):
                try:
                    created = datetime.fromisoformat(
                        deal["add_time"].replace("Z", "+00:00")
                    )
                    closed = datetime.fromisoformat(
                        deal["close_time"].replace("Z", "+00:00")
                    )
                    sales_cycle_days.append((closed - created).days)
                except Exception:
                    pass

            # Stage time tracking
            stage_history = deal.get("stage_history", [])
            for stage_change in stage_history:
                stage_name = stage_change.get(
                    "to_stage_name", f"Stage_{stage_change.get('to_stage_id')}"
                )
                time_in_stage = stage_change.get("time_in_previous_stage", 0)

                if stage_name not in stage_times:
                    stage_times[stage_name] = []
                stage_times[stage_name].append(time_in_stage)

        # Calculate averages
        analytics.total_value = total_value
        analytics.weighted_value = weighted_value

        if analytics.total_deals > 0:
            analytics.average_deal_size = total_value / analytics.total_deals
            analytics.conversion_rate = (
                analytics.won_deals / analytics.total_deals
            ) * 100

        if sales_cycle_days:
            analytics.average_sales_cycle = sum(sales_cycle_days) / len(
                sales_cycle_days
            )

        # Calculate average time in each stage
        for stage_name, times in stage_times.items():
            if times:
                analytics.average_time_in_stages[stage_name] = sum(times) / len(times)

        return analytics

    def calculate_stage_analytics(self, deals: List[Dict]) -> List[StageAnalytics]:
        """
        Calculate analytics for each pipeline stage.

        Args:
            deals: List of deal dictionaries

        Returns:
            List of StageAnalytics objects
        """
        stage_data = {}

        # Collect data for each stage
        for deal in deals:
            current_stage_id = deal.get("stage_id")
            current_stage_name = deal.get("stage_name", f"Stage_{current_stage_id}")
            value = float(deal.get("value", 0))

            if current_stage_id not in stage_data:
                stage_data[current_stage_id] = {
                    "name": current_stage_name,
                    "deals": [],
                    "total_value": 0.0,
                    "stage_times": [],
                }

            stage_data[current_stage_id]["deals"].append(deal)
            stage_data[current_stage_id]["total_value"] += value

            # Track time in current stage
            time_in_stage = deal.get("time_in_current_stage")
            if time_in_stage is not None:
                stage_data[current_stage_id]["stage_times"].append(time_in_stage)

        # Calculate analytics for each stage
        stage_analytics = []
        for stage_id, data in stage_data.items():
            analytics = StageAnalytics(
                stage_id=stage_id,
                stage_name=data["name"],
                deals_count=len(data["deals"]),
                total_value=data["total_value"],
            )

            # Average time in stage
            if data["stage_times"]:
                analytics.average_time_in_stage = sum(data["stage_times"]) / len(
                    data["stage_times"]
                )

            stage_analytics.append(analytics)

        return stage_analytics

    def calculate_deal_velocity(self, deals: List[Dict]) -> Dict[str, float]:
        """
        Calculate deal velocity metrics.

        Args:
            deals: List of deal dictionaries

        Returns:
            Dictionary with velocity metrics
        """
        velocity_metrics = {
            "average_deal_velocity": 0.0,  # days from open to close
            "fastest_deal": float("inf"),
            "slowest_deal": 0.0,
            "deals_with_velocity": 0,
        }

        deal_durations = []

        for deal in deals:
            if deal.get("status") in ["won", "lost"]:
                created_time = deal.get("add_time")
                close_time = deal.get("close_time") or deal.get("update_time")

                if created_time and close_time:
                    try:
                        created = datetime.fromisoformat(
                            created_time.replace("Z", "+00:00")
                        )
                        closed = datetime.fromisoformat(
                            close_time.replace("Z", "+00:00")
                        )
                        duration = (closed - created).days

                        if duration > 0:
                            deal_durations.append(duration)
                    except Exception:
                        continue

        if deal_durations:
            velocity_metrics["average_deal_velocity"] = sum(deal_durations) / len(
                deal_durations
            )
            velocity_metrics["fastest_deal"] = min(deal_durations)
            velocity_metrics["slowest_deal"] = max(deal_durations)
            velocity_metrics["deals_with_velocity"] = len(deal_durations)

        return velocity_metrics

    def calculate_pipeline_health(self, deals: List[Dict]) -> Dict[str, Any]:
        """
        Calculate overall pipeline health metrics.

        Args:
            deals: List of deal dictionaries

        Returns:
            Dictionary with pipeline health metrics
        """
        health_metrics = {
            "pipeline_score": 0.0,  # 0-100
            "deal_quality_score": 0.0,
            "pipeline_velocity_score": 0.0,
            "conversion_efficiency": 0.0,
            "recommendations": [],
        }

        if not deals:
            health_metrics["recommendations"].append("No deals found to analyze")
            return health_metrics

        # Basic metrics
        total_deals = len(deals)
        open_deals = len([d for d in deals if d.get("status") == "open"])
        won_deals = len([d for d in deals if d.get("status") == "won"])
        lost_deals = len([d for d in deals if d.get("status") == "lost"])

        # Deal quality score (based on value and probability)
        total_value = sum(float(d.get("value", 0)) for d in deals)
        weighted_value = sum(
            float(d.get("value", 0)) * int(d.get("probability", 0)) / 100 for d in deals
        )

        if total_value > 0:
            health_metrics["deal_quality_score"] = min(
                100, (weighted_value / total_value) * 100
            )

        # Conversion efficiency
        if total_deals > 0:
            conversion_rate = (won_deals / total_deals) * 100
            health_metrics["conversion_efficiency"] = conversion_rate

        # Pipeline velocity score
        velocity_metrics = self.calculate_deal_velocity(deals)
        avg_velocity = velocity_metrics["average_deal_velocity"]

        # Score based on velocity (faster is better, assuming 30 days is ideal)
        if avg_velocity > 0:
            if avg_velocity <= 30:
                health_metrics["pipeline_velocity_score"] = 100
            elif avg_velocity <= 60:
                health_metrics["pipeline_velocity_score"] = 80
            elif avg_velocity <= 90:
                health_metrics["pipeline_velocity_score"] = 60
            else:
                health_metrics["pipeline_velocity_score"] = 40

        # Overall pipeline score (weighted average)
        health_metrics["pipeline_score"] = (
            health_metrics["deal_quality_score"] * 0.4
            + health_metrics["pipeline_velocity_score"] * 0.3
            + health_metrics["conversion_efficiency"] * 0.3
        )

        # Generate recommendations
        if health_metrics["deal_quality_score"] < 50:
            health_metrics["recommendations"].append(
                "Focus on higher-quality leads with better win probability"
            )

        if health_metrics["conversion_efficiency"] < 20:
            health_metrics["recommendations"].append(
                "Review sales process to improve conversion rates"
            )

        if avg_velocity > 90:
            health_metrics["recommendations"].append(
                "Sales cycle is too long - consider streamlining the process"
            )

        if open_deals > total_deals * 0.8:
            health_metrics["recommendations"].append(
                "Too many open deals - focus on closing existing opportunities"
            )

        return health_metrics

    def forecast_revenue(
        self, deals: List[Dict], days_ahead: int = 90
    ) -> Dict[str, Any]:
        """
        Forecast revenue based on current pipeline.

        Args:
            deals: List of deal dictionaries
            days_ahead: Number of days to forecast

        Returns:
            Dictionary with revenue forecast
        """
        forecast = {
            "total_pipeline_value": 0.0,
            "weighted_forecast": 0.0,
            "conservative_forecast": 0.0,
            "optimistic_forecast": 0.0,
            "deals_in_forecast": 0,
            "forecast_by_month": {},
        }

        cutoff_date = datetime.now() + timedelta(days=days_ahead)

        for deal in deals:
            if deal.get("status") != "open":
                continue

            expected_close_date = deal.get("expected_close_date")
            if expected_close_date:
                try:
                    close_date = datetime.fromisoformat(
                        expected_close_date.replace("Z", "+00:00")
                    )
                    if close_date > cutoff_date:
                        continue
                except Exception:
                    pass

            value = float(deal.get("value", 0))
            probability = int(deal.get("probability", 0))

            forecast["total_pipeline_value"] += value
            forecast["weighted_forecast"] += value * (probability / 100)
            forecast["conservative_forecast"] += value * (
                probability / 200
            )  # Half the probability
            forecast["optimistic_forecast"] += (
                value * min(100, probability * 1.2) / 100
            )  # 20% boost
            forecast["deals_in_forecast"] += 1

            # Group by month
            if expected_close_date:
                try:
                    close_date = datetime.fromisoformat(
                        expected_close_date.replace("Z", "+00:00")
                    )
                    month_key = close_date.strftime("%Y-%m")

                    if month_key not in forecast["forecast_by_month"]:
                        forecast["forecast_by_month"][month_key] = {
                            "weighted": 0.0,
                            "conservative": 0.0,
                            "optimistic": 0.0,
                            "deal_count": 0,
                        }

                    forecast["forecast_by_month"][month_key]["weighted"] += value * (
                        probability / 100
                    )
                    forecast["forecast_by_month"][month_key]["conservative"] += (
                        value * (probability / 200)
                    )
                    forecast["forecast_by_month"][month_key]["optimistic"] += (
                        value * min(100, probability * 1.2) / 100
                    )
                    forecast["forecast_by_month"][month_key]["deal_count"] += 1
                except Exception:
                    pass

        return forecast


def create_stage_change_record(
    deal_id: int,
    from_stage_id: Optional[int],
    to_stage_id: int,
    from_stage_name: Optional[str],
    to_stage_name: Optional[str],
    changed_by_user_id: Optional[int] = None,
    changed_by_user_name: Optional[str] = None,
    notes: Optional[str] = None,
) -> StageChange:
    """
    Create a stage change record for tracking.

    Args:
        deal_id: ID of the deal
        from_stage_id: Previous stage ID
        to_stage_id: New stage ID
        from_stage_name: Previous stage name
        to_stage_name: New stage name
        changed_by_user_id: User who made the change
        changed_by_user_name: Name of user who made the change
        notes: Optional notes about the change

    Returns:
        StageChange object
    """
    import uuid

    return StageChange(
        id=int(uuid.uuid4()) % 2147483647,  # Generate a random int ID
        deal_id=deal_id,
        from_stage_id=from_stage_id,
        to_stage_id=to_stage_id,
        from_stage_name=from_stage_name,
        to_stage_name=to_stage_name,
        changed_by_user_id=changed_by_user_id,
        changed_by_user_name=changed_by_user_name,
        change_date=datetime.now(),
        notes=notes,
    )
