import base64
import json
import time
from typing import Dict, Tuple

def decode_jwt_payload(token: str) -> Dict:
    """
    Decode the payload part of a JWT token.
    
    Args:
        token (str): JWT token string
    
    Returns:
        Dict: Decoded payload or None if decoding fails
    """
    try:
        # Split token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Get the payload (middle part)
        payload_base64 = parts[1]
        # Add padding if needed
        payload_base64 += '=' * ((4 - len(payload_base64) % 4) % 4)
        
        # Decode the base64
        payload_bytes = base64.urlsafe_b64decode(payload_base64)
        # Parse the JSON
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        return None

def validate_jwt_payload(payload: Dict) -> Tuple[bool, str]:
    """
    Validate the JWT payload according to A2 specifications.
    
    Args:
        payload (Dict): Decoded JWT payload
    
    Returns:
        Tuple[bool, str]: Validation result and message
    """
    # Check payload exists and is a dictionary
    if not payload or not isinstance(payload, dict):
        return False, "Invalid token format"
    
    # Validate subject (sub claim)
    valid_subjects = ["starlord", "gamora", "drax", "rocket", "groot"]
    if "sub" not in payload or payload["sub"] not in valid_subjects:
        return False, "Invalid subject in token"
    
    # Validate expiration (exp claim)
    if "exp" not in payload or not isinstance(payload["exp"], (int, float)):
        return False, "Missing or invalid expiration in token"
    
    current_time = time.time()
    if payload["exp"] <= current_time:
        return False, "Token has expired"
    
    # Validate issuer (iss claim)
    if "iss" not in payload or payload["iss"] != "cmu.edu":
        return False, "Invalid issuer in token"
    
    return True, "Valid token"