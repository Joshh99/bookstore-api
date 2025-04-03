import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import customer_routes
from shared_utils.jwt.middleware import jwt_validation_middleware

app = FastAPI(title="Customer Service")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add JWT middleware to validate requests
app.middleware("http")(jwt_validation_middleware)

# Include customer routes
app.include_router(customer_routes.router)

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTPExceptions and return a consistent JSON response
    with the appropriate status code and error message.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions and return a 500 Internal Server Error
    with a generic error message.
    """
    # You might want to log the exception here
    print(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

# Status endpoint for health checks
@app.get("/status")
def status():
    """
    Health check endpoint for the Customer service.
    """
    return {"status": "OK"}

if __name__ == "__main__":
    # Configure port from environment variable, default to 3000
    port = int(os.getenv("PORT", 3000))
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True
    )