from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.book import Book, BookCreate

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
    
    try:
        # Create a new Book object using the data from the BookCreate object
        new_book = Book(**book.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
    
    try:
        # Update the book's fields with the values from the BookCreate object
        updated_book_data = book_data.model_dump(exclude_unset=True)
        for field, value in updated_book_data.items():
            setattr(book, field, value)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Commit the changes to the database
    db.commit()
    
    # Refresh the book object to include any updated fields
    db.refresh(book)
    
    return book