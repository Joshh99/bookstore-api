from fastapi import APIRouter, Depends, HTTPException, Request, Response
import httpx
import os
from typing import Any, Dict, Optional

# Create router for customer-related endpoints
router = APIRouter(prefix="/customers", tags=["customers"])

# Get the backend customer service URL from environment variable
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000")

# Helper to create the full backend URL
def get_backend_url(path: str) -> str:
    # Make sure the base URL doesn't end with a slash and the path starts with one
    base_url = CUSTOMER_SERVICE_URL.rstrip("/")
    path = "/" + path.lstrip("/")
    return f"{base_url}{path}"

@router.get("/status")
async def status():
    """Health check endpoint for the Web BFF Customer routes."""
    return {"status": "OK"}

@router.get("/{id}")
async def get_customer(id: str, request: Request):
    """
    Proxy GET request to the Customer service to retrieve a customer by ID.
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Forward the request to the backend service
        backend_url = f"{CUSTOMER_SERVICE_URL}/customers/{id}"
        
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
            raise HTTPException(status_code=503, detail=f"Error communicating with Customer service: {str(e)}")

@router.get("/")
async def get_customer_by_user_id(request: Request):
    """
    Proxy GET request to the Customer service to retrieve a customer by user ID (query parameter).
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Forward the request to the backend service with query parameters
        try:
            # Get the original URL's query parameters and pass them along
            response = await client.get(
                f"{CUSTOMER_SERVICE_URL}/customers/",
                params=dict(request.query_params),
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
            raise HTTPException(status_code=503, detail=f"Error communicating with Customer service: {str(e)}")

@router.post("/")
async def create_customer(request: Request):
    """
    Proxy POST request to the Customer service to create a new customer.
    
    This endpoint passes through the response without transformation.
    """
    async with httpx.AsyncClient() as client:
        # Get the request body
        body = await request.body()
        
        try:
            # Forward the request to the backend service with the same body and headers
            response = await client.post(
                f"{CUSTOMER_SERVICE_URL}/customers/",
                content=body,
                headers={
                    "Authorization": request.headers.get("Authorization"),
                    "Content-Type": request.headers.get("Content-Type", "application/json")
                }
            )
            
            # Return the response from the backend service including any headers like Location
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Error communicating with Customer service: {str(e)}")