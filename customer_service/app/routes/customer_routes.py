from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional

from app.models.customer import CustomerCreate, CustomerResponse
from shared_utils.db import get_db  # Updated import path
from app.services import customer_service

# Create an instance of APIRouter with proper prefix for A2
router = APIRouter(tags=["customers"], prefix="/customers")

@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(customer: CustomerCreate, response: Response, db: Session = Depends(get_db)):
    """
    Create a new customer.
    """
    created_customer = customer_service.create_customer(db=db, customer=customer)
    response.headers["Location"] = f"/customers/{created_customer.id}"
    return CustomerResponse.model_validate(created_customer)
    
@router.get("/{id}", response_model=CustomerResponse)
def get_customer(id: str, db: Session = Depends(get_db)):
    """
    Get a customer by their ID.
    """
    try:
        customer_id = int(id)
        if customer_id <= 0:
            raise HTTPException(status_code=400, detail="Customer ID must be a positive integer")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")
    
    db_customer = customer_service.get_customer_by_id(db=db, customer_id=customer_id)
    return CustomerResponse.model_validate(db_customer)

@router.get("/", response_model=CustomerResponse)
def get_customer_by_user_id(userId: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get a customer by their user ID (email).
    """
    if userId is None:
        raise HTTPException(status_code=400, detail="Missing required query parameter 'userId'")
    
    if '@' not in userId or '.' not in userId:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    db_customer = customer_service.get_customer_by_user_id(db=db, user_id=userId)
    return CustomerResponse.model_validate(db_customer)

@router.get("/status")
def status():
    """
    Health check endpoint for the Customer service.
    """
    return {"status": "OK"}