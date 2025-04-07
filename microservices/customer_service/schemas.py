from pydantic import BaseModel, EmailStr
from typing import Optional

class CustomerBase(BaseModel):
    userId: EmailStr
    name: str
    address: str
    address2: Optional[str] = None
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