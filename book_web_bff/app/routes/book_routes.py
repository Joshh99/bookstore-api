from fastapi import APIRouter, Depends, HTTPException, Request, Response
import httpx
import os
from typing import Any, Dict, Optional

# Create router for book-related endpoints
router = APIRouter(prefix="/books", tags=["books"])

# Get the backend book service URL from environment variable
BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000")

# Helper to create the full backend URL
def get_backend_url(path: str) -> str:
    # Make sure the base URL doesn't end with a slash and the path starts with one
    base_url = BOOK_SERVICE_URL.rstrip("/")
    path = "/" + path.lstrip("/")
    return f"{base_url}{path}"

@router.get("/status")
async def status():
    """Health check endpoint for the Web BFF Book routes."""
    return {"status": "OK"}

@router.get("/{isbn}")
async def get_book(isbn: str, request: Request):
    """
    Proxy GET request to the Book service to retrieve a book by ISBN.
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Forward the request to the backend service
        backend_url = f"{BOOK_SERVICE_URL}/books/{isbn}"
        
        try:
            # Forward any relevant headers (Authorization token will be handled by middleware)
            response = await client.get(
                backend_url,
                headers={"Authorization": request.headers.get("Authorization")}
            )
            
            # Return the response from the backend service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error communicating with Book service: {str(e)}")

@router.get("/isbn/{isbn}")
async def get_book_by_isbn(isbn: str, request: Request):
    """
    Proxy GET request to the Book service to retrieve a book by ISBN using the /isbn/ path.
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Forward the request to the backend service
        backend_url = f"{BOOK_SERVICE_URL}/books/isbn/{isbn}"
        
        try:
            # Forward any relevant headers
            response = await client.get(
                backend_url,
                headers={"Authorization": request.headers.get("Authorization")}
            )
            
            # Return the response from the backend service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error communicating with Book service: {str(e)}")

@router.post("/")
async def create_book(request: Request):
    """
    Proxy POST request to the Book service to create a new book.
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Get the request body
        body = await request.body()
        
        try:
            # Forward the request to the backend service with the same body and headers
            response = await client.post(
                f"{BOOK_SERVICE_URL}/books/",
                content=body,
                headers={
                    "Authorization": request.headers.get("Authorization"),
                    "Content-Type": request.headers.get("Content-Type", "application/json")
                }
            )
            
            # Return the response from the backend service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error communicating with Book service: {str(e)}")

@router.put("/{isbn}")
async def update_book(isbn: str, request: Request):
    """
    Proxy PUT request to the Book service to update an existing book.
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Get the request body
        body = await request.body()
        
        try:
            # Forward the request to the backend service with the same body and headers
            response = await client.put(
                f"{BOOK_SERVICE_URL}/books/{isbn}",
                content=body,
                headers={
                    "Authorization": request.headers.get("Authorization"),
                    "Content-Type": request.headers.get("Content-Type", "application/json")
                }
            )
            
            # Return the response from the backend service
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error communicating with Book service: {str(e)}")