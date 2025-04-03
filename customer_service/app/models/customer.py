# customer.py
from sqlalchemy import Column, String, Integer
from shared_utils.db import Base  
from pydantic import BaseModel, field_validator, EmailStr, ConfigDict
from typing import Optional, Any

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    address = Column(String(200))
    address2 = Column(String(200))
    city = Column(String(50))
    state = Column(String(2))
    zipcode = Column(String(10))
    phone = Column(String(15))

class CustomerBase(BaseModel):
    userId: str
    name: str
    email: str
    address: str
    address2: str = None
    city: str
    state: str
    zipcode: str
    phone: str

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    
    class Config:
        from_attributes = True