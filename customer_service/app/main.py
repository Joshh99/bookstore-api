import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import customer_routes
from shared_utils.db import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Customer Service",
    description="Microservice for managing customer data",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include customer routes
app.include_router(customer_routes.router)

@app.get("/status")
def status_check():
    return {"status": "Customer service is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )