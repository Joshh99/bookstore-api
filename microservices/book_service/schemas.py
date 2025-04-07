from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Any

class BookBase(BaseModel):
    """ 
    The schema serves as the base schema for the book model. 
    It defines the common fields that are shared across 
    different book-related schemas.
    Also, All the fields in this schema are REQUIRED by default. 
    """
    ISBN: str
    title: str
    Author: str
    description: str
    genre: str
    price: Decimal = Field(..., decimal_places=2)  # ... -> price field is required
    quantity: int

    @field_validator('price')
    def validate_price(cls, value):
        if value <= 0:
            raise ValueError('Price must be greater than zero')
        return value
    
    # Using just the Config approach
    class Config:
        json_encoders = {
            Decimal: float  # Convert Decimal to float during JSON serialization
        }

class BookCreate(BookBase):
    """
    The schema represents the input data required for creating a new book.
    """
    pass      

class BookResponse(BookBase):
    """
    The schema represents the output data that will be returned when a 
    book is successfully created, retrieved, or updated.
    """
    class Config:
        from_attributes = True   # allows the schema to read data from SQLAlchemy models directly
        json_encoders = {
            Decimal: float  # Convert Decimal to float during JSON serialization
        }