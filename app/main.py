from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError  
from .utils.middleware import JWTMiddleware

from app.routes import book_routes, customer_routes

app = FastAPI(title="Bookstore API")

app.add_middleware(JWTMiddleware)

# CORS (Cross-Origin Resource Sharing) Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add this validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors (missing fields, invalid types, etc.)
    and return a 400 Bad Request status code.
    """
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
    )

# Include routers
app.include_router(book_routes.router)
app.include_router(customer_routes.router)

# Status endpoint
@app.get("/status", response_class=PlainTextResponse)
def status():
    """Health check endpoint that returns OK if the service is running."""
    return "OK"

# Exception handlers
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

