"""
Middleware functions for request/response processing.
Includes authentication, logging, error handling, and rate limiting.
"""

from flask import request, jsonify, g
from functools import wraps
import time
import logging
from typing import Callable, Any
import hashlib
import hmac
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting storage
rate_limit_storage = {}

def setup_middleware(app):
    """
    Set up all middleware for the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Execute before each request."""
        g.start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
        
        # Check rate limit
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Calculate request duration
        duration = time.time() - g.start_time
        
        # Log response
        logger.info(f"Response: {response.status_code} - Duration: {duration:.3f}s")
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        """Handle file too large errors."""
        return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

def check_rate_limit(client_ip: str, limit: int = 100, window: int = 3600) -> bool:
    """
    Check if client has exceeded rate limit.
    
    Args:
        client_ip: Client IP address
        limit: Maximum requests per window
        window: Time window in seconds
        
    Returns:
        True if within limit, False if exceeded
    """
    current_time = time.time()
    
    # Clean old entries
    for ip in list(rate_limit_storage.keys()):
        if current_time - rate_limit_storage[ip]['timestamp'] > window:
            del rate_limit_storage[ip]
    
    # Check current IP
    if client_ip in rate_limit_storage:
        if current_time - rate_limit_storage[client_ip]['timestamp'] <= window:
            rate_limit_storage[client_ip]['count'] += 1
            if rate_limit_storage[client_ip]['count'] > limit:
                return False
        else:
            # Reset counter
            rate_limit_storage[client_ip] = {
                'timestamp': current_time,
                'count': 1
            }
    else:
        rate_limit_storage[client_ip] = {
            'timestamp': current_time,
            'count': 1
        }
    
    return True

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key (for future authentication).
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    # For now, accept any key in production would check against secure store
    expected_key = os.environ.get('API_KEY', 'rift-hackathon-2026')
    return hmac.compare_digest(api_key, expected_key)

def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require API key for endpoints.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def log_request_data(f: Callable) -> Callable:
    """
    Decorator to log request data for debugging.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Log request details
        logger.debug(f"Headers: {dict(request.headers)}")
        
        if request.is_json:
            logger.debug(f"JSON Body: {request.json}")
        
        if request.files:
            logger.debug(f"Files: {list(request.files.keys())}")
        
        return f(*args, **kwargs)
    
    return decorated

def validate_content_type(allowed_types: list) -> Callable:
    """
    Decorator to validate content type.
    
    Args:
        allowed_types: List of allowed content types
        
    Returns:
        Decorator function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            content_type = request.headers.get('Content-Type', '')
            
            if not any(allowed in content_type for allowed in allowed_types):
                return jsonify({
                    'error': f'Content-Type must be one of: {", ".join(allowed_types)}'
                }), 415
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def cache_response(timeout: int = 300) -> Callable:
    """
    Decorator to cache response.
    
    Args:
        timeout: Cache timeout in seconds
        
    Returns:
        Decorator function
    """
    cache = {}
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # Create cache key from request
            cache_key = hashlib.md5(
                f"{request.path}{request.query_string}".encode()
            ).hexdigest()
            
            # Check cache
            if cache_key in cache:
                cached_response, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    return cached_response
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Cache response
            cache[cache_key] = (response, time.time())
            
            return response
        
        return decorated
    
    return decorator