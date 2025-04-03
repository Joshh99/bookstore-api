# app/utils/response_transformers.py
from typing import Dict, Any, List, Union

def transform_book_response(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Transform book response for mobile clients by replacing 'non-fiction' with '3' in the genre field.
    
    Args:
        data: Book data from the backend service, can be a single book or a list of books
        
    Returns:
        Transformed book data
    """
    if isinstance(data, list):
        # Transform each book in the list
        return [transform_single_book(book) for book in data]
    elif isinstance(data, dict):
        # Transform a single book
        return transform_single_book(data)
    return data

def transform_single_book(book: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a single book record by replacing 'non-fiction' with '3'.
    
    Args:
        book: Single book dictionary
        
    Returns:
        Transformed book dictionary
    """
    if book.get('genre') == 'non-fiction':
        book['genre'] = '3'
    return book

def filter_customer_response(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Filter customer response for mobile clients by removing address-related fields.
    
    Args:
        data: Customer data from the backend service, can be a single customer or a list of customers
        
    Returns:
        Filtered customer data
    """
    if isinstance(data, list):
        # Filter each customer in the list
        return [filter_single_customer(customer) for customer in data]
    elif isinstance(data, dict):
        # Filter a single customer
        return filter_single_customer(data)
    return data

def filter_single_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter a single customer record by removing address-related fields.
    
    Args:
        customer: Single customer dictionary
        
    Returns:
        Filtered customer dictionary
    """
    # Fields to remove for mobile clients
    fields_to_remove = ['address', 'address2', 'city', 'state', 'zipcode']
    
    # Create a new dictionary without the fields to remove
    return {key: value for key, value in customer.items() if key not in fields_to_remove}