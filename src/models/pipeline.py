"""Pipeline and Stage data models."""

from datetime import datetime
from typing import List, Optional
from pydantic import Field

from .common import PipedriveBaseModel


class Stage(PipedriveBaseModel):
    """Pipeline stage."""

    id: int = Field(description="Stage ID")
    order_nr: int = Field(description="Stage order number")
    name: str = Field(description="Stage name")
    pipeline_id: int = Field(description="Pipeline ID")
    deal_probability: Optional[int] = Field(None, description="Win probability percentage")
    rotten_flag: Optional[bool] = Field(None, description="Whether stage has rottenness enabled")
    rotten_days: Optional[int] = Field(None, description="Days until deal is considered rotten")
    active_flag: bool = Field(True, description="Whether stage is active")
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")


class Pipeline(PipedriveBaseModel):
    """Sales pipeline."""

    id: int = Field(description="Pipeline ID")
    name: str = Field(description="Pipeline name")
    url_title: Optional[str] = Field(None, description="URL-friendly title")
    order_nr: int = Field(description="Pipeline order number")
    active: bool = Field(True, description="Whether pipeline is active")
    deal_probability: Optional[bool] = Field(None, description="Whether probability is enabled")
    add_time: datetime = Field(description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    selected: Optional[bool] = Field(None, description="Whether pipeline is selected")
    
    # Stages
    stages: List[Stage] = Field(default_factory=list, description="Pipeline stages")
