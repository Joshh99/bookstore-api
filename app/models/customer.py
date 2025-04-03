from sqlalchemy import Column, String, Integer
from app.utils.db import Base
from pydantic import BaseModel, field_validator, EmailStr, ConfigDict
from typing import Optional, Any

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    userid = Column(String(255), unique=True, nullable=False)  # Changed from userId to userid
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    address2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zipcode = Column(String(10), nullable=False)

# For data sent by client when creating a customer
class CustomerCreate(BaseModel):
    userId: EmailStr  # Keep camelCase in the API
    name: str
    phone: str
    address: str
    address2: Optional[str] = None
    city: str
    state: str
    zipcode: str
    
    @field_validator('state')
    def validate_state(cls, value):
        if len(value) != 2:
            raise ValueError("State must be a valid 2-letter US state abbreviation")
        return value
    
    # This model_dump method will convert userId to userid for database operations
    def model_dump_for_db(self):
        data = self.model_dump()
        # Convert camelCase to lowercase for database column
        data["userid"] = data.pop("userId")
        return data


# For data returned to client
class CustomerResponse(BaseModel):
    id: int
    userId: EmailStr  # Keep camelCase in the API response
    name: str
    phone: str
    address: str
    address2: Optional[str] = None
    city: str
    state: str
    zipcode: str
    
    

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs):
        # If it's an ORM model, transform field names to match schema
        if hasattr(obj, '__table__'):
            # Create a dictionary with transformed keys
            data = {
                'id': obj.id,
                'userId': obj.userid,  # Map lowercase to camelCase
                'name': obj.name,
                'phone': obj.phone,
                'address': obj.address,
                'address2': obj.address2,
                'city': obj.city,
                'state': obj.state,
                'zipcode': obj.zipcode
            }
            return super().model_validate(data, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)