import os
import httpx
import uvicorn
import json
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, Union, Any

from utils import decode_jwt_payload, validate_jwt_payload, transform_book_response, filter_customer_response

# Get backend URL from environment variable
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000")

app = FastAPI(title="Mobile BFF Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Middleware
@app.middleware("http")
async def jwt_validation_middleware(request: Request, call_next):
    # Always allow status endpoint
    if request.url.path == "/status":
        return await call_next(request)
    
    # Validate X-Client-Type header
    client_type = request.headers.get("X-Client-Type")
    if not client_type:
        return JSONResponse(
            status_code=400,
            content={"message": "Missing X-Client-Type header"}
        )
    
    # Validate client type for mobile BFF
    valid_client_types = ["iOS", "Android"]
    if client_type not in valid_client_types:
        return JSONResponse(
            status_code=400,
            content={"message": f"Invalid X-Client-Type. Must be one of {valid_client_types}"}
        )
    
    # Validate Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"message": "Missing or invalid Authorization header"}
        )
    
    # Extract and decode token
    token = auth_header.replace("Bearer ", "")
    payload = decode_jwt_payload(token)
    
    # Validate token payload
    is_valid, message = validate_jwt_payload(payload)
    if not is_valid:
        return JSONResponse(
            status_code=401,
            content={"message": message}
        )
    
    # Add payload to request state for potential downstream use
    request.state.jwt_payload = payload
    
    # Continue processing the request
    response = await call_next(request)
    return response

# Status endpoint for health checks
@app.get("/status")
def status():
    """
    Health check endpoint for the Mobile BFF service.
    """
    return {"status": "OK"}

# Book Service Proxy Endpoints
@app.get("/books/isbn/{isbn}")
async def get_book_by_isbn(isbn: str, request: Request):
    """
    Proxy to Book service with mobile-specific transformations.
    Replaces 'non-fiction' genre with '3'.
    """
    return await proxy_book_request(isbn, request.url.path)

@app.get("/books/{isbn}")
async def get_book(isbn: str, request: Request):
    """
    Proxy to Book service with mobile-specific transformations.
    Replaces 'non-fiction' genre with '3'.
    """
    return await proxy_book_request(isbn, request.url.path)

@app.post("/books")
async def create_book(request: Request):
    """
    Proxy POST request to Book service.
    """
    return await proxy_generic_request("books", "POST", request)

@app.put("/books/{isbn}")
async def update_book(isbn: str, request: Request):
    """
    Proxy PUT request to Book service.
    """
    return await proxy_generic_request(f"books/{isbn}", "PUT", request)

# Customer Service Proxy Endpoints
@app.get("/customers/{id}")
async def get_customer(id: str):
    """
    Proxy to Customer service with mobile-specific transformations.
    Removes address-related fields.
    """
    return await proxy_customer_request(f"customers/{id}")

@app.get("/customers")
async def get_customer_by_userId(userId: Optional[str] = None):
    """
    Proxy to Customer service with mobile-specific transformations.
    Removes address-related fields.
    """
    if not userId:
        raise HTTPException(status_code=400, detail="Missing required query parameter 'userId'")
    
    return await proxy_customer_request(f"customers?userId={userId}")

@app.post("/customers")
async def create_customer(request: Request):
    """
    Proxy POST request to Customer service.
    """
    return await proxy_generic_request("customers", "POST", request)

# Helper functions for proxying requests
async def proxy_book_request(isbn: str, request_path: str):
    """
    Proxy book requests to the backend book service and transform the response.
    
    Args:
        isbn: The ISBN to look up
        request_path: The original path from the client request
    """
    # Determine backend URL
    backend_url = f"{BACKEND_BASE_URL}/books/{isbn}"
    if "isbn" in request_path:
        backend_url = f"{BACKEND_BASE_URL}/books/isbn/{isbn}"
    
    # Call backend service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                backend_url,
                headers={"X-Client-Type": "Internal"}
            )
            
            # Handle non-200 responses
            if response.status_code != 200:
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.content else {"message": "Error from backend service"}
                )
            
            # Get response data and transform for mobile
            response_data = response.json()
            transformed_data = transform_book_response(response_data)
            
            return transformed_data
            
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"message": f"Error connecting to backend service: {str(e)}"}
            )

async def proxy_customer_request(path: str):
    """
    Proxy customer requests to the backend customer service and transform the response.
    
    Args:
        path: The path for the backend request
    """
    backend_url = f"{BACKEND_BASE_URL}/{path}"
    
    # Call backend service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                backend_url,
                headers={"X-Client-Type": "Internal"}
            )
            
            # Handle non-200 responses
            if response.status_code != 200:
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.content else {"message": "Error from backend service"}
                )
            
            # Get response data and filter for mobile
            response_data = response.json()
            filtered_data = filter_customer_response(response_data)
            
            return filtered_data
            
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"message": f"Error connecting to backend service: {str(e)}"}
            )

async def proxy_generic_request(path: str, method: str, request: Request):
    """
    Generic proxy for POST, PUT, DELETE requests to backend services.
    
    Args:
        path: The path for the backend request
        method: HTTP method (POST, PUT, DELETE)
        request: Original FastAPI request
    """
    backend_url = f"{BACKEND_BASE_URL}/{path}"
    
    # Get request body
    body = await request.json()
    
    # Call backend service
    async with httpx.AsyncClient() as client:
        try:
            if method == "POST":
                response = await client.post(
                    backend_url,
                    json=body,
                    headers={"X-Client-Type": "Internal"}
                )
            elif method == "PUT":
                response = await client.put(
                    backend_url,
                    json=body,
                    headers={"X-Client-Type": "Internal"}
                )
            elif method == "DELETE":
                response = await client.delete(
                    backend_url,
                    headers={"X-Client-Type": "Internal"}
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"message": f"Unsupported method: {method}"}
                )
            
            # Handle responses
            if response.status_code not in [200, 201, 204]:
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.content else {"message": "Error from backend service"}
                )
            
            # Return response from backend (for POST and PUT)
            if method in ["POST", "PUT"]:
                response_data = response.json()
                
                # Apply transformations if necessary
                if path.startswith("books"):
                    transformed_data = transform_book_response(response_data)
                    return transformed_data
                elif path.startswith("customers"):
                    filtered_data = filter_customer_response(response_data)
                    return filtered_data
                
                return response_data
            
            # For DELETE, just return a success message
            return {"message": "Resource deleted successfully"}
            
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"message": f"Error connecting to backend service: {str(e)}"}
            )

if __name__ == "__main__":
    # Configure port from environment variable, default to 80
    port = int(os.getenv("PORT", 80))
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True
    )