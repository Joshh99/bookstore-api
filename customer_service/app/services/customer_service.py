from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.customer import Customer, CustomerCreate

def create_customer(db: Session, customer: CustomerCreate):
    """
    Create a new customer in the database.
    """
    # Check if a customer with the User-ID already exists in the database
    db_customer = db.query(Customer).filter(Customer.userId == customer.userId).first()
    if db_customer:
        raise HTTPException(status_code=422, detail="This user ID already exists in the system.")
    
    # Check if a customer with the same email already exists
    db_customer_email = db.query(Customer).filter(Customer.email == customer.email).first()
    if db_customer_email:
        raise HTTPException(status_code=422, detail="This email already exists in the system.")
    
    try:
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
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Add the new customer to the database session
    db.add(new_customer)
    
    # Commit the changes to the database
    db.commit()
    
    # Refresh the object to include generated fields
    db.refresh(new_customer)
    
    return new_customer

def get_customer_by_id(db: Session, customer_id: int):
    """
    Get a customer by their numeric ID.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

def get_customer_by_user_id(db: Session, user_id: str):
    """
    Get a customer by their user ID (email).
    """
    customer = db.query(Customer).filter(Customer.userId == user_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer