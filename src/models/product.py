"""Product data models."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import Field

from .common import PipedriveBaseModel


class ProductPrice(PipedriveBaseModel):
    """Product price in specific currency."""

    id: int = Field(description="Price ID")
    product_id: int = Field(description="Product ID")
    price: Decimal = Field(description="Price")
    currency: str = Field(description="Currency code")
    cost: Optional[Decimal] = Field(None, description="Cost")
    overhead_cost: Optional[Decimal] = Field(None, description="Overhead cost")


class Product(PipedriveBaseModel):
    """Product in catalog."""

    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    code: Optional[str] = Field(None, description="Product code/SKU")
    
    # Ownership
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    owner_name: Optional[str] = Field(None, description="Owner name")
    
    # Pricing
    unit: Optional[str] = Field(None, description="Unit type")
    tax: Optional[Decimal] = Field(None, description="Tax percentage")
    prices: List[ProductPrice] = Field(default_factory=list, description="Prices in different currencies")
    
    # Status
    active_flag: bool = Field(True, description="Whether product is active")
    selectable: bool = Field(True, description="Whether product is selectable")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    
    # Timestamps
    add_time: Optional[datetime] = Field(None, description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Files
    files_count: Optional[int] = Field(None, description="Number of files")
    
    # Followers
    followers_count: Optional[int] = Field(None, description="Number of followers")
    
    # Custom fields
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom field values")


class ProductCreateRequest(PipedriveBaseModel):
    """Request model for creating a product."""

    name: str = Field(description="Product name")
    code: Optional[str] = Field(None, description="Product code")
    unit: Optional[str] = Field(None, description="Unit type")
    tax: Optional[Decimal] = Field(None, description="Tax percentage")
    prices: Optional[List[Dict[str, Any]]] = Field(None, description="Prices")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    owner_id: Optional[int] = Field(None, description="Owner user ID")


class ProductUpdateRequest(PipedriveBaseModel):
    """Request model for updating a product."""

    name: Optional[str] = Field(None, description="Product name")
    code: Optional[str] = Field(None, description="Product code")
    unit: Optional[str] = Field(None, description="Unit type")
    tax: Optional[Decimal] = Field(None, description="Tax percentage")
    prices: Optional[List[Dict[str, Any]]] = Field(None, description="Prices")
    visible_to: Optional[str] = Field(None, description="Visibility level")
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    active_flag: Optional[bool] = Field(None, description="Active status")
