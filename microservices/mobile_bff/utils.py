import base64
import json
import time
from typing import Dict, Union, Tuple, Any, List

# JWT Validation Functions
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

# Mobile BFF Transformation Functions
def transform_book_response(response_data: Union[Dict, str]) -> Union[Dict, str]:
    """
    Replace 'non-fiction' with '3' in book genre field for mobile clients.
    
    Args:
        response_data: Book data response (dictionary or string)
        
    Returns:
        Modified response with genre transformation
    """
    # Handle dictionary response
    if isinstance(response_data, dict):
        if response_data.get('genre') == 'non-fiction':
            response_data['genre'] = '3'
        return response_data
        
    # Handle string response (JSON string)
    elif isinstance(response_data, str):
        return response_data.replace('"non-fiction"', '"3"').replace("'non-fiction'", "'3'")
        
    return response_data

def filter_customer_response(response_data: Union[Dict, str]) -> Union[Dict, str]:
    """
    Remove address-related fields from customer response for mobile clients.
    
    Args:
        response_data: Customer data response (dictionary or string)
        
    Returns:
        Modified response with address fields removed
    """
    if isinstance(response_data, dict):
        # Fields to remove
        fields_to_remove = ['address', 'address2', 'city', 'state', 'zipcode']
        
        # Remove the fields if they exist
        for field in fields_to_remove:
            if field in response_data:
                response_data.pop(field)
        
        return response_data
        
    # If it's not a dictionary, return as is
    # In a real implementation, we might want to parse and process JSON strings too
    return response_data