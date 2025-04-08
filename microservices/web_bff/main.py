import os
import httpx
import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, Union, Any
from dotenv import load_dotenv
from urllib.parse import urljoin
from urllib.parse import urlparse


from utils import decode_jwt_payload, validate_jwt_payload

# Load env vars from multiple possible locations
load_dotenv()  # First try the current directory
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "")

if BACKEND_BASE_URL.startswith('"') and BACKEND_BASE_URL.endswith('"'):
    BACKEND_BASE_URL = BACKEND_BASE_URL[1:-1]

app = FastAPI(title="Web BFF Service")

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
    
    # Validate client type for web BFF
    if client_type != "Web":
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid X-Client-Type. Must be 'Web'"}
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
    Health check endpoint for the Web BFF service.
    """
    return {"status": "OK"}

# Book Service Proxy Endpoints
@app.get("/books/isbn/{isbn}")
async def get_book_by_isbn(isbn: str, request: Request):
    """
    Proxy to Book service with no transformations for web clients.
    """
    return await proxy_request(f"books/isbn/{isbn}", "GET")

@app.get("/books/{isbn}")
async def get_book(isbn: str, request: Request):
    """
    Proxy to Book service with no transformations for web clients.
    """
    return await proxy_request(f"books/{isbn}", "GET")

@app.post("/books")
async def create_book(request: Request):
    """
    Proxy POST request to Book service.
    """
    body = await request.json()
    return await proxy_request("books", "POST", body)

@app.put("/books/{isbn}")
async def update_book(isbn: str, request: Request):
    """
    Proxy PUT request to Book service.
    """
    body = await request.json()
    return await proxy_request(f"books/{isbn}", "PUT", body)

# Customer Service Proxy Endpoints
@app.get("/customers/{id}")
async def get_customer(id: str):
    """
    Proxy to Customer service with no transformations for web clients.
    """
    return await proxy_request(f"customers/{id}", "GET")

@app.get("/customers")
async def get_customer_by_userId(userId: Optional[str] = None):
    """
    Proxy to Customer service with no transformations for web clients.
    """
    if not userId:
        raise HTTPException(status_code=400, detail="Missing required query parameter 'userId'")
    
    return await proxy_request(f"customers?userId={userId}", "GET")

@app.post("/customers")
async def create_customer(request: Request):
    """
    Proxy POST request to Customer service.
    """
    body = await request.json()
    return await proxy_request("customers", "POST", body)

# General proxy function for all backend requests
async def proxy_request(path: str, method: str, body: Dict = None):
    """
    Generic proxy for requests to backend services.
    
    Args:
        path: The path for the backend request
        method: HTTP method (GET, POST, PUT, DELETE)
        body: Request body for POST/PUT requests
    """
    from urllib.parse import urljoin
    
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
            
            # For web BFF, simply return the response as-is without any transformations
            if response.headers.get("content-type") == "application/json":
                return response.json()
            else:
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