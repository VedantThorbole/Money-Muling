"""
API package for REST endpoints.
Exposes all routes and middleware for the application.
"""

from .routes import api_bp
from .middleware import setup_middleware

__all__ = ['api_bp', 'setup_middleware']