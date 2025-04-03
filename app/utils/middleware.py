from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from .jwt import decode_jwt_payload, validate_jwt_payload

class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip JWT validation for status endpoint
        if request.url.path == "/status":
            return await call_next(request)
        
        # Check X-Client-Type header
        client_type = request.headers.get("X-Client-Type")
        if not client_type:
            return HTTPException(status_code=400, detail="Missing X-Client-Type header")()
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return HTTPException(status_code=401, detail="Missing or invalid Authorization header")()
        
        # Extract token
        token = auth_header.replace("Bearer ", "")
        
        # Decode and validate token
        payload = decode_jwt_payload(token)
        is_valid, message = validate_jwt_payload(payload)
        
        if not is_valid:
            return HTTPException(status_code=401, detail=message)()
        
        # Add the decoded payload to the request state for later use if needed
        request.state.jwt_payload = payload
        
        # Continue processing the request
        return await call_next(request)