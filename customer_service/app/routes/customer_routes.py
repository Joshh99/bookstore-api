from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from shared_utils.db import get_db
from app.models.customer import CustomerCreate, CustomerResponse
from app.services.customer_service import (
    create_customer,
    get_customer_by_id,
    get_customer_by_user_id
)

router = APIRouter(tags=["customers"], prefix="/customers")

@router.get("/status")
def status():
    """Health check endpoint"""
    return {"status": "OK"}

@router.post("/", response_model=CustomerResponse, status_code=201)
def create_new_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    x_client_type: str = Header(...),
    authorization: str = Header(...)
):
    """Create a new customer"""
    return create_customer(db=db, customer=customer)

@router.get("/{id}", response_model=CustomerResponse)
def get_customer_by_id_endpoint(
    id: str,
    db: Session = Depends(get_db),
    x_client_type: str = Header(...),
    authorization: str = Header(...)
):
    """Get customer by ID"""
    try:
        customer_id = int(id)
        if customer_id <= 0:
            raise HTTPException(status_code=400, detail="Customer ID must be positive")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")
    
    customer = get_customer_by_id(db=db, customer_id=customer_id)
    
    # Mobile response transformation
    if x_client_type in ["iOS", "Android"]:
        response_data = CustomerResponse.model_validate(customer).model_dump()
        for field in ["address", "address2", "city", "state", "zipcode"]:
            response_data.pop(field, None)
        return response_data
    
    return customer

@router.get("/", response_model=CustomerResponse)
def get_customer_by_user_id_endpoint(
    userId: Optional[str] = None,
    db: Session = Depends(get_db),
    x_client_type: str = Header(...),
    authorization: str = Header(...)
):
    """Get customer by user ID (email)"""
    if userId is None:
        raise HTTPException(status_code=400, detail="Missing userId parameter")
    
    if '@' not in userId or '.' not in userId:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    customer = get_customer_by_user_id(db=db, user_id=userId)
    
    # Mobile response transformation
    if x_client_type in ["iOS", "Android"]:
        response_data = CustomerResponse.model_validate(customer).model_dump()
        for field in ["address", "address2", "city", "state", "zipcode"]:
            response_data.pop(field, None)
        return response_data
    
    return customer