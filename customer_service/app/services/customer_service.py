from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.customer import Customer, CustomerCreate

def create_customer(db: Session, customer: CustomerCreate):
    """Create a new customer in database"""
    db_customer = db.query(Customer).filter(Customer.userid == customer.userId).first()
    if db_customer:
        raise HTTPException(
            status_code=422,
            detail="This user ID already exists in the system."
        )
    
    db_data = customer.model_dump_for_db()
    new_customer = Customer(**db_data)
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return new_customer

def get_customer_by_id(db: Session, customer_id: int):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    return customer

def get_customer_by_user_id(db: Session, user_id: str):
    """Get customer by user ID (email)"""
    customer = db.query(Customer).filter(Customer.userid == user_id).first()
    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )
    return customer