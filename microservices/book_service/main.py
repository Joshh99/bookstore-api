import os
import uvicorn
import base64
import json
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, String, Text, Numeric, Integer
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Any

from database import Base, engine, get_db
from schemas import BookCreate, BookResponse

# Create tables
Base.metadata.create_all(bind=engine)

# Define SQLAlchemy model
class Book(Base):
    __tablename__ = "books"

    ISBN = Column(String(20), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    Author = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    genre = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)

app = FastAPI(title="Book Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service functions
def create_book(db: Session, book: BookCreate):
    """
    Create a new book in the database.
    
    :param db: Database session
    :param book: Book data to be created
    :return: Created book
    :raises HTTPException: If a book with the same ISBN already exists
    """
    # Check if a book with the same ISBN already exists
    existing_book = db.query(Book).filter(Book.ISBN == book.ISBN).first()
    if existing_book:
        raise HTTPException(
            status_code=422, 
            detail="A book with this ISBN already exists in the system."
        )
    
    # Create a new Book object using the data from the BookCreate object
    new_book = Book(**book.model_dump())
    
    # Add the new book to the database session
    db.add(new_book)
    
    # Commit the changes to the database
    db.commit()
    
    # Refresh the new_book object to include any generated fields
    db.refresh(new_book)
    
    return new_book

def get_book_by_isbn(db: Session, isbn: str):
    """
    Retrieve a book by its ISBN.
    
    :param db: Database session
    :param isbn: ISBN of the book to retrieve
    :return: Book object
    :raises HTTPException: If the book is not found
    """
    book = db.query(Book).filter(Book.ISBN == isbn).first()

    if not book:
        raise HTTPException(
            status_code=404, 
            detail="Book not found"
        )
    
    return book

def update_book(db: Session, isbn: str, book_data: BookCreate):
    """
    Update an existing book in the database.
    
    :param db: Database session
    :param isbn: ISBN of the book to update
    :param book_data: Updated book data
    :return: Updated book
    :raises HTTPException: If the book is not found or validation fails
    """
    # Query the database for the book with the specified ISBN
    book = db.query(Book).filter(Book.ISBN == isbn).first()

    if not book:
        raise HTTPException(
            status_code=404, 
            detail="Book not found"
        )
    
    # Update the book's fields with the values from the BookCreate object
    updated_book_data = book_data.model_dump(exclude_unset=True)
    for field, value in updated_book_data.items():
        setattr(book, field, value)

    # Commit the changes to the database
    db.commit()
    
    # Refresh the book object to include any updated fields
    db.refresh(book)
    
    return book

# API Routes
@app.post("/books", response_model=BookResponse, status_code=201)
def create_new_book(book: BookCreate, db: Session = Depends(get_db)):
    """
    Create a new book.
    
    Validates the book data and adds it to the database.
    Raises an HTTPException if the book already exists.
    """
    return create_book(db=db, book=book)

@app.get("/books/isbn/{isbn}", response_model=BookResponse)
def get_book_by_isbn_path(isbn: str, db: Session = Depends(get_db)):
    """
    Retrieve a book by its ISBN.
    
    Raises an HTTPException if the book is not found.
    """
    return get_book_by_isbn(db, isbn)

@app.get("/books/{isbn}", response_model=BookResponse)
def get_book(isbn: str, db: Session = Depends(get_db)):
    """
    Retrieve a book by its ISBN.
    
    Raises an HTTPException if the book is not found.
    """
    return get_book_by_isbn(db, isbn)

@app.put("/books/{isbn}", response_model=BookResponse)
def update_existing_book(isbn: str, book: BookCreate, db: Session = Depends(get_db)):
    """
    Update an existing book.
    
    Validates that the ISBN in the path matches the ISBN in the body.
    Raises an HTTPException if the book is not found or ISBNs don't match.
    """
    if isbn != book.ISBN:
        raise HTTPException(status_code=400, detail="ISBN in path must match ISBN in body")
    
    return update_book(db=db, isbn=isbn, book_data=book)

@app.get("/status")
def status():
    """
    Health check endpoint for the Book service.
    """
    return {"status": "OK"}

# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPExceptions and return a consistent JSON response
    with the appropriate status code and error message.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions and return a 500 Internal Server Error
    with a generic error message.
    """
    # You might want to log the exception here
    print(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

if __name__ == "__main__":
    # Configure port from environment variable, default to 3000
    port = int(os.getenv("PORT", 3000))
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True
    )