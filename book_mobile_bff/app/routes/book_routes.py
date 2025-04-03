from fastapi import APIRouter, HTTPException, Request, Response
import httpx
import os
import json
from typing import Any, Dict, Optional

from app.utils.response_transformers import transform_book_response

# Create router for book-related endpoints
router = APIRouter(prefix="/books", tags=["books"])

# Get the backend book service URL from environment variable
BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000")

@router.get("/status")
async def status():
    """Health check endpoint for the Mobile BFF Book routes."""
    return {"status": "OK"}

@router.get("/{isbn}")
async def get_book(isbn: str, request: Request):
    """
    Proxy GET request to the Book service to retrieve a book by ISBN.
    
    Transforms response for mobile clients by replacing 'non-fiction' with '3'.
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
            
            # Check if the response is successful
            if response.status_code == 200:
                # Get the response data
                response_data = response.json()
                
                # Apply the transformation for mobile clients
                transformed_data = transform_book_response(response_data)
                
                # Return the transformed response
                return transformed_data
            else:
                # For error responses, just pass through without transformation
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
    
    Transforms response for mobile clients by replacing 'non-fiction' with '3'.
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
            
            # Check if the response is successful
            if response.status_code == 200:
                # Get the response data
                response_data = response.json()
                
                # Apply the transformation for mobile clients
                transformed_data = transform_book_response(response_data)
                
                # Return the transformed response
                return transformed_data
            else:
                # For error responses, just pass through without transformation
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
    
    No transformation needed for POST requests.
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
    
    No transformation needed for PUT requests.
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