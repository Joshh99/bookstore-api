from sqlalchemy.orm import Session
from app.models.customer import Customer, CustomerCreate
from fastapi import HTTPException

def create_customer(db: Session, customer: CustomerCreate):
    """
    Create a new customer in the database.
    """
    # Check if a customer with the User-ID already exists in the database
    db_customer = db.query(Customer).filter(Customer.userid == customer.userId).first()
    if db_customer:
        raise HTTPException(status_code=422, detail="This user ID already exists in the system.")
    
    # Create a new Customer object using the data from CustomerCreate
    # Use the helper method to convert field names
    db_data = customer.model_dump_for_db()
    new_customer = Customer(**db_data)
    
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
    customer = db.query(Customer).filter(Customer.userid == user_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer