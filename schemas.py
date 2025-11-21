"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date as DateType

# Core app schemas

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Display name")
    email: Optional[str] = Field(None, description="Email address")
    avatar_url: Optional[str] = Field(None, description="Profile avatar")
    is_active: bool = Field(True, description="Whether user is active")

class StepLog(BaseModel):
    """
    Step logs per user per date
    Collection name: "steplog"
    """
    user: str = Field(..., description="User display name")
    steps: int = Field(..., ge=0, description="Number of steps for the entry")
    date: DateType = Field(default_factory=DateType.today, description="Date of the steps (YYYY-MM-DD)")
    note: Optional[str] = Field(None, description="Optional note for this entry")

# Example schemas kept for reference (not used by the app)
class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
