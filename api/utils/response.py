"""
API response utilities for consistent JSON responses
"""

from flask import jsonify
from datetime import datetime
from typing import Any, Dict, Optional

class APIResponse:
    """Standardized API response formatter"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200, metadata: Optional[Dict] = None) -> tuple:
        """
        Create a successful API response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            metadata: Additional metadata (pagination, etc.)
        
        Returns:
            Flask response tuple
        """
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        if metadata:
            response['metadata'] = metadata
            
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str = "An error occurred", status_code: int = 400, error_code: Optional[str] = None, details: Optional[Dict] = None) -> tuple:
        """
        Create an error API response
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Application-specific error code
            details: Additional error details
        
        Returns:
            Flask response tuple
        """
        response = {
            'success': False,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'error': {
                'code': error_code or f"HTTP_{status_code}",
                'message': message
            }
        }
        
        if details:
            response['error']['details'] = details
            
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(data: list, page: int, per_page: int, total: int, message: str = "Success") -> tuple:
        """
        Create a paginated API response
        
        Args:
            data: List of data items
            page: Current page number
            per_page: Items per page
            total: Total number of items
            message: Success message
        
        Returns:
            Flask response tuple
        """
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        metadata = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1 if has_next else None,
                'prev_page': page - 1 if has_prev else None
            }
        }
        
        return APIResponse.success(data, message, metadata=metadata)
    
    @staticmethod
    def validation_error(errors: Dict[str, list]) -> tuple:
        """
        Create a validation error response
        
        Args:
            errors: Dictionary of field validation errors
        
        Returns:
            Flask response tuple
        """
        response = {
            'success': False,
            'message': "Validation failed",
            'timestamp': datetime.utcnow().isoformat(),
            'validation_errors': errors,
            'error': {
                'code': "VALIDATION_ERROR",
                'message': "Validation failed",
                'details': {'validation_errors': errors}
            }
        }
        return jsonify(response), 400
    
    @staticmethod
    def not_found(resource: str = "Resource") -> tuple:
        """
        Create a not found error response
        
        Args:
            resource: Name of the resource that was not found
        
        Returns:
            Flask response tuple
        """
        return APIResponse.error(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> tuple:
        """
        Create an unauthorized error response
        
        Args:
            message: Authorization error message
        
        Returns:
            Flask response tuple
        """
        return APIResponse.error(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def forbidden(message: str = "Forbidden") -> tuple:
        """
        Create a forbidden error response
        
        Args:
            message: Forbidden error message
        
        Returns:
            Flask response tuple
        """
        return APIResponse.error(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )
    
    @staticmethod
    def conflict(message: str = "Resource conflict") -> tuple:
        """
        Create a conflict error response
        
        Args:
            message: Conflict error message
        
        Returns:
            Flask response tuple
        """
        return APIResponse.error(
            message=message,
            status_code=409,
            error_code="CONFLICT"
        )
    
    @staticmethod
    def server_error(message: str = "Internal server error") -> tuple:
        """
        Create a server error response
        
        Args:
            message: Server error message
        
        Returns:
            Flask response tuple
        """
        return APIResponse.error(
            message=message,
            status_code=500,
            error_code="INTERNAL_ERROR"
        )