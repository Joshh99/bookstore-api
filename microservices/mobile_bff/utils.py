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
        padding_length = 4 - (len(payload_base64) % 4)
        if padding_length < 4:
            payload_base64 += '=' * padding_length
        
        # Decode the base64
        payload_bytes = base64.urlsafe_b64decode(payload_base64)
        # Parse the JSON
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception as e:
        print(f"Error decoding JWT: {str(e)}")
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
    if "sub" not in payload:
        return False, "Missing subject claim in token"
    if payload["sub"] not in valid_subjects:
        return False, "Invalid subject in token"
    
    # Validate expiration (exp claim)
    if "exp" not in payload:
        return False, "Missing expiration claim in token"
    if not isinstance(payload["exp"], (int, float)):
        return False, "Invalid expiration format in token"
    
    current_time = time.time()
    if payload["exp"] <= current_time:
        return False, "Token has expired"
    
    # Validate issuer (iss claim)
    if "iss" not in payload:
        return False, "Missing issuer claim in token"
    if payload["iss"] != "cmu.edu":
        return False, "Invalid issuer in token"
    
    return True, "Valid token"

# Mobile BFF Transformation Functions
def transform_book_response(response_data: Union[Dict, List, str]) -> Union[Dict, List, str]:
    """
    Replace 'non-fiction' with '3' in book genre field for mobile clients.
    
    Args:
        response_data: Book data response (dictionary, list, or string)
        
    Returns:
        Modified response with genre transformation
    """
    # Handle dictionary response
    if isinstance(response_data, dict):
        if response_data.get('genre') == 'non-fiction':
            response_data['genre'] = '3'
        return response_data
    
    # Handle list response (list of books)
    elif isinstance(response_data, list):
        for item in response_data:
            if isinstance(item, dict) and item.get('genre') == 'non-fiction':
                item['genre'] = '3'
        return response_data
        
    # Handle string response (JSON string)
    elif isinstance(response_data, str):
        # This is a simple approach - for more complex scenarios, 
        # consider deserializing, modifying, and re-serializing
        return response_data.replace('"non-fiction"', '"3"').replace("'non-fiction'", "'3'")
        
    return response_data

def filter_customer_response(response_data: Union[Dict, List, str]) -> Union[Dict, List, str]:
    """
    Remove address-related fields from customer response for mobile clients.
    
    Args:
        response_data: Customer data response (dictionary, list, or string)
        
    Returns:
        Modified response with address fields removed
    """
    # Fields to remove
    fields_to_remove = ['address', 'address2', 'city', 'state', 'zipcode']
    
    # Handle dictionary response
    if isinstance(response_data, dict):
        # Remove the fields if they exist
        for field in fields_to_remove:
            if field in response_data:
                response_data.pop(field)
        return response_data
    
    # Handle list response (list of customers)
    elif isinstance(response_data, list):
        for item in response_data:
            if isinstance(item, dict):
                for field in fields_to_remove:
                    if field in item:
                        item.pop(field)
        return response_data
    
    # Handle string response (JSON string)
    elif isinstance(response_data, str):
        try:
            # Try to parse the string as JSON
            json_data = json.loads(response_data)
            
            # Process as dictionary or list
            if isinstance(json_data, dict):
                for field in fields_to_remove:
                    if field in json_data:
                        json_data.pop(field)
            elif isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, dict):
                        for field in fields_to_remove:
                            if field in item:
                                item.pop(field)
                                
            # Convert back to string
            return json.dumps(json_data)
        except json.JSONDecodeError:
            # If not valid JSON, return as is
            return response_data
    
    # If it's not a dictionary, list, or string, return as is
    return response_data