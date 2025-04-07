import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Session
from typing import Optional
import base64
import json
import time

from database import Base, engine, get_db
from schemas import CustomerCreate, CustomerResponse

# Create tables
Base.metadata.create_all(bind=engine)

# Define SQLAlchemy model
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

app = FastAPI(title="Customer Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT utility functions
def decode_jwt_payload(token: str):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload_base64 = parts[1]
        payload_base64 += '=' * ((4 - len(payload_base64) % 4) % 4)
        
        payload_bytes = base64.urlsafe_b64decode(payload_base64)
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        return None

def validate_jwt_payload(payload):
    if not payload or not isinstance(payload, dict):
        return False, "Invalid token format"
    
    valid_subjects = ["starlord", "gamora", "drax", "rocket", "groot"]
    if "sub" not in payload or payload["sub"] not in valid_subjects:
        return False, "Invalid subject in token"
    
    if "exp" not in payload or not isinstance(payload["exp"], (int, float)):
        return False, "Missing or invalid expiration in token"
    
    current_time = time.time()
    if payload["exp"] <= current_time:
        return False, "Token has expired"
    
    if "iss" not in payload or payload["iss"] != "cmu.edu":
        return False, "Invalid issuer in token"
    
    return True, "Valid token"

# JWT Middleware
@app.middleware("http")
async def jwt_validation_middleware(request: Request, call_next):
    # Always allow status endpoint
    if request.url.path == "/status":
        return await call_next(request)
    
    # Validate X-Client-Type header
    client_type = request.headers.get("X-Client-Type")
    if not client_type:
        return JSONResponse(
            status_code=400,
            content={"message": "Missing X-Client-Type header"}
        )
    
    # Validate client type
    valid_client_types = ["Web", "iOS", "Android"]
    if client_type not in valid_client_types:
        return JSONResponse(
            status_code=400,
            content={"message": f"Invalid X-Client-Type. Must be one of {valid_client_types}"}
        )
    
    # Validate Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"message": "Missing or invalid Authorization header"}
        )
    
    # Extract and decode token
    token = auth_header.replace("Bearer ", "")
    payload = decode_jwt_payload(token)
    
    # Validate token payload
    is_valid, message = validate_jwt_payload(payload)
    if not is_valid:
        return JSONResponse(
            status_code=401,
            content={"message": message}
        )
    
    # Continue processing the request
    response = await call_next(request)
    return response

# Service functions
def create_customer(db: Session, customer: CustomerCreate):
    # Check if a customer with the User-ID already exists in the database
    db_customer = db.query(Customer).filter(Customer.userId == customer.userId).first()
    if db_customer:
        raise HTTPException(status_code=422, detail="This user ID already exists in the system.")
    
    # Check if a customer with the same email already exists
    db_customer_email = db.query(Customer).filter(Customer.email == customer.email).first()
    if db_customer_email:
        raise HTTPException(status_code=422, detail="This email already exists in the system.")
    
    # Create a new Customer object
    new_customer = Customer(
        userId=customer.userId,
        name=customer.name,
        email=customer.email,
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