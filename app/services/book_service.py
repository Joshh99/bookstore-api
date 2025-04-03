from sqlalchemy.orm import Session
from app.models.book import Book, BookCreate
from fastapi import HTTPException
from pydantic import ValidationError

def create_book(db: Session, book: BookCreate):
    # Check if a book with the same ISBN already exists in the database
    db_book = db.query(Book).filter(Book.ISBN == book.ISBN).first()
    if db_book:
        # If a book with the same ISBN exists, raise an HTTPException with status code 400 (Bad Request)
        raise HTTPException(status_code=422, detail="This ISBN already exists in the system.")
    
    # Create a new Book object using the data from the BookCreate object
    try:
        new_book = Book(**book.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
    # Add the new book to the database session
    db.add(new_book)
    
    # Commit the changes to the database
    db.commit()
    
    # Refresh the new_book object to include any generated fields (e.g., auto-incremented ID)
    db.refresh(new_book)
    
    # Return the created book
    return new_book

def get_book_by_isbn(db: Session, isbn: str):
    # Query the database for a book with the specified ISBN
    book = db.query(Book).filter(Book.ISBN == isbn).first()

    if not book:
        # If the book is not found, raise an HTTPException with status code 404 (Not Found)
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Return the found book
    return book

def update_book(db: Session, isbn: str, book_data: BookCreate):
    # Query the database for a book with the specified ISBN
    book = db.query(Book).filter(Book.ISBN == isbn).first()

    if not book:
        # If the book is not found, raise an HTTPException with status code 404 (Not Found)
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update the book's fields with the values from the BookCreate object
    try:
        updated_book = book_data.model_dump(exclude_unset=True)
        for field, value in updated_book.items():
            setattr(book, field, value)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Commit the changes to the database
    db.commit()
    
    # Refresh the book object to include any updated fields
    db.refresh(book)
    
    # Return the updated book
    return book