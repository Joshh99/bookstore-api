import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Session
from typing import Optional
import base64
import json
import time

from database import Base, engine, get_db
from schemas import CustomerCreate, CustomerResponse

# Create tables
Base.metadata.create_all(bind=engine, checkfirst=True)

# Define SQLAlchemy model
class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = {'extend_existing': True}  # This will prevent the duplicate table definition error


    id = Column(Integer, primary_key=True, index=True)
    userId = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    address2 = Column(String(200))
    city = Column(String(50))
    state = Column(String(2))
    zipcode = Column(String(10))
    phone = Column(String(15))

app = FastAPI(title="Customer Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Overwrite 422 error with 400
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"message": exc.errors()},
    )

# Service functions
def create_customer(db: Session, customer: CustomerCreate):
    # Check if a customer with the User-ID already exists in the database
    db_customer = db.query(Customer).filter(Customer.userId == customer.userId).first()
    if db_customer:
        raise HTTPException(status_code=422, detail="This user ID already exists in the system.")
    
    
    
    # Create a new Customer object
    new_customer = Customer(
        userId=customer.userId,
        name=customer.name,
        phone=customer.phone,
        address=customer.address,
        address2=customer.address2,
        city=customer.city,
        state=customer.state,
        zipcode=customer.zipcode
    )
    
    # Add the new customer to the database session
    db.add(new_customer)
    
    # Commit the changes to the database
    db.commit()
    
    # Refresh the object to include generated fields
    db.refresh(new_customer)
    
    return new_customer

def get_customer_by_id(db: Session, customer_id: int):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

def get_customer_by_user_id(db: Session, user_id: str):
    customer = db.query(Customer).filter(Customer.userId == user_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

# API Routes
@app.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer_endpoint(customer: CustomerCreate, response: Response, db: Session = Depends(get_db)):
    """
    Create a new customer.
    """
    created_customer = create_customer(db=db, customer=customer)
    response.headers["Location"] = f"/customers/{created_customer.id}"
    return CustomerResponse.model_validate(created_customer)
    
@app.get("/customers/{id}", response_model=CustomerResponse)
def get_customer_endpoint(id: str, db: Session = Depends(get_db)):
    """
    Get a customer by their ID.
    """
    try:
        customer_id = int(id)
        if customer_id <= 0:
            raise HTTPException(status_code=400, detail="Customer ID must be a positive integer")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")
    
    db_customer = get_customer_by_id(db=db, customer_id=customer_id)
    return CustomerResponse.model_validate(db_customer)

@app.get("/customers", response_model=CustomerResponse)
def get_customer_by_user_id_endpoint(userId: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get a customer by their user ID.
    """
    if userId is None:
        raise HTTPException(status_code=400, detail="Missing required query parameter 'userId'")
    
    if '@' not in userId or '.' not in userId:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    db_customer = get_customer_by_user_id(db=db, user_id=userId)
    return CustomerResponse.model_validate(db_customer)

@app.get("/status")
def status():
    """
    Health check endpoint for the Customer service.
    """
    return {"status": "OK"}

# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)