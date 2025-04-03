import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import book_routes
from shared_utils.jwt.middleware import jwt_validation_middleware

app = FastAPI(title="Book Service")

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

# Include book routes
app.include_router(book_routes.router)

if __name__ == "__main__":
    # Configure port from environment variable, default to 3000
    port = int(os.getenv("PORT", 3000))
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True
    )