import os
import httpx
import uvicorn
import json
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, Union, Any
from dotenv import load_dotenv
from urllib.parse import urljoin
from urllib.parse import urlparse

from utils import decode_jwt_payload, validate_jwt_payload, transform_book_response, filter_customer_response

load_dotenv()
load_dotenv(".env")
# Get backend URL from environment variable
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "")

if BACKEND_BASE_URL.startswith('"') and BACKEND_BASE_URL.endswith('"'):
    BACKEND_BASE_URL = BACKEND_BASE_URL[1:-1]

# BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:3000")

print("Backend base url:", BACKEND_BASE_URL)
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
    
    # Validate client type for the appropriate BFF
    if request.app.title == "Web BFF Service" and client_type != "Web":
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid X-Client-Type. Must be 'Web'"}
        )
    elif request.app.title == "Mobile BFF Service" and client_type not in ["iOS", "Android"]:
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid X-Client-Type. Must be one of ['iOS', 'Android']"}
        )
    
    # Validate Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"message": "Missing Authorization header"}
        )
    
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid Authorization header format. Must be 'Bearer <token>'"}
        )
    
    # Extract and decode token
    token = auth_header.replace("Bearer ", "")
    payload = decode_jwt_payload(token)
    
    if not payload:
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid JWT token format"}
        )
    
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

@app.get("/status")
async def status():
    return {"status": "OK", "service": "mobile_bff"}

@app.get("/books/isbn/{isbn}")
async def get_book_by_isbn(isbn: str, request: Request):
    """
    Proxy to Book service with mobile-specific transformations.
    Replaces 'non-fiction' genre with '3'.
    """
    return await proxy_request(f"books/isbn/{isbn}", "GET", transform_type="book")

@app.get("/books/{isbn}")
async def get_book(isbn: str, request: Request):
    """
    Proxy to Book service with mobile-specific transformations.
    Replaces 'non-fiction' genre with '3'.
    """
    return await proxy_request(f"books/{isbn}", "GET", transform_type="book")

@app.post("/books")
async def create_book(request: Request):
    """
    Proxy POST request to Book service.
    """
    body = await request.json()
    return await proxy_request("books", "POST", body, transform_type="book")

@app.put("/books/{isbn}")
async def update_book(isbn: str, request: Request):
    """
    Proxy PUT request to Book service.
    """
    body = await request.json()
    return await proxy_request(f"books/{isbn}", "PUT", body, transform_type="book")

@app.get("/customers/{id}")
async def get_customer(id: str):
    """
    Proxy to Customer service with mobile-specific transformations.
    Removes address-related fields.
    """
    return await proxy_request(f"customers/{id}", "GET", transform_type="customer")

@app.get("/customers")
async def get_customer_by_userId(userId: Optional[str] = None):
    """
    Proxy to Customer service with mobile-specific transformations.
    Removes address-related fields.
    """
    if not userId:
        raise HTTPException(status_code=400, detail="Missing required query parameter 'userId'")
    
    return await proxy_request(f"customers?userId={userId}", "GET", transform_type="customer")

@app.post("/customers")
async def create_customer(request: Request):
    """
    Proxy POST request to Customer service.
    """
    body = await request.json()
    return await proxy_request("customers", "POST", body, transform_type="customer")

# General proxy function for all backend requests
async def proxy_request(path: str, method: str, body: Dict = None, transform_type: str = None):
    """
    Generic proxy for requests to backend services.
    
    Args:
        path: The path for the backend request
        method: HTTP method (GET, POST, PUT, DELETE)
        body: Request body for POST/PUT requests
        transform_type: Type of transformation to apply ("book" or "customer" or None)
    """
    # Ensure path doesn't start with a slash if urljoin is used
    if path.startswith('/'):
        path = path[1:]
    
    backend_url = urljoin(BACKEND_BASE_URL, path)
    print(f"Making {method} request to: {backend_url}")  # Debug the final URL
    
    # Call backend service
    async with httpx.AsyncClient() as client:
        try:
            headers = {"X-Client-Type": "Internal"}
            
            if method == "GET":
                response = await client.get(backend_url, headers=headers)
            elif method == "POST":
                response = await client.post(backend_url, json=body, headers=headers)
            elif method == "PUT":
                response = await client.put(backend_url, json=body, headers=headers)
            elif method == "DELETE":
                response = await client.delete(backend_url, headers=headers)
            else:
                return JSONResponse(
                    status_code=400,
                    content={"message": f"Unsupported method: {method}"}
                )
            
            # Handle non-2xx responses
            if response.status_code >= 400:
                error_content = {"message": "Error from backend service"}
                try:
                    error_content = response.json()
                except:
                    pass
                return JSONResponse(
                    status_code=response.status_code,
                    content=error_content
                )
            
            # Process response based on transformation type
            try:
                response_data = response.json()
                
                # Apply mobile-specific transformations
                if transform_type == "book":
                    return transform_book_response(response_data)
                elif transform_type == "customer":
                    print("Filtering customer data:", response_data)  # Debug
                    return filter_customer_response(response_data)
                else:
                    return response_data
            except ValueError:
                # If not JSON, return as is
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
        except httpx.RequestError as e:
            print(f"Error connecting to backend service: {str(e)}")
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