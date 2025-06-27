"""
Centralized error handling for AI-Based Data Cleaner
"""
import traceback
import sys
from typing import Any, Dict, Optional, Callable
from functools import wraps
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DataCleanerError(Exception):
    """Base exception class for Data Cleaner application"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class FileProcessingError(DataCleanerError):
    """Exception for file processing errors"""
    
    def __init__(self, message: str, filename: str = None, file_type: str = None):
        super().__init__(message, "FILE_PROCESSING_ERROR", {
            'filename': filename,
            'file_type': file_type
        })

class AIServiceError(DataCleanerError):
    """Exception for AI service errors"""
    
    def __init__(self, message: str, service: str = "OpenAI", api_response: str = None):
        super().__init__(message, "AI_SERVICE_ERROR", {
            'service': service,
            'api_response': api_response
        })

class DataValidationError(DataCleanerError):
    """Exception for data validation errors"""
    
    def __init__(self, message: str, column: str = None, validation_type: str = None):
        super().__init__(message, "DATA_VALIDATION_ERROR", {
            'column': column,
            'validation_type': validation_type
        })

class ConfigurationError(DataCleanerError):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR", {
            'config_key': config_key
        })

class ErrorHandler:
    """Centralized error handling and reporting"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
    
    def handle_error(self, error: Exception, context: str = None, 
                    user_friendly: bool = True) -> Dict[str, Any]:
        """
        Handle and log errors with appropriate user feedback
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            user_friendly: Whether to return user-friendly error messages
            
        Returns:
            Dictionary containing error information for user display
        """
        
        # Log the full error details
        error_details = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        logger.error(f"Error in {context}: {error_details}")
        
        # Track error frequency
        error_key = f"{type(error).__name__}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Store in error history
        self.error_history.append(error_details)
        
        # Return user-friendly error information
        if user_friendly:
            return self._format_user_error(error, context)
        else:
            return error_details
    
    def _format_user_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Format error for user display"""
        
        user_error = {
            'title': 'An Error Occurred',
            'message': 'Something went wrong. Please try again.',
            'suggestions': [],
            'error_code': getattr(error, 'error_code', 'UNKNOWN_ERROR'),
            'technical_details': str(error)
        }
        
        # Customize based on error type
        if isinstance(error, FileProcessingError):
            user_error.update({
                'title': 'File Processing Error',
                'message': 'There was a problem processing your file.',
                'suggestions': [
                    'Check that your file is not corrupted',
                    'Ensure the file format is supported (CSV, Excel)',
                    'Try uploading a smaller file',
                    'Check that the file contains valid data'
                ]
            })
            
        elif isinstance(error, AIServiceError):
            user_error.update({
                'title': 'AI Service Error',
                'message': 'The AI cleaning service encountered an issue.',
                'suggestions': [
                    'Check your internet connection',
                    'Verify your OpenAI API key is valid',
                    'Try again in a few moments',
                    'Consider using non-AI cleaning options'
                ]
            })
            
        elif isinstance(error, DataValidationError):
            user_error.update({
                'title': 'Data Validation Error',
                'message': 'Your data contains issues that prevent processing.',
                'suggestions': [
                    'Check for missing or invalid column headers',
                    'Ensure data types are consistent within columns',
                    'Remove or fix severely corrupted data',
                    'Try cleaning the data manually first'
                ]
            })
            
        elif isinstance(error, ConfigurationError):
            user_error.update({
                'title': 'Configuration Error',
                'message': 'There is a configuration issue with the application.',
                'suggestions': [
                    'Check that all required environment variables are set',
                    'Verify your .env file is properly configured',
                    'Ensure your OpenAI API key is valid',
                    'Contact support if the issue persists'
                ]
            })
            
        elif isinstance(error, (MemoryError, OverflowError)):
            user_error.update({
                'title': 'Memory Error',
                'message': 'The file is too large to process.',
                'suggestions': [
                    'Try uploading a smaller file',
                    'Split your data into smaller chunks',
                    'Remove unnecessary columns before uploading',
                    'Consider using a more powerful system'
                ]
            })
            
        return user_error
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors encountered"""
        
        return {
            'total_errors': len(self.error_history),
            'error_counts': self.error_counts,
            'recent_errors': self.error_history[-5:] if self.error_history else [],
            'most_common_errors': sorted(
                self.error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }

# Global error handler instance
error_handler = ErrorHandler()

def handle_exceptions(context: str = None, user_friendly: bool = True):
    """
    Decorator for handling exceptions in functions
    
    Args:
        context: Description of the function context
        user_friendly: Whether to return user-friendly error messages
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_context = context or f"{func.__module__}.{func.__name__}"
                error_info = error_handler.handle_error(e, func_context, user_friendly)
                
                # Re-raise with additional context for debugging
                if not user_friendly:
                    raise
                
                # Return error info for user-friendly handling
                return {'error': True, 'error_info': error_info}
        
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, context: str = None, 
                default_return: Any = None, **kwargs) -> Any:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        context: Context description
        default_return: Value to return if function fails
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_return if error occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        func_context = context or f"{func.__module__}.{func.__name__}"
        error_handler.handle_error(e, func_context)
        return default_return

def validate_input(value: Any, expected_type: type, 
                  field_name: str = "input") -> Any:
    """
    Validate input value with proper error handling
    
    Args:
        value: Value to validate
        expected_type: Expected type
        field_name: Name of the field being validated
        
    Returns:
        Validated value
        
    Raises:
        DataValidationError: If validation fails
    """
    if value is None:
        raise DataValidationError(
            f"{field_name} cannot be None",
            validation_type="null_check"
        )
    
    if not isinstance(value, expected_type):
        raise DataValidationError(
            f"{field_name} must be of type {expected_type.__name__}, got {type(value).__name__}",
            validation_type="type_check"
        )
    
    return value
