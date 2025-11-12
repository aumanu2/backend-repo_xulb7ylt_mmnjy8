"""
Database Schemas

Nightclub app collections.
Each Pydantic model represents a collection in MongoDB. Collection name is the lowercase class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Event(BaseModel):
    title: str = Field(..., description="Event name")
    date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    dj: str = Field(..., description="Headlining DJ")
    price: float = Field(..., ge=0, description="Ticket price in EUR")
    description: Optional[str] = Field(None, description="Event description")
    image: Optional[str] = Field(None, description="Image URL")

class Ticketpurchase(BaseModel):
    buyer_name: str = Field(..., description="Buyer full name")
    email: EmailStr = Field(..., description="Buyer email")
    phone: Optional[str] = Field(None, description="Buyer phone number")
    event_id: str = Field(..., description="Event ID (stringified ObjectId)")
    quantity: int = Field(..., ge=1, description="Number of tickets")
    total_price: float = Field(..., ge=0, description="Computed total price in EUR")

# Optional: Simple gallery item model if needed by admin in the future
class Galleryitem(BaseModel):
    url: str = Field(..., description="Image URL")
    caption: Optional[str] = Field(None, description="Caption text")
