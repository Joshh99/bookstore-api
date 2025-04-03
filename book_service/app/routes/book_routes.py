from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.book import BookCreate, BookResponse
from app.services.book_service import create_book, get_book_by_isbn, update_book
from app.utils.db import get_db

# Create an instance of APIRouter for book routes
router = APIRouter(tags=["books"], prefix="/books")

@router.get("/status")
def status():
    """
    Health check endpoint for the Book service.
    """
    return {"status": "OK"}

@router.post("/", response_model=BookResponse, status_code=201)
def create_new_book(book: BookCreate, db: Session = Depends(get_db)):
    """
    Create a new book.
    
    Validates the book data and adds it to the database.
    Raises an HTTPException if the book already exists.
    """
    return create_book(db=db, book=book)

@router.get("/isbn/{isbn}", response_model=BookResponse)
def get_book_by_isbn_path(isbn: str, db: Session = Depends(get_db)):
    """
    Retrieve a book by its ISBN.
    
    Raises an HTTPException if the book is not found.
    """
    return get_book_by_isbn(db, isbn)

@router.get("/{isbn}", response_model=BookResponse)
def get_book(isbn: str, db: Session = Depends(get_db)):
    """
    Retrieve a book by its ISBN.
    
    Raises an HTTPException if the book is not found.
    """
    return get_book_by_isbn(db, isbn)

@router.put("/{isbn}", response_model=BookResponse)
def update_existing_book(isbn: str, book: BookCreate, db: Session = Depends(get_db)):
    """
    Update an existing book.
    
    Validates that the ISBN in the path matches the ISBN in the body.
    Raises an HTTPException if the book is not found or ISBNs don't match.
    """
    if isbn != book.ISBN:
        raise HTTPException(status_code=400, detail="ISBN in path must match ISBN in body")
    
    return update_book(db=db, isbn=isbn, book_data=book)