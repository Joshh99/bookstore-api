from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from .jwt import decode_jwt_payload, validate_jwt_payload

class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Always allow status endpoint
        if request.url.path == "/status":
            return await call_next(request)
        
        # Validate X-Client-Type header
        client_type = request.headers.get("X-Client-Type")
        if not client_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Missing X-Client-Type header"
            )
        
        # Validate client type
        valid_client_types = ["Web", "iOS", "Android"]
        if client_type not in valid_client_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid X-Client-Type. Must be one of {valid_client_types}"
            )
        
        # Validate Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Missing or invalid Authorization header"
            )
        
        # Extract and decode token
        token = auth_header.replace("Bearer ", "")
        payload = decode_jwt_payload(token)
        
        # Validate token payload
        is_valid, message = validate_jwt_payload(payload)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail=message
            )
        
        # Add payload to request state for potential downstream use
        request.state.jwt_payload = payload
        
        # Continue processing the request
        response = await call_next(request)
        return response

def jwt_validation_middleware(request: Request, call_next):
    """
    Wrapper function to use with FastAPI's middleware decorator 
    if not using class-based middleware.
    """
    middleware = JWTMiddleware(call_next)
    return middleware.dispatch(request, call_next)