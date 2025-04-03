from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.models.book import BookCreate, BookResponse
from app.utils.db import get_db
from app.services import book_service

# Create an instance of APIRouter for book routes
router = APIRouter(tags=["books"])

@router.post("/books", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, response: Response, db: Session = Depends(get_db)):
    """
    Create a new book.
    """
    created_book = book_service.create_book(db=db, book=book)
    response.headers["Location"] = f"/books/{created_book.ISBN}"
    return created_book

@router.get("/books/isbn/{isbn}", response_model=BookResponse)
def get_book_by_isbn_path(isbn: str, db: Session = Depends(get_db)):
    """
    Get a book by its ISBN using the /books/isbn/{isbn} path.
    """
    return book_service.get_book_by_isbn(db, isbn)

@router.get("/books/{isbn}", response_model=BookResponse)
def get_book(isbn: str, db: Session = Depends(get_db)):
    """
    Get a book by its ISBN.
    """
    return book_service.get_book_by_isbn(db, isbn)

@router.put("/books/{isbn}", response_model=BookResponse)
def update_book(isbn: str, book: BookCreate, db: Session = Depends(get_db)):
    """
    Update a book.
    """
    # Add this check
    if isbn != book.ISBN:
        raise HTTPException(status_code=400, detail="ISBN in path must match ISBN in body")
    
    return book_service.update_book(db=db, isbn=isbn, book_data=book)