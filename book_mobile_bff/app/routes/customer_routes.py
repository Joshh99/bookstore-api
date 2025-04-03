from fastapi import APIRouter, HTTPException, Request, Response
import httpx
import os
import json
from typing import Any, Dict, Optional

from app.utils.response_transformers import filter_customer_response

# Create router for customer-related endpoints
router = APIRouter(prefix="/customers", tags=["customers"])

# Get the backend customer service URL from environment variable
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000")

@router.get("/status")
async def status():
    """Health check endpoint for the Mobile BFF Customer routes."""
    return {"status": "OK"}

@router.get("/{id}")
async def get_customer(id: str, request: Request):
    """
    Proxy GET request to the Customer service to retrieve a customer by ID.
    
    Filters out address-related fields for mobile clients.
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
            
            # Check if the response is successful
            if response.status_code == 200:
                # Get the response data
                response_data = response.json()
                
                # Apply the filtering for mobile clients
                filtered_data = filter_customer_response(response_data)
                
                # Return the filtered response
                return filtered_data
            else:
                # For error responses, just pass through without transformation
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
    
    Filters out address-related fields for mobile clients.
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
            
            # Check if the response is successful
            if response.status_code == 200:
                # Get the response data
                response_data = response.json()
                
                # Apply the filtering for mobile clients
                filtered_data = filter_customer_response(response_data)
                
                # Return the filtered response
                return filtered_data
            else:
                # For error responses, just pass through without transformation
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
    
    No transformation needed for POST requests.
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